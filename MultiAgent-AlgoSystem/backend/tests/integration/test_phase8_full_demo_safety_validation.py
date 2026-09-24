import json
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.agents.risk.risk_engine import RiskEngine, risk_engine
from backend.app.ai_agent.runtime import agent_runtime, AgentRuntimeState
from backend.app.ai_agent.background_supervisor import ai_supervisor
from backend.app.ai_agent.tools.risk import request_order, clear_idempotency_cache
from backend.app.ai_agent.tools.strategy import create_strategy_candidate
from backend.app.models.ai_audit import OrderRequestModel
from backend.app.models.trading import Trade
from backend.app.database.session import async_session_maker
from trading.execution.mt5_client import mt5_client


@pytest.fixture(autouse=True)
def setup_safety_state():
    """Ensure clean idempotency cache and disengaged kill switch before each test."""
    clear_idempotency_cache()
    risk_engine.disengage_kill_switch(operator="PHASE8_TEST_SETUP")
    yield
    clear_idempotency_cache()
    risk_engine.disengage_kill_switch(operator="PHASE8_TEST_TEARDOWN")


@pytest.mark.asyncio
async def test_phase8_1_full_demo_pipeline_risk_approved():
    """Verify end-to-end pipeline: AI -> Request Order -> Risk Approved -> MT5 DEMO Execution -> Reconciled."""
    req_json = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=1.0700,
        take_profit=1.1200,
        strategy_id="strategy_v1",
        reason="Phase 8 End-to-End verified pipeline DEMO order test",
        execute=True,
    )
    res = json.loads(req_json)
    assert res["approved"] is True
    assert res["status"] in ("APPROVED", "EXECUTED", "RECONCILED")
    assert res["request_id"].startswith("REQ-")
    assert res["execution_id"] is not None


@pytest.mark.asyncio
async def test_phase8_2_risk_rejected_order_creates_zero_orders():
    """Verify risk rejection (missing SL or excessive risk) executes ZERO orders on MT5."""
    req_json = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=5.0,  # Exceeds max allowable lot size and 1% risk
        stop_loss=0.0,  # Missing SL violation
        take_profit=1.2000,
        strategy_id="strategy_v1",
        reason="Excessive lot size with missing SL",
        execute=True,
    )
    res = json.loads(req_json)
    assert res["approved"] is False
    assert res["status"] == "REJECTED"
    assert res.get("execution_id") is None
    assert "broker_ticket" not in res or res.get("broker_ticket") is None


@pytest.mark.asyncio
async def test_phase8_3_kill_switch_active_blocks_all_execution():
    """Verify Kill Switch ON blocks all order requests immediately."""
    risk_engine.engage_kill_switch(reason="Phase 8 Kill Switch Emergency Drill", operator="SAFETY_VALIDATOR")
    assert risk_engine.kill_switch_active is True

    req_json = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=1.0800,
        take_profit=1.1000,
        strategy_id="strategy_v1",
        reason="Testing kill switch enforcement",
        execute=True,
    )
    res = json.loads(req_json)
    assert res["approved"] is False
    assert res["status"] == "REJECTED"
    assert "KILL SWITCH" in res["reason"].upper()
    assert res.get("execution_id") is None


@pytest.mark.asyncio
async def test_phase8_4_duplicate_order_protection_idempotency():
    """Verify duplicate order requests cannot result in duplicate orders."""
    res1 = json.loads(request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=1.0750,
        take_profit=1.1100,
        strategy_id="strategy_v1",
        reason="Idempotency test order 1",
        execute=True,
    ))

    # Second submission with identical parameters immediately
    res2 = json.loads(request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=1.0750,
        take_profit=1.1100,
        strategy_id="strategy_v1",
        reason="Idempotency duplicate submission 2",
        execute=True,
    ))

    assert res2["approved"] is False
    assert res2["status"] == "REJECTED"
    assert "Duplicate order" in res2["reason"]


@pytest.mark.asyncio
async def test_phase8_5_fail_closed_on_mt5_unavailable():
    """Verify execution engine fails closed safely when MT5 is disconnected."""
    original_connected = mt5_client.connected
    original_sim = mt5_client.is_simulation_mode
    try:
        mt5_client.connected = False  # Simulate MT5 disconnect
        mt5_client.is_simulation_mode = False

        req_json = request_order(
            symbol="EURUSD",
            side="BUY",
            quantity=0.01,
            stop_loss=1.0800,
            take_profit=1.1000,
            strategy_id="strategy_v1",
            reason="MT5 disconnect safety test",
            execute=True,
        )
        res = json.loads(req_json)
        assert res["approved"] is False
        assert res["status"] == "REJECTED"
        assert "MT5 terminal disconnected" in res["reason"]
    finally:
        mt5_client.connected = original_connected
        mt5_client.is_simulation_mode = original_sim


@pytest.mark.asyncio
async def test_phase8_6_kill_switch_persistence_across_restart():
    """Verify kill switch state survives application restart via persistent storage."""
    # 1. Engage kill switch
    risk_engine.engage_kill_switch(reason="Durable Restart Test Reason", operator="OPERATOR_RESTART_TEST")
    assert risk_engine.kill_switch_active is True

    # 2. Simulate backend restart by instantiating fresh RiskEngine reading the persistent file
    fresh_risk_engine = RiskEngine()
    assert fresh_risk_engine.kill_switch_active is True
    assert "Durable Restart Test Reason" in fresh_risk_engine.kill_switch_reason
    assert fresh_risk_engine.kill_switch_operator == "OPERATOR_RESTART_TEST"


@pytest.mark.asyncio
async def test_phase8_7_candidate_cannot_auto_activate_without_human_gate():
    """Verify AI cannot directly activate strategy candidates and LIVE mode is prohibited."""
    ver = f"v1.8.{uuid.uuid4().hex[:4]}"
    cand_res = json.loads(create_strategy_candidate(
        strategy_id="strategy_v1",
        version=ver,
        parameters={"ema_fast": 12, "ema_slow": 36},
        rules="Optimized fast crossover",
    ))
    assert cand_res["status"] == "CANDIDATE"

    # Create dummy experiment record to test review endpoint
    exp_id = f"EXP-GATE-{uuid.uuid4().hex[:6]}"
    from backend.app.models.research import Experiment
    async with async_session_maker() as session:
        exp = Experiment(
            experiment_id=exp_id,
            experiment_name="Human Review Gate Test",
            strategy_id="strategy_v1",
            strategy_version=ver,
            status="CANDIDATE",
            parameters_json="{}",
            action="PENDING_HUMAN_REVIEW",
        )
        session.add(exp)
        await session.commit()

    # AI runtime cannot change it to ACTIVE or deploy LIVE
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        live_res = await ac.post(
            f"/api/research/experiments/{exp_id}/review",
            json={"decision": "LIVE_ACTIVE", "operator_comment": "Attempting unauthorized live push"},
        )
        # Must be blocked with 403 Forbidden
        assert live_res.status_code == 403
        assert "LIVE trading deployment is strictly disabled" in live_res.json()["detail"]


@pytest.mark.asyncio
async def test_phase8_8_auditability_of_safety_events():
    """Verify all critical safety events are recorded durably in the database."""
    # Place at least one request to guarantee records exist
    request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=1.0700,
        take_profit=1.1200,
        strategy_id="strategy_v1",
        reason="Auditability test record",
        execute=False,
    )
    async with async_session_maker() as session:
        stmt = select(OrderRequestModel).order_by(OrderRequestModel.created_at.desc()).limit(10)
        res = await session.execute(stmt)
        requests = list(res.scalars().all())
        assert len(requests) > 0
        for r in requests:
            assert r.request_id.startswith("REQ-")
            assert r.symbol is not None
            assert r.side in ("BUY", "SELL", "UNKNOWN")
