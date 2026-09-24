"""Deterministic Risk Gate & Controlled Order Request Tools for AI Agent."""
import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from agents import function_tool
from sqlalchemy import select

from backend.app.agents.risk.risk_engine import risk_engine
from backend.app.agents.runtime.event_bus import event_bus
from backend.app.core.config import settings
from backend.app.core.constants import OrderStatus
from backend.app.core.logging import logger
from backend.app.database.session import async_session_maker
from backend.app.models.ai_audit import OrderRequestModel
from backend.app.models.trading import Order, Position
from backend.app.schemas.risk import RiskEvaluationRequest
from trading.execution.mt5_client import mt5_client

# In-memory idempotency cache for Phase 4 duplicate order protection: maps key -> timestamp
_recent_order_requests: Dict[str, float] = {}

def clear_idempotency_cache():
    """Clear in-memory idempotency records (useful for test resets)."""
    _recent_order_requests.clear()


def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return loop.run_until_complete(coro)


def get_risk_state() -> str:
    """
    Get current deterministic risk limits, active kill switch state,
    current drawdown, and position limits.
    """
    acc = mt5_client.get_account_info()
    positions = mt5_client.get_open_positions()
    equity = acc.get("equity", 10000.0)
    peak = max(risk_engine.peak_equity, equity)
    curr_dd = round(max(0.0, (peak - equity) / (peak + 1e-9) * 100.0), 2)

    return json.dumps({
        "kill_switch_active": risk_engine.kill_switch_active,
        "kill_switch_reason": risk_engine.kill_switch_reason,
        "kill_switch_operator": risk_engine.kill_switch_operator,
        "dual_state_persistence": {
            "file_persistence": True,
            "db_persistence": True,
            "file_path": str(risk_engine.state_file),
        },
        "account_equity": equity,
        "account_balance": acc.get("balance", 10000.0),
        "peak_equity": peak,
        "current_drawdown_pct": curr_dd,
        "daily_loss_pct": round(getattr(risk_engine, "current_day_loss", 0.0) / (equity + 1e-9) * 100.0, 2),
        "daily_loss_amount": round(getattr(risk_engine, "current_day_loss", 0.0), 2),
        "consecutive_losses": risk_engine.consecutive_losses,
        "open_positions_count": len(positions),
        "hard_limits": {
            "max_risk_per_trade_pct": settings.RISK_PER_TRADE_PCT * 100,  # 1%
            "max_account_drawdown_pct": settings.MAX_ACCOUNT_DRAWDOWN_PCT * 100,  # 10%
            "max_daily_loss_pct": settings.MAX_DAILY_LOSS_PCT * 100,  # 3%
            "max_open_positions": settings.MAX_OPEN_POSITIONS,  # 5
            "max_symbol_exposure": settings.MAX_SYMBOL_EXPOSURE,  # 3
            "max_allowed_spread_pips": settings.MAX_ALLOWED_SPREAD_PIPS,  # 3.0
            "trading_mode": settings.TRADING_MODE,
        },
        "ai_modification_permitted": False,
    }, indent=2)


def calculate_position_size(symbol: str, entry_price: float, stop_loss: float) -> str:
    """
    Calculate strictly risk-managed position volume (lots) based on 1% equity risk and stop distance.
    Does NOT place any orders.
    """
    clean_sym = symbol.upper().strip()
    stop_dist = abs(entry_price - stop_loss)
    if stop_dist <= 0:
        return json.dumps({"error": "Stop loss distance must be positive and non-zero."}, indent=2)

    acc = mt5_client.get_account_info()
    equity = acc.get("equity", 10000.0)
    risk_dollars = equity * settings.RISK_PER_TRADE_PCT

    contract_size = 100.0 if "XAU" in clean_sym else 100000.0
    risk_per_lot = stop_dist * contract_size
    lots = round(max(0.01, min(risk_dollars / risk_per_lot, 10.0)), 2) if risk_per_lot > 0 else 0.01

    if settings.is_demo and lots > settings.DEMO_MAX_ORDER_LOTS:
        lots = settings.DEMO_MAX_ORDER_LOTS

    return json.dumps({
        "symbol": clean_sym,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "stop_distance_points": round(stop_dist, 5),
        "equity": equity,
        "risk_percentage": settings.RISK_PER_TRADE_PCT * 100,
        "risk_amount_dollars": round(risk_dollars, 2),
        "recommended_lots": lots,
    }, indent=2)


def validate_trade_request(
    symbol: str,
    side: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
) -> str:
    """
    Simulate a pre-trade risk check through the Deterministic Risk Engine.
    Verifies stop loss distance, spread, open position limits, and direction without placing an order.
    """
    clean_sym = symbol.upper().strip()
    clean_side = side.upper().strip()

    prices = mt5_client.get_symbol_price(clean_sym)
    acc = mt5_client.get_account_info()
    positions = mt5_client.get_open_positions()
    sym_positions = [p for p in positions if p.get("symbol") == clean_sym]

    req = RiskEvaluationRequest(
        strategy_id="ai_pre_check",
        symbol=clean_sym,
        side=clean_side,
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        account_equity=acc.get("equity", 10000.0),
        account_balance=acc.get("balance", 10000.0),
        current_spread_pips=prices.get("spread_pips", 1.5),
        open_positions_count=len(positions),
        symbol_positions_count=len(sym_positions),
        daily_realized_loss=0.0,
    )

    eval_result = risk_engine.evaluate_order(req)
    return json.dumps({
        "is_approved": eval_result.is_approved,
        "calculated_lots": eval_result.calculated_lots,
        "rejection_reasons": eval_result.rejection_reasons,
        "risk_amount_dollars": eval_result.risk_amount_dollars,
        "metrics_snapshot": eval_result.metrics_snapshot,
    }, indent=2)


def request_order(
    symbol: str,
    side: str,
    quantity: float,
    stop_loss: float,
    take_profit: float,
    strategy_id: str,
    reason: str,
    execute: bool = True,
) -> str:
    """
    SUBMIT AN ORDER PROPOSAL TO THE DETERMINISTIC RISK ENGINE & EXECUTION ENGINE.
    The AI agent does NOT place broker orders directly.
    Every proposal undergoes:
    1. Hard Kill Switch check
    2. Account exposure check
    3. Daily loss & drawdown check
    4. Position size limit check
    5. Spread limit check
    6. Stop-loss requirement check
    If approved by the Risk Engine and execute=True, routes strictly to MT5 DEMO.
    If rejected, the order is safely blocked and logged in the journal.
    """
    async def _async_request():
        clean_sym = symbol.upper().strip()
        clean_side = side.upper().strip()
        request_id = f"REQ-{uuid.uuid4().hex[:10].upper()}"
        client_order_id = f"ORD-{uuid.uuid4().hex[:10].upper()}"

        # 1. Parameter and Safety Pre-Checks
        pre_rejection_reasons = []

        if risk_engine.kill_switch_active:
            pre_rejection_reasons.append(f"Emergency kill switch is ACTIVE ({risk_engine.kill_switch_reason}). All order requests are blocked.")

        if not mt5_client.connected and not mt5_client.is_simulation_mode:
            pre_rejection_reasons.append("MT5 terminal disconnected. System fails closed.")

        if not clean_sym or len(clean_sym) < 3 or not clean_sym.replace("/", "").isalnum():
            pre_rejection_reasons.append(f"Invalid symbol '{symbol}'. Must be a valid trading symbol.")

        if not strategy_id or not strategy_id.strip():
            pre_rejection_reasons.append("Strategy ID is required for order requests.")

        if quantity <= 0:
            pre_rejection_reasons.append(f"Invalid order quantity {quantity}: Must be strictly positive.")

        if stop_loss is None or stop_loss <= 0:
            pre_rejection_reasons.append("Mandatory Stop Loss missing or non-positive. Orders without stop loss are strictly prohibited.")

        # If any pre-checks fail, journal and reject immediately
        if pre_rejection_reasons:
            err_reason = pre_rejection_reasons[0]
            logger.warning(f"Order proposal {request_id} rejected at pre-check: {err_reason}")
            async with async_session_maker() as session:
                req_record = OrderRequestModel(
                    request_id=request_id,
                    symbol=clean_sym or "UNKNOWN",
                    side=clean_side or "UNKNOWN",
                    quantity=max(0.0, quantity or 0.0),
                    stop_loss=stop_loss or 0.0,
                    take_profit=take_profit or 0.0,
                    strategy_id=strategy_id or "unknown",
                    reason=reason or "",
                    is_approved=False,
                    rejection_reasons_json=json.dumps(pre_rejection_reasons),
                    risk_evaluation_json=json.dumps({"pre_check_failure": True}),
                    approved_lots=0.0,
                    execution_status="REJECTED",
                )
                session.add(req_record)
                await session.commit()

            await event_bus.publish(
                event_type="ORDER_REJECTED",
                component="ai_risk_gate",
                message=f"Order proposal {request_id} rejected: {err_reason}",
                details={"request_id": request_id, "reasons": pre_rejection_reasons},
            )
            return {
                "approved": False,
                "status": "REJECTED",
                "request_id": request_id,
                "reason": err_reason,
                "risk_check": {"approved": False, "rejection_reasons": pre_rejection_reasons},
            }

        # 2. Fetch market prices and account info (Fail-Closed)
        try:
            acc = mt5_client.get_account_info()
            if not acc or acc.get("equity") is None or acc.get("balance") is None:
                raise ValueError("Account telemetry missing equity or balance.")
            positions = mt5_client.get_open_positions()
            sym_positions = [p for p in positions if p.get("symbol") == clean_sym]
        except Exception as e:
            err_reason = f"Account state unavailable (fail-closed): {e}"
            logger.error(f"Order proposal {request_id} failed: {err_reason}")
            async with async_session_maker() as session:
                req_record = OrderRequestModel(
                    request_id=request_id,
                    symbol=clean_sym,
                    side=clean_side,
                    quantity=quantity,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    strategy_id=strategy_id,
                    reason=reason,
                    is_approved=False,
                    rejection_reasons_json=json.dumps([err_reason]),
                    risk_evaluation_json=json.dumps({"error": str(e)}),
                    approved_lots=0.0,
                    execution_status="REJECTED",
                )
                session.add(req_record)
                await session.commit()
            return {
                "approved": False,
                "status": "REJECTED",
                "request_id": request_id,
                "reason": err_reason,
                "risk_check": {"approved": False, "rejection_reasons": [err_reason]},
            }

        try:
            prices = mt5_client.get_symbol_price(clean_sym)
            if not prices or prices.get("ask") is None or prices.get("bid") is None:
                raise ValueError(f"Price data for {clean_sym} unavailable.")
        except Exception as e:
            err_reason = f"Market data unavailable (fail-closed): {e}"
            logger.error(f"Order proposal {request_id} failed: {err_reason}")
            async with async_session_maker() as session:
                req_record = OrderRequestModel(
                    request_id=request_id,
                    symbol=clean_sym,
                    side=clean_side,
                    quantity=quantity,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    strategy_id=strategy_id,
                    reason=reason,
                    is_approved=False,
                    rejection_reasons_json=json.dumps([err_reason]),
                    risk_evaluation_json=json.dumps({"error": str(e)}),
                    approved_lots=0.0,
                    execution_status="REJECTED",
                )
                session.add(req_record)
                await session.commit()
            return {
                "approved": False,
                "status": "REJECTED",
                "request_id": request_id,
                "reason": err_reason,
                "risk_check": {"approved": False, "rejection_reasons": [err_reason]},
            }

        current_price = prices["ask"] if clean_side == "BUY" else prices["bid"]
        if current_price <= 0:
            current_price = stop_loss + 0.001 if clean_side == "BUY" else stop_loss - 0.001

        # 3. Construct Risk Evaluation Request
        risk_req = RiskEvaluationRequest(
            strategy_id=strategy_id,
            symbol=clean_sym,
            side=clean_side,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            account_equity=acc.get("equity", 10000.0),
            account_balance=acc.get("balance", 10000.0),
            current_spread_pips=prices.get("spread_pips", 1.5),
            open_positions_count=len(positions),
            symbol_positions_count=len(sym_positions),
            daily_realized_loss=0.0,
        )

        # 4. DETERMINISTIC RISK EVALUATION (Fail-Closed)
        try:
            risk_result = risk_engine.evaluate_order(risk_req)
        except Exception as e:
            logger.error(f"Risk engine evaluation exception: {e}")
            err_reason = f"Risk engine unavailable (fail-closed): {str(e)}"
            async with async_session_maker() as session:
                req_record = OrderRequestModel(
                    request_id=request_id,
                    symbol=clean_sym,
                    side=clean_side,
                    quantity=quantity,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    strategy_id=strategy_id,
                    reason=reason,
                    is_approved=False,
                    rejection_reasons_json=json.dumps([err_reason]),
                    risk_evaluation_json=json.dumps({"exception": str(e)}),
                    approved_lots=0.0,
                    execution_status="REJECTED",
                )
                session.add(req_record)
                await session.commit()
            return {
                "approved": False,
                "status": "REJECTED",
                "request_id": request_id,
                "reason": err_reason,
                "risk_check": {"approved": False, "rejection_reasons": [err_reason]},
            }

        # 5. Record OrderRequest in DB journal / audit trail
        async with async_session_maker() as session:
            req_record = OrderRequestModel(
                request_id=request_id,
                symbol=clean_sym,
                side=clean_side,
                quantity=quantity,
                stop_loss=stop_loss,
                take_profit=take_profit,
                strategy_id=strategy_id,
                reason=reason,
                is_approved=risk_result.is_approved,
                rejection_reasons_json=json.dumps(risk_result.rejection_reasons) if not risk_result.is_approved else None,
                risk_evaluation_json=json.dumps(risk_result.metrics_snapshot),
                approved_lots=risk_result.calculated_lots if risk_result.is_approved else 0.0,
                execution_status="APPROVED" if risk_result.is_approved else "REJECTED",
            )
            session.add(req_record)
            await session.commit()

        # 7. If Risk Engine rejected, return failure immediately
        if not risk_result.is_approved:
            primary_reason = risk_result.rejection_reasons[0] if risk_result.rejection_reasons else "Risk check failed"
            await event_bus.publish(
                event_type="ORDER_REJECTED",
                component="risk_engine",
                message=f"Order proposal {request_id} rejected: {primary_reason}",
                details={"request_id": request_id, "reasons": risk_result.rejection_reasons},
            )
            return {
                "approved": False,
                "status": "REJECTED",
                "request_id": request_id,
                "reason": primary_reason,
                "risk_check": {
                    "approved": False,
                    "rejection_reasons": risk_result.rejection_reasons,
                    "metrics": risk_result.metrics_snapshot,
                },
            }

        # 8. Risk Engine Approved -> Persist in Journal / Audit Trail
        await event_bus.publish(
            event_type="ORDER_APPROVED",
            component="risk_engine",
            message=f"Order proposal {request_id} approved by Deterministic Risk Engine: {clean_sym} {clean_side} {risk_result.calculated_lots} lots",
            details={
                "request_id": request_id,
                "calculated_lots": risk_result.calculated_lots,
                "risk_amount_dollars": risk_result.risk_amount_dollars,
            },
        )

        # If not executing directly to MT5 (e.g. Phase 3 gate validation)
        if not execute:
            return {
                "approved": True,
                "status": "APPROVED",
                "request_id": request_id,
                "client_order_id": client_order_id,
                "symbol": clean_sym,
                "side": clean_side,
                "approved_lots": risk_result.calculated_lots,
                "risk_amount_dollars": risk_result.risk_amount_dollars,
                "risk_check": {
                    "approved": True,
                    "rejection_reasons": [],
                    "metrics": risk_result.metrics_snapshot,
                },
                "reason": "Order approved by Deterministic Risk Engine and recorded in journal audit.",
            }

        # 9. Phase 4 Execution Engine: MT5 DEMO Execution Flow
        # A. Duplicate-order protection (Idempotency Gate)
        idemp_key = f"{strategy_id}:{clean_sym}:{clean_side}"
        now_ts = time.time()
        last_ts = _recent_order_requests.get(idemp_key)
        if last_ts and (now_ts - last_ts) < settings.IDEMPOTENCY_WINDOW_SECONDS:
            err_reason = f"Duplicate order rejected by Idempotency Gate: recent {clean_side} order for {clean_sym} already placed within {settings.IDEMPOTENCY_WINDOW_SECONDS}s."
            logger.warning(f"Order proposal {request_id} duplicate rejected: {err_reason}")
            async with async_session_maker() as session:
                stmt = select(OrderRequestModel).where(OrderRequestModel.request_id == request_id)
                res = await session.execute(stmt)
                rec = res.scalar_one_or_none()
                if rec:
                    rec.execution_status = "REJECTED"
                    rec.execution_error = err_reason
                    await session.commit()
            return {
                "approved": False,
                "status": "REJECTED",
                "request_id": request_id,
                "reason": err_reason,
                "duplicate_rejected": True,
            }
        _recent_order_requests[idemp_key] = now_ts

        # B. Transition state to SUBMITTING with unique execution_id
        execution_id = f"EXEC-{uuid.uuid4().hex[:10].upper()}"
        async with async_session_maker() as session:
            stmt = select(OrderRequestModel).where(OrderRequestModel.request_id == request_id)
            res = await session.execute(stmt)
            rec = res.scalar_one_or_none()
            if rec:
                rec.execution_id = execution_id
                rec.execution_status = "SUBMITTING"
                await session.commit()

        # C. Submit to MT5 DEMO Gateway (DEMO ONLY)
        volume_to_execute = risk_result.calculated_lots
        if settings.is_demo and volume_to_execute > settings.DEMO_MAX_ORDER_LOTS:
            volume_to_execute = settings.DEMO_MAX_ORDER_LOTS

        try:
            broker_res = mt5_client.place_order(
                symbol=clean_sym,
                side=clean_side,
                volume=volume_to_execute,
                price=current_price,
                sl=stop_loss,
                tp=take_profit,
                comment=f"{strategy_id[:8]}:{request_id[:8]}",
            )
        except Exception as e:
            broker_res = {"success": False, "error": f"MT5 submission exception: {str(e)}"}

        # D. Process Broker Result and Persist to Database & Journal
        is_success = bool(broker_res and broker_res.get("success", False))

        async with async_session_maker() as session:
            stmt = select(OrderRequestModel).where(OrderRequestModel.request_id == request_id)
            res = await session.execute(stmt)
            rec = res.scalar_one_or_none()

            if is_success:
                broker_ticket = broker_res.get("ticket")
                broker_deal = broker_res.get("deal")
                if rec:
                    rec.execution_status = "EXECUTED"
                    rec.broker_ticket = broker_ticket
                    rec.broker_deal_id = broker_deal
                    rec.execution_error = None

                # Create Order record in database journal
                order_rec = Order(
                    client_order_id=client_order_id,
                    strategy_id=strategy_id,
                    symbol=clean_sym,
                    side=clean_side,
                    order_type="MARKET",
                    quantity=risk_result.calculated_lots,
                    price=float(broker_res.get("price", current_price)),
                    sl=stop_loss,
                    tp=take_profit,
                    status="EXECUTED",
                    risk_evaluation_json=json.dumps(risk_result.metrics_snapshot),
                    broker_ticket=broker_ticket,
                    broker_response=json.dumps(broker_res),
                    execution_latency_ms=float(broker_res.get("latency_ms", 0.0)),
                )
                session.add(order_rec)
                await session.commit()

                await event_bus.publish(
                    event_type="ORDER_EXECUTED",
                    component="execution_engine",
                    message=f"Order {request_id} ({execution_id}) EXECUTED on MT5 DEMO: Ticket={broker_ticket}",
                    details={
                        "request_id": request_id,
                        "execution_id": execution_id,
                        "ticket": broker_ticket,
                        "deal": broker_deal,
                        "symbol": clean_sym,
                        "side": clean_side,
                        "lots": risk_result.calculated_lots,
                    },
                )

                return {
                    "approved": True,
                    "status": "EXECUTED",
                    "request_id": request_id,
                    "execution_id": execution_id,
                    "client_order_id": client_order_id,
                    "symbol": clean_sym,
                    "side": clean_side,
                    "approved_lots": risk_result.calculated_lots,
                    "broker_ticket": broker_ticket,
                    "broker_deal_id": broker_deal,
                    "mt5_result": broker_res,
                    "reason": "Order approved by Deterministic Risk Engine and successfully executed on MT5 DEMO.",
                }
            else:
                err_msg = broker_res.get("error") or broker_res.get("message") or "Broker order execution rejected"
                if rec:
                    rec.execution_status = "FAILED"
                    rec.execution_error = err_msg
                await session.commit()

                await event_bus.publish(
                    event_type="ORDER_FAILED",
                    component="execution_engine",
                    message=f"Order {request_id} ({execution_id}) FAILED on MT5 DEMO: {err_msg}",
                    details={
                        "request_id": request_id,
                        "execution_id": execution_id,
                        "error": err_msg,
                    },
                )

                return {
                    "approved": True,
                    "status": "FAILED",
                    "request_id": request_id,
                    "execution_id": execution_id,
                    "client_order_id": client_order_id,
                    "symbol": clean_sym,
                    "side": clean_side,
                    "approved_lots": risk_result.calculated_lots,
                    "reason": f"MT5 execution failed: {err_msg}",
                    "broker_error": err_msg,
                }

    data = _run_async(_async_request())
    return json.dumps(data, indent=2)
