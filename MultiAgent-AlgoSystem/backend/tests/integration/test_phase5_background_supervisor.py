"""Integration and verification tests for Phase 5 Background Supervisor & Autonomous Runtime."""
import asyncio
from datetime import datetime, timezone
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from backend.app.ai_agent.background_supervisor import AIBackgroundSupervisor
from backend.app.ai_agent.runtime import agent_runtime
from backend.app.ai_agent.schemas import AgentRuntimeState
from backend.app.agents.risk.risk_engine import risk_engine
from backend.app.agents.runtime.event_bus import event_bus
from backend.app.core.config import settings
from trading.execution.mt5_client import mt5_client


@pytest.mark.asyncio
async def test_phase5_1_supervisor_lifecycle_and_heartbeat():
    """Verify supervisor starts, records heartbeat, exposes telemetry, and shuts down gracefully."""
    sup = AIBackgroundSupervisor(check_interval_seconds=0.1)
    assert not sup.is_running
    assert sup.last_heartbeat is None

    await sup.start()
    assert sup.is_running
    assert sup.last_heartbeat is not None

    status = sup.get_status()
    assert status["running"] is True
    assert status["last_heartbeat"] is not None
    assert status["ai_runtime_state"] in [s.value for s in AgentRuntimeState]
    assert "db_healthy" in status
    assert "current_drawdown_pct" in status

    # Graceful shutdown
    await sup.stop()
    assert not sup.is_running
    status_stopped = sup.get_status()
    assert status_stopped["running"] is False


@pytest.mark.asyncio
async def test_phase5_2_new_and_closed_trade_detection():
    """Verify supervisor detects new open positions and closed trades from MT5 broker telemetry."""
    sup = AIBackgroundSupervisor(check_interval_seconds=0.05)
    captured_events = []

    async def listener(evt):
        captured_events.append(evt.event_type)

    event_bus.subscribe("TRADE_DETECTED", listener)
    event_bus.subscribe("TRADE_CLOSED", listener)

    try:
        # Initial state: 0 positions
        with patch.object(mt5_client, "get_open_positions", return_value=[]):
            await sup._monitor_positions_and_trades()
            assert len(sup._known_positions) == 0

        # Step 1: New position appears
        mock_pos = [{"ticket": 999001, "symbol": "EURUSD", "side": "BUY", "volume": 0.1, "profit": 5.0}]
        with patch.object(mt5_client, "get_open_positions", return_value=mock_pos):
            await sup._monitor_positions_and_trades()
            assert 999001 in sup._known_positions
            assert "TRADE_DETECTED" in captured_events

        # Step 2: Position disappears (trade closed)
        with patch.object(mt5_client, "get_open_positions", return_value=[]), \
             patch("backend.app.ai_agent.background_supervisor.mt5_reconciler.reconcile_trades", new_callable=AsyncMock) as mock_rec:
            mock_rec.return_value = {"imported_records": 1}
            await sup._monitor_positions_and_trades()
            assert 999001 not in sup._known_positions
            assert "TRADE_CLOSED" in captured_events
            assert mock_rec.called
            assert sup._trades_reconciled_count == 1
    finally:
        event_bus.unsubscribe("TRADE_DETECTED", listener)
        event_bus.unsubscribe("TRADE_CLOSED", listener)


@pytest.mark.asyncio
async def test_phase5_3_drawdown_increase_and_risk_violation_kill_switch():
    """Verify supervisor detects drawdown increase and trips kill switch on limit breach (>= 10%)."""
    sup = AIBackgroundSupervisor(check_interval_seconds=0.05)
    captured_events = []

    async def listener(evt):
        captured_events.append(evt.event_type)

    event_bus.subscribe("DRAWDOWN_INCREASED", listener)
    event_bus.subscribe("RISK_VIOLATION", listener)

    # Ensure kill switch starts disengaged
    risk_engine.disengage_kill_switch("OPERATOR")
    assert not risk_engine.kill_switch_active

    try:
        # Peak equity set to 100,000
        sup._peak_equity = 100000.0

        # Current equity drops to 89,000 (11% drawdown -> exceeds 10% limit)
        with patch.object(mt5_client, "get_account_info", return_value={"equity": 89000.0, "balance": 100000.0}):
            await sup._check_drawdown_and_risk_limits()

            assert sup._current_drawdown_pct == 11.0
            assert risk_engine.kill_switch_active is True
            assert "RISK_VIOLATION" in captured_events
    finally:
        event_bus.unsubscribe("DRAWDOWN_INCREASED", listener)
        event_bus.unsubscribe("RISK_VIOLATION", listener)
        risk_engine.disengage_kill_switch("OPERATOR")


@pytest.mark.asyncio
async def test_phase5_4_mt5_disconnect_detection_and_fail_closed():
    """Verify supervisor detects MT5 disconnect and trips kill switch."""
    sup = AIBackgroundSupervisor(check_interval_seconds=0.05)
    captured_events = []

    async def listener(evt):
        captured_events.append(evt.event_type)

    event_bus.subscribe("MT5_DISCONNECTED", listener)
    risk_engine.disengage_kill_switch("OPERATOR")

    try:
        with patch.object(mt5_client, "connected", False), \
             patch.object(mt5_client, "is_simulation_mode", False), \
             patch.object(settings, "AUTO_KILL_ON_MT5_DISCONNECT", True):
            await sup._check_mt5_connectivity()
            assert "MT5_DISCONNECTED" in captured_events
            assert risk_engine.kill_switch_active is True
    finally:
        event_bus.unsubscribe("MT5_DISCONNECTED", listener)
        risk_engine.disengage_kill_switch("OPERATOR")


@pytest.mark.asyncio
async def test_phase5_5_supabase_database_failure_detection():
    """Verify supervisor detects database failure and emits DATABASE_FAILURE."""
    sup = AIBackgroundSupervisor(check_interval_seconds=0.05)
    captured_events = []

    async def listener(evt):
        captured_events.append(evt.event_type)

    event_bus.subscribe("DATABASE_FAILURE", listener)

    try:
        with patch("backend.app.ai_agent.background_supervisor.async_session_maker", side_effect=Exception("Database connection timeout")):
            await sup._check_database_health()
            assert not sup._db_healthy
            assert "DATABASE_FAILURE" in captured_events
            assert sup._errors_recovered_count >= 1
    finally:
        event_bus.unsubscribe("DATABASE_FAILURE", listener)


@pytest.mark.asyncio
async def test_phase5_6_ai_failure_detection_and_recovery():
    """Verify supervisor detects AI runtime ERROR state and safely recovers it back to IDLE."""
    sup = AIBackgroundSupervisor(check_interval_seconds=0.05)
    captured_events = []

    async def listener(evt):
        captured_events.append(evt.event_type)

    event_bus.subscribe("AI_FAILURE", listener)

    try:
        # Force AI runtime into ERROR state
        agent_runtime.update_state(AgentRuntimeState.ERROR, last_error="Simulated OpenAI LLM context overflow")
        assert agent_runtime.current_state == AgentRuntimeState.ERROR

        await sup._check_ai_runtime_health()

        assert "AI_FAILURE" in captured_events
        # Verified recovered back to IDLE
        assert agent_runtime.current_state == AgentRuntimeState.IDLE
    finally:
        event_bus.unsubscribe("AI_FAILURE", listener)


@pytest.mark.asyncio
async def test_phase5_7_real_states_enum_conformance():
    """Verify all real states conform to the specification."""
    required_states = {
        "IDLE", "THINKING", "TOOL_CALL", "RESEARCHING",
        "BACKTESTING", "RISK_CHECK", "EXECUTING", "ERROR", "STOPPED"
    }
    actual_states = {s.value for s in AgentRuntimeState}
    assert required_states.issubset(actual_states)
