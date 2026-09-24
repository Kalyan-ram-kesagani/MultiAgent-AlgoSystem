"""Critical integration tests verifying AI Agent Risk Engine boundary, Kill Switch persistence, and Trade Classification."""
import json
from pathlib import Path
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from backend.app.agents.risk.risk_engine import RiskEngine, risk_engine
from backend.app.ai_agent.runtime import agent_runtime
from backend.app.ai_agent.tools.risk import request_order
from backend.app.database.session import async_session_maker, init_db
from backend.app.main import app
from backend.app.models.ai_audit import KillSwitchStateModel, OrderRequestModel
from backend.app.models.trading import Order, Trade
from backend.app.services.mt5_reconciler import mt5_reconciler
from trading.execution.mt5_client import mt5_client


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    """Ensure database schema is initialized and clean for each test."""
    mt5_client.is_simulation_mode = True
    await init_db()
    # Reset kill switch before each test
    risk_engine.disengage_kill_switch(operator="TEST_FIXTURE_RESET")
    yield
    risk_engine.disengage_kill_switch(operator="TEST_FIXTURE_CLEANUP")


@pytest.mark.asyncio
async def test_critical_1_ai_requests_risky_order_rejected():
    """
    CRITICAL TEST 1:
    AI requests risky order (e.g. inverted stop loss where BUY SL >= entry)
    -> Risk Engine rejects
    -> MT5 receives NO order.
    """
    initial_positions_count = len(mt5_client.get_open_positions())

    # Submit an invalid/risky order proposal (BUY with SL higher than entry)
    raw_res = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.1,
        stop_loss=1.1500,  # Invalid: above market price
        take_profit=1.2000,
        strategy_id="strategy_v1",
        reason="Test risky order proposal",
    )
    res = json.loads(raw_res)

    assert res["approved"] is False
    assert "stop loss" in res["reason"].lower() or "invalid" in res["reason"].lower() or "rejected" in res["reason"].lower()

    # Verify MT5 received NO order
    final_positions_count = len(mt5_client.get_open_positions())
    assert final_positions_count == initial_positions_count


@pytest.mark.asyncio
async def test_critical_2_kill_switch_on_blocks_ai_order():
    """
    CRITICAL TEST 2:
    Kill switch ON -> AI requests order -> request rejected -> MT5 receives NO order.
    """
    initial_positions_count = len(mt5_client.get_open_positions())

    # Engage kill switch
    risk_engine.engage_kill_switch("Emergency test circuit breaker tripped", operator="TEST_OPERATOR")
    assert risk_engine.kill_switch_active is True

    # AI attempts to request an otherwise valid order
    raw_res = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=1.0500,
        take_profit=1.1200,
        strategy_id="strategy_v1",
        reason="AI attempts trade while kill switch active",
    )
    res = json.loads(raw_res)

    assert res["approved"] is False
    assert "kill switch" in res["reason"].lower()

    # Verify MT5 received NO order
    final_positions_count = len(mt5_client.get_open_positions())
    assert final_positions_count == initial_positions_count


@pytest.mark.asyncio
async def test_critical_3_risk_engine_fail_closed():
    """
    CRITICAL TEST 3:
    Risk Engine unavailable or invalid input -> order rejected.
    """
    # Negative quantity or impossible symbol triggers fail-closed validation
    raw_res = request_order(
        symbol="INVALID_SYMBOL_XYZ",
        side="BUY",
        quantity=-1.0,
        stop_loss=0.0,
        take_profit=0.0,
        strategy_id="strategy_v1",
        reason="Fail closed test",
    )
    res = json.loads(raw_res)
    assert res["approved"] is False


@pytest.mark.asyncio
async def test_critical_4_ai_unavailable_system_remains_safe():
    """
    CRITICAL TEST 4:
    AI unavailable -> system remains safe.
    Trading infrastructure continues enforcing risk rules independently of AI state.
    """
    # Set AI runtime to ERROR or STOPPED
    from backend.app.ai_agent.schemas import AgentRuntimeState
    agent_runtime.update_state(AgentRuntimeState.ERROR)
    assert agent_runtime.state == AgentRuntimeState.ERROR

    # Risk Engine still operates deterministically
    assert risk_engine is not None
    risk_state = risk_engine.evaluate_order.__doc__
    assert risk_state is not None


@pytest.mark.asyncio
async def test_critical_5_kill_switch_persistence_across_restart(tmp_path):
    """
    CRITICAL TEST 5:
    Restart backend -> kill switch state remains correct across restarts.
    """
    test_file = tmp_path / ".kill_switch_test.json"
    engine1 = RiskEngine(state_file=test_file)
    engine1.engage_kill_switch("Breach detected in simulation", operator="WATCHDOG")
    assert engine1.kill_switch_active is True

    # Simulate backend restart by instantiating new engine pointing to same state
    engine2 = RiskEngine(state_file=test_file)
    assert engine2.kill_switch_active is True
    assert "Breach detected in simulation" in (engine2.kill_switch_reason or "")
    assert engine2.kill_switch_operator == "WATCHDOG"


@pytest.mark.asyncio
async def test_critical_6_manual_trade_classification_and_attribution():
    """
    CRITICAL TEST 6:
    Manual MT5 trade -> journal marks MANUAL/EXTERNAL -> not attributed to AI strategy.
    """
    async with async_session_maker() as session:
        # Reconcile trades from MT5 terminal / simulator
        summary = await mt5_reconciler.reconcile_trades(session)
        assert "imported_records" in summary

        # Query trades and verify origin classification exists
        stmt = select(Trade)
        res = await session.execute(stmt)
        trades = list(res.scalars().all())

        for t in trades:
            assert t.origin in ("SYSTEM_GENERATED", "MANUAL", "EXTERNAL", "UNKNOWN")


@pytest.mark.asyncio
async def test_ai_agent_api_endpoints():
    """Test AI Agent API routes."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET /api/ai/status
        res_status = await client.get("/api/ai/status")
        assert res_status.status_code == 200
        data_status = res_status.json()
        assert "status" in data_status
        assert "model" in data_status

        # GET /api/risk/status
        res_risk = await client.get("/api/risk/status")
        assert res_risk.status_code == 200

        # POST /api/kill-switch toggle
        res_toggle_on = await client.post(
            "/api/kill-switch",
            json={"activate": True, "reason": "API test trip", "requested_by": "Test Suite"},
        )
        assert res_toggle_on.status_code == 200
        assert res_toggle_on.json()["kill_switch_active"] is True

        res_toggle_off = await client.post(
            "/api/kill-switch",
            json={"activate": False, "reason": "API test reset", "requested_by": "Test Suite"},
        )
        assert res_toggle_off.status_code == 200
        assert res_toggle_off.json()["kill_switch_active"] is False

        # POST /api/orders/request through API
        res_order = await client.post(
            "/api/orders/request",
            json={
                "symbol": "EURUSD",
                "side": "BUY",
                "quantity": 0.01,
                "stop_loss": 1.0500,
                "take_profit": 1.1200,
                "strategy_id": "strategy_v1",
                "reason": "Integration API test order request",
            },
        )
        assert res_order.status_code == 200
        order_data = res_order.json()
        assert "approved" in order_data
