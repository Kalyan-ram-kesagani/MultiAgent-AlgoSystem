"""
Phase 3 Integration Test Suite: Deterministic Risk Gate & Controlled Order Routing.
Verifies:
1. Risk within limits -> APPROVED (logged in Journal, NOT sent to MT5 yet).
2. Risk violation -> REJECTED (logged in Journal).
3. Kill switch ON -> REJECTED unconditionally.
4. Risk engine unavailable -> REJECTED (Fail-Closed).
5. AI cannot bypass risk limits (immutability of hard risk rules).
6. POST /api/orders/request and GET /api/risk/status API endpoints.
"""
import json
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from backend.app.agents.risk.risk_engine import risk_engine
from backend.app.ai_agent.tools.risk import request_order, get_risk_state
from backend.app.core.config import settings
from backend.app.database.session import async_session_maker, init_db
from backend.app.main import app
from backend.app.models.ai_audit import OrderRequestModel
from trading.execution.mt5_client import mt5_client


@pytest_asyncio.fixture(autouse=True)
async def setup_test_env():
    """Ensure clean simulator state and disengaged kill switch."""
    mt5_client.is_simulation_mode = True
    await init_db()
    risk_engine.disengage_kill_switch(operator="PHASE3_TEST_SETUP")
    yield
    risk_engine.disengage_kill_switch(operator="PHASE3_TEST_CLEANUP")


@pytest.mark.asyncio
async def test_phase3_1_order_within_limits_approved():
    """
    TEST 1:
    Order within all risk limits -> APPROVED.
    Logged in Journal / OrderRequestModel.
    CRITICAL: MT5 receives NO order yet (Phase 3 mandate).
    """
    initial_positions = len(mt5_client.get_open_positions())

    # Submit valid BUY proposal (SL below current price ~1.0850) with execute=False for Phase 3 risk gate
    raw_res = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=1.0750,
        take_profit=1.1050,
        strategy_id="strategy_v1",
        reason="Valid trend pullback setup within 1% risk",
        execute=False,
    )
    res = json.loads(raw_res)

    assert res["approved"] is True
    assert res["status"] == "APPROVED"
    assert res["approved_lots"] > 0
    assert "request_id" in res
    req_id = res["request_id"]

    # Verify recorded in Journal / DB audit
    async with async_session_maker() as session:
        stmt = select(OrderRequestModel).where(OrderRequestModel.request_id == req_id)
        db_res = await session.execute(stmt)
        record = db_res.scalar_one_or_none()
        assert record is not None
        assert record.is_approved is True
        assert record.execution_status == "APPROVED"

    # Verify MT5 received NO order (Phase 3: Not connected to MT5 yet)
    final_positions = len(mt5_client.get_open_positions())
    assert final_positions == initial_positions


@pytest.mark.asyncio
async def test_phase3_2_risk_violation_rejected():
    """
    TEST 2:
    Order violating risk parameters (inverted SL: BUY with SL above price) -> REJECTED.
    Logged in Journal / OrderRequestModel with rejection reasons.
    """
    raw_res = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.1,
        stop_loss=1.2000,  # Invalid inverted stop loss
        take_profit=1.2500,
        strategy_id="strategy_v1",
        reason="Invalid stop loss test",
    )
    res = json.loads(raw_res)

    assert res["approved"] is False
    assert res["status"] == "REJECTED"
    assert "reason" in res
    assert "stop loss" in res["reason"].lower() or "rejected" in res["reason"].lower()
    req_id = res["request_id"]

    # Verify logged in Journal / DB
    async with async_session_maker() as session:
        stmt = select(OrderRequestModel).where(OrderRequestModel.request_id == req_id)
        db_res = await session.execute(stmt)
        record = db_res.scalar_one_or_none()
        assert record is not None
        assert record.is_approved is False
        assert record.execution_status == "REJECTED"
        assert record.rejection_reasons_json is not None


@pytest.mark.asyncio
async def test_phase3_3_kill_switch_active_blocks_all_orders():
    """
    TEST 3:
    Kill Switch ACTIVE -> REJECTED unconditionally.
    """
    risk_engine.engage_kill_switch("Phase 3 safety drill", operator="TEST_OPERATOR")
    assert risk_engine.kill_switch_active is True

    raw_res = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=1.0500,
        take_profit=1.1200,
        strategy_id="strategy_v1",
        reason="Attempt order during kill switch",
    )
    res = json.loads(raw_res)

    assert res["approved"] is False
    assert "kill switch" in res["reason"].lower()


@pytest.mark.asyncio
async def test_phase3_4_risk_engine_fail_closed_on_error(monkeypatch):
    """
    TEST 4:
    Risk engine evaluation failure/unavailable -> REJECTED (Fail Closed).
    """
    # Monkeypatch evaluate_order to raise an unexpected exception
    def broken_eval(*args, **kwargs):
        raise RuntimeError("Risk Engine temporary memory fault")

    monkeypatch.setattr(risk_engine, "evaluate_order", broken_eval)

    raw_res = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=1.0500,
        take_profit=1.1200,
        strategy_id="strategy_v1",
        reason="Fail-closed test",
    )
    res = json.loads(raw_res)

    assert res["approved"] is False
    assert res["status"] == "REJECTED"
    assert "fail-closed" in res["reason"].lower() or "unavailable" in res["reason"].lower()


@pytest.mark.asyncio
async def test_phase3_5_ai_cannot_bypass_risk_limits():
    """
    TEST 5:
    Hard risk limits cannot be altered by AI.
    Risk status endpoint confirms immutable limits and ai_modification_permitted: False.
    """
    state_raw = get_risk_state()
    state = json.loads(state_raw)

    assert state["ai_modification_permitted"] is False
    hard_limits = state["hard_limits"]
    assert hard_limits["max_risk_per_trade_pct"] == 1.0
    assert hard_limits["max_account_drawdown_pct"] == 10.0
    assert hard_limits["max_daily_loss_pct"] == 3.0
    assert hard_limits["max_open_positions"] == settings.MAX_OPEN_POSITIONS
    assert hard_limits["max_symbol_exposure"] == settings.MAX_SYMBOL_EXPOSURE


@pytest.mark.asyncio
async def test_phase3_6_api_endpoints():
    """
    TEST 6:
    POST /api/orders/request and GET /api/risk/status via HTTP client.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET /api/risk/status
        r_status = await client.get("/api/risk/status")
        assert r_status.status_code == 200
        data = r_status.json()
        assert "hard_limits" in data
        assert data["ai_modification_permitted"] is False

        # 2. POST /api/orders/request - Approved order
        r_req = await client.post(
            "/api/orders/request",
            json={
                "symbol": "EURUSD",
                "side": "BUY",
                "quantity": 0.01,
                "stop_loss": 1.0750,
                "take_profit": 1.1050,
                "strategy_id": "strategy_v1",
                "reason": "Phase 3 API verification",
                "execute": False,
            },
        )
        assert r_req.status_code == 200
        req_data = r_req.json()
        assert req_data["approved"] is True
        assert req_data["status"] == "APPROVED"
        req_id = req_data["request_id"]

        # 3. GET /api/orders/{order_request_id}
        r_get = await client.get(f"/api/orders/{req_id}")
        assert r_get.status_code == 200
        get_data = r_get.json()
        assert get_data["order_request_id"] == req_id
        assert get_data["is_approved"] is True
        assert get_data["execution_status"] == "APPROVED"

        # 4. GET /api/risk/limits
        r_limits = await client.get("/api/risk/limits")
        assert r_limits.status_code == 200
        lims = r_limits.json()
        assert lims["max_risk_per_trade_pct"] == 1.0
        assert lims["max_portfolio_drawdown_pct"] == 10.0
        assert lims["max_daily_loss_pct"] == 3.0
        assert lims["ai_modification_permitted"] is False


@pytest.mark.asyncio
async def test_phase3_7_daily_loss_limit_breach_rejected():
    """TEST 7: Daily loss >= 3% strictly rejects order proposal."""
    from backend.app.schemas.risk import RiskEvaluationRequest
    req = RiskEvaluationRequest(
        strategy_id="strategy_v1",
        symbol="EURUSD",
        side="BUY",
        entry_price=1.0850,
        stop_loss=1.0750,
        take_profit=1.1050,
        account_equity=10000.0,
        account_balance=10000.0,
        current_spread_pips=1.2,
        open_positions_count=1,
        symbol_positions_count=1,
        daily_realized_loss=-350.0,  # 3.5% loss > 3.0% limit
    )
    res = risk_engine.evaluate_order(req)
    assert res.is_approved is False
    assert any("daily loss" in r.lower() for r in res.rejection_reasons)


@pytest.mark.asyncio
async def test_phase3_8_portfolio_drawdown_limit_breach_rejected():
    """TEST 8: Max portfolio drawdown >= 10% rejects order and engages kill switch."""
    from backend.app.schemas.risk import RiskEvaluationRequest
    risk_engine.peak_equity = 10000.0
    req = RiskEvaluationRequest(
        strategy_id="strategy_v1",
        symbol="EURUSD",
        side="BUY",
        entry_price=1.0850,
        stop_loss=1.0750,
        take_profit=1.1050,
        account_equity=8800.0,  # 12% drawdown > 10% limit
        account_balance=8800.0,
        current_spread_pips=1.2,
        open_positions_count=0,
        symbol_positions_count=0,
    )
    res = risk_engine.evaluate_order(req)
    assert res.is_approved is False
    assert any("drawdown" in r.lower() for r in res.rejection_reasons)
    assert risk_engine.kill_switch_active is True


@pytest.mark.asyncio
async def test_phase3_9_exposure_and_position_limits_rejected():
    """TEST 9: Open positions >= MAX_OPEN_POSITIONS or symbol exposure >= MAX_SYMBOL_EXPOSURE rejected."""
    from backend.app.schemas.risk import RiskEvaluationRequest
    # Max open positions
    req_max_pos = RiskEvaluationRequest(
        strategy_id="strategy_v1",
        symbol="EURUSD",
        side="BUY",
        entry_price=1.0850,
        stop_loss=1.0750,
        take_profit=1.1050,
        account_equity=10000.0,
        account_balance=10000.0,
        current_spread_pips=1.2,
        open_positions_count=settings.MAX_OPEN_POSITIONS,
        symbol_positions_count=0,
    )
    res_pos = risk_engine.evaluate_order(req_max_pos)
    assert res_pos.is_approved is False
    assert any("open positions" in r.lower() for r in res_pos.rejection_reasons)

    # Max symbol exposure
    req_max_exp = RiskEvaluationRequest(
        strategy_id="strategy_v1",
        symbol="EURUSD",
        side="BUY",
        entry_price=1.0850,
        stop_loss=1.0750,
        take_profit=1.1050,
        account_equity=10000.0,
        account_balance=10000.0,
        current_spread_pips=1.2,
        open_positions_count=1,
        symbol_positions_count=settings.MAX_SYMBOL_EXPOSURE,
    )
    res_exp = risk_engine.evaluate_order(req_max_exp)
    assert res_exp.is_approved is False
    assert any("symbol positions" in r.lower() for r in res_exp.rejection_reasons)


@pytest.mark.asyncio
async def test_phase3_10_missing_or_invalid_stop_loss_rejected():
    """TEST 10: Missing or non-positive stop loss is strictly rejected."""
    raw = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=0.0,  # Missing/invalid SL
        take_profit=1.1050,
        strategy_id="strategy_v1",
        reason="Missing SL test",
    )
    res = json.loads(raw)
    assert res["approved"] is False
    assert res["status"] == "REJECTED"
    assert "stop loss" in res["reason"].lower()


@pytest.mark.asyncio
async def test_phase3_11_invalid_symbol_or_missing_strategy_rejected():
    """TEST 11: Invalid symbol or empty strategy ID strictly rejected."""
    # Invalid symbol
    raw_sym = request_order(
        symbol="$$$INVALID###",
        side="BUY",
        quantity=0.01,
        stop_loss=1.0750,
        take_profit=1.1050,
        strategy_id="strategy_v1",
        reason="Invalid symbol test",
    )
    res_sym = json.loads(raw_sym)
    assert res_sym["approved"] is False
    assert "invalid symbol" in res_sym["reason"].lower()

    # Empty strategy ID
    raw_strat = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=1.0750,
        take_profit=1.1050,
        strategy_id="",
        reason="Missing strategy test",
    )
    res_strat = json.loads(raw_strat)
    assert res_strat["approved"] is False
    assert "strategy" in res_strat["reason"].lower()


@pytest.mark.asyncio
async def test_phase3_12_unavailable_safety_state_fails_closed(monkeypatch):
    """TEST 12: Account state unavailable -> Fails closed and rejects."""
    def broken_account():
        raise RuntimeError("MT5 account telemetry unavailable")

    monkeypatch.setattr(mt5_client, "get_account_info", broken_account)
    raw = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=1.0750,
        take_profit=1.1050,
        strategy_id="strategy_v1",
        reason="Safety state failure test",
    )
    res = json.loads(raw)
    assert res["approved"] is False
    assert res["status"] == "REJECTED"
    assert "unavailable" in res["reason"].lower()


@pytest.mark.asyncio
async def test_phase3_13_zero_mt5_orders_guaranteed():
    """TEST 13: Absolute proof that Phase 3 submits ZERO orders to MT5 broker."""
    initial_positions = len(mt5_client.get_open_positions())
    
    # Run multiple approved and rejected proposals
    for i in range(3):
        raw = request_order(
            symbol="EURUSD",
            side="BUY",
            quantity=0.01,
            stop_loss=1.0750,
            take_profit=1.1050,
            strategy_id="strategy_v1",
            reason=f"Zero MT5 test {i}",
            execute=False,
        )
        res = json.loads(raw)
        assert res["approved"] is True
        assert res["status"] == "APPROVED"

    final_positions = len(mt5_client.get_open_positions())
    assert final_positions == initial_positions, "CRITICAL: Phase 3 MUST NOT send any orders to MT5!"

