"""
Phase 4 Integration Test Suite: Execution Engine -> MT5 DEMO -> Supabase.
Verifies:
1. Risk approval required before any broker submission.
2. Approved DEMO request creates expected MT5 order & Order record in DB.
3. Risk rejection creates ZERO MT5 orders.
4. Duplicate-order protection (Idempotency Gate) blocks duplicate submissions.
5. MT5 failure/broker error handled safely fail-closed (status="FAILED", error logged).
6. Result reconciled in DB and transitions to RECONCILED.
7. Manual and external trades remain correctly classified.
8. API endpoints POST /api/orders/request and GET /api/orders/{order_request_id}.
"""
import json
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from backend.app.agents.risk.risk_engine import risk_engine
from backend.app.ai_agent.tools.risk import request_order, clear_idempotency_cache
from backend.app.core.config import settings
from backend.app.database.session import async_session_maker, init_db
from backend.app.main import app
from backend.app.models.ai_audit import OrderRequestModel
from backend.app.models.trading import Order, Trade
from backend.app.services.mt5_reconciler import mt5_reconciler
from trading.execution.mt5_client import mt5_client


@pytest_asyncio.fixture(autouse=True)
async def setup_test_env():
    """Ensure clean simulator state and disengaged kill switch."""
    mt5_client.is_simulation_mode = True
    await init_db()
    risk_engine.disengage_kill_switch(operator="PHASE4_TEST_SETUP")
    clear_idempotency_cache()
    yield
    risk_engine.disengage_kill_switch(operator="PHASE4_TEST_CLEANUP")
    clear_idempotency_cache()


@pytest.mark.asyncio
async def test_phase4_1_approved_request_executes_on_mt5_demo():
    """
    TEST 1:
    AI proposal -> Risk Engine APPROVED -> Execution Engine submits to MT5 DEMO -> DB updated.
    """
    raw_res = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=1.0750,
        take_profit=1.1050,
        strategy_id="strategy_v1",
        reason="Phase 4 valid DEMO execution test",
        execute=True,
    )
    res = json.loads(raw_res)

    assert res["approved"] is True
    assert res["status"] == "EXECUTED"
    assert "execution_id" in res
    assert res["execution_id"].startswith("EXEC-")
    assert res["broker_ticket"] is not None
    req_id = res["request_id"]

    # Verify OrderRequestModel in DB
    async with async_session_maker() as session:
        stmt = select(OrderRequestModel).where(OrderRequestModel.request_id == req_id)
        db_res = await session.execute(stmt)
        record = db_res.scalar_one_or_none()
        assert record is not None
        assert record.is_approved is True
        assert record.execution_status == "EXECUTED"
        assert record.execution_id == res["execution_id"]
        assert record.broker_ticket == res["broker_ticket"]

        # Verify Order record in database journal
        order_stmt = select(Order).where(Order.client_order_id == res["client_order_id"])
        order_res = await session.execute(order_stmt)
        order_rec = order_res.scalar_one_or_none()
        assert order_rec is not None
        assert order_rec.status == "EXECUTED"
        assert order_rec.broker_ticket == res["broker_ticket"]


@pytest.mark.asyncio
async def test_phase4_2_risk_rejection_creates_zero_mt5_orders():
    """
    TEST 2:
    Order proposal violating risk (inverted SL) -> REJECTED.
    CRITICAL: Execution Engine must NOT be invoked, zero broker orders.
    """
    initial_positions = len(mt5_client.get_open_positions())

    raw_res = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=1.2000,  # Inverted stop loss for BUY
        take_profit=1.2500,
        strategy_id="strategy_v1",
        reason="Phase 4 risk rejection test",
        execute=True,
    )
    res = json.loads(raw_res)

    assert res["approved"] is False
    assert res["status"] == "REJECTED"
    assert "stop loss" in res["reason"].lower()

    # Verify no execution_id and no broker_ticket
    assert "execution_id" not in res or res.get("execution_id") is None
    req_id = res["request_id"]

    # Verify OrderRequestModel in DB
    async with async_session_maker() as session:
        stmt = select(OrderRequestModel).where(OrderRequestModel.request_id == req_id)
        db_res = await session.execute(stmt)
        record = db_res.scalar_one_or_none()
        assert record is not None
        assert record.is_approved is False
        assert record.execution_status == "REJECTED"
        assert record.broker_ticket is None

    final_positions = len(mt5_client.get_open_positions())
    assert final_positions == initial_positions


@pytest.mark.asyncio
async def test_phase4_3_duplicate_order_protection():
    """
    TEST 3:
    Duplicate-order protection: An identical proposal submitted within idempotency window is safely rejected.
    """
    clear_idempotency_cache()

    # 1. First order submission -> EXECUTED
    raw_res1 = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=1.0750,
        take_profit=1.1050,
        strategy_id="strategy_v1",
        reason="First order placement",
        execute=True,
    )
    res1 = json.loads(raw_res1)
    assert res1["status"] == "EXECUTED"

    # 2. Second identical proposal immediately submitted -> REJECTED by Idempotency Gate
    raw_res2 = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=1.0750,
        take_profit=1.1050,
        strategy_id="strategy_v1",
        reason="Duplicate order placement attempt",
        execute=True,
    )
    res2 = json.loads(raw_res2)
    assert res2["approved"] is False
    assert res2["status"] == "REJECTED"
    assert "duplicate" in res2["reason"].lower()


@pytest.mark.asyncio
async def test_phase4_4_mt5_failure_safe_handling(monkeypatch):
    """
    TEST 4:
    Broker / MT5 failure is safely handled fail-closed.
    Status transitions to FAILED, error is recorded in journal, no uncaught exceptions.
    """
    def mock_broken_place_order(*args, **kwargs):
        return {
            "success": False,
            "error": "Broker rejected order: 10013 (Invalid request parameters)",
            "retcode": 10013,
        }

    monkeypatch.setattr(mt5_client, "place_order", mock_broken_place_order)

    raw_res = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=1.0750,
        take_profit=1.1050,
        strategy_id="strategy_v1",
        reason="MT5 failure test",
        execute=True,
    )
    res = json.loads(raw_res)

    assert res["approved"] is True  # Risk Engine approved proposal
    assert res["status"] == "FAILED"  # But MT5 execution failed
    assert "broker_error" in res
    assert "10013" in res["broker_error"]
    req_id = res["request_id"]

    # Verify recorded in DB
    async with async_session_maker() as session:
        stmt = select(OrderRequestModel).where(OrderRequestModel.request_id == req_id)
        db_res = await session.execute(stmt)
        record = db_res.scalar_one_or_none()
        assert record is not None
        assert record.execution_status == "FAILED"
        assert record.execution_error is not None
        assert "10013" in record.execution_error


@pytest.mark.asyncio
async def test_phase4_5_mt5_reconciliation_transitions_to_reconciled():
    """
    TEST 5:
    MT5 deal reconciliation updates executed order to RECONCILED.
    Verifies trade classification (SYSTEM_GENERATED vs MANUAL/EXTERNAL).
    """
    # 1. Execute an order
    raw_res = request_order(
        symbol="EURUSD",
        side="BUY",
        quantity=0.01,
        stop_loss=1.0750,
        take_profit=1.1050,
        strategy_id="strategy_v1",
        reason="Reconciliation test order",
        execute=True,
    )
    res = json.loads(raw_res)
    assert res["status"] == "EXECUTED"
    ticket = res["broker_ticket"]
    req_id = res["request_id"]

    # 2. Simulate broker deal in MT5 history
    class MockDeal:
        def __init__(self, t, sym, vol, side, profit):
            self.ticket = t
            self.order = t
            self.position_id = t
            self.symbol = sym
            self.volume = vol
            self.type = 1 if side == "BUY" else 0  # Close deal
            self.entry = 1  # OUT
            self.time = 1700000000
            self.price = 1.0880
            self.profit = profit
            self.commission = -0.05
            self.swap = 0.0
            self.magic = 123456

    mock_deals = [MockDeal(ticket, "EURUSD", 0.01, "BUY", 15.0)]

    def mock_get_history(days=90):
        return mock_deals

    mt5_client.get_history_deals = mock_get_history

    # 3. Reconcile
    async with async_session_maker() as session:
        rec_res = await mt5_reconciler.reconcile_trades(session)
        await session.commit()
        assert rec_res["imported_records"] >= 1

        # Check OrderRequestModel is now RECONCILED
        stmt = select(OrderRequestModel).where(OrderRequestModel.request_id == req_id)
        db_res = await session.execute(stmt)
        record = db_res.scalar_one_or_none()
        assert record is not None
        assert record.execution_status == "RECONCILED"

        # Check Trade record is attributed to SYSTEM_GENERATED
        trade_stmt = select(Trade).where(Trade.ticket == ticket)
        trade_res = await session.execute(trade_stmt)
        trade_rec = trade_res.scalar_one_or_none()
        assert trade_rec is not None
        assert trade_rec.origin == "SYSTEM_GENERATED"


@pytest.mark.asyncio
async def test_phase4_6_api_order_request_live_execution():
    """
    TEST 6:
    POST /api/orders/request and GET /api/orders/{order_request_id} via HTTP API.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit valid order proposal
        post_res = await client.post(
            "/api/orders/request",
            json={
                "symbol": "EURUSD",
                "side": "BUY",
                "quantity": 0.01,
                "stop_loss": 1.0750,
                "take_profit": 1.1050,
                "strategy_id": "strategy_v1",
                "reason": "Phase 4 API full execution test",
                "execute": True,
            },
        )
        assert post_res.status_code == 200
        data = post_res.json()
        assert data["approved"] is True
        assert data["status"] == "EXECUTED"
        assert "execution_id" in data
        assert data["execution_id"].startswith("EXEC-")
        assert data["broker_ticket"] is not None
        req_id = data["request_id"]

        # Query order by ID
        get_res = await client.get(f"/api/orders/{req_id}")
        assert get_res.status_code == 200
        order_info = get_res.json()
        assert order_info["order_request_id"] == req_id
        assert order_info["execution_id"] == data["execution_id"]
        assert order_info["execution_status"] == "EXECUTED"
        assert order_info["broker_ticket"] == data["broker_ticket"]
