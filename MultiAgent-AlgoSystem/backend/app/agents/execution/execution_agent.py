"""Agent #8 — Execution Agent: Controlled Order Placement, Idempotency, and Broker Reconciliation."""
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.risk.risk_engine import risk_engine
from backend.app.core.config import settings
from backend.app.core.constants import OrderSide, OrderStatus
from backend.app.core.logging import logger
from backend.app.models.trading import Order, Position, Signal
from backend.app.schemas.risk import RiskEvaluationRequest
from backend.app.schemas.trading import OrderResponse, SignalCreate
from trading.execution.mt5_client import mt5_client


class ExecutionAgent:
    """Safely transitions signals into executed broker orders strictly through the Risk Engine."""

    # In-memory idempotency cache: maps idempotency_key -> timestamp
    _recent_orders: Dict[str, float] = {}

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session

    def _is_duplicate_order(self, symbol: str, direction: str, strategy_id: str) -> bool:
        """Check if an identical order signature was executed within the idempotency window."""
        key = f"{strategy_id}:{symbol.upper()}:{direction.upper()}"
        now = time.time()
        last_time = self._recent_orders.get(key)
        if last_time and (now - last_time) < settings.IDEMPOTENCY_WINDOW_SECONDS:
            return True
        return False

    def _record_order_signature(self, symbol: str, direction: str, strategy_id: str) -> None:
        key = f"{strategy_id}:{symbol.upper()}:{direction.upper()}"
        self._recent_orders[key] = time.time()

    async def execute_signal(
        self,
        signal: SignalCreate,
        current_open_positions: int = 0,
        current_symbol_positions: int = 0,
        daily_realized_loss: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Process signal through Risk Engine gate before placing order.
        Never bypasses Risk Engine!
        """
        start_time = time.perf_counter()
        client_order_id = f"ORD-{uuid.uuid4().hex[:10].upper()}"

        try:
            from backend.app.agents.runtime import agent_registry
            agent_registry.heartbeat("agent_execution")
        except Exception:
            pass

        # 1. Fail-Closed Check: Verify Gateway connection & health
        if not mt5_client.connected and not mt5_client.is_simulation_mode:

            logger.error("ExecutionAgent blocked: MT5 gateway is disconnected.")
            return {
                "client_order_id": client_order_id,
                "status": OrderStatus.REJECTED,
                "rejection_reasons": ["MT5 Gateway is disconnected from broker trade server."],
                "order": None,
            }

        # 2. Idempotency & Duplicate Order Protection
        if self._is_duplicate_order(signal.symbol, signal.direction, signal.strategy_id):
            logger.warning(
                f"Duplicate order rejected by Idempotency Gate for {signal.symbol} {signal.direction}",
                extra={"event": "DUPLICATE_ORDER_REJECTED", "symbol": signal.symbol},
            )
            return {
                "client_order_id": client_order_id,
                "status": OrderStatus.REJECTED,
                "rejection_reasons": [
                    f"Duplicate order protection: A recent {signal.direction} order for {signal.symbol} was already placed within {settings.IDEMPOTENCY_WINDOW_SECONDS}s."
                ],
                "order": None,
            }

        # 3. Market Data Freshness Check
        is_fresh, age, _ = mt5_client.is_tick_fresh(signal.symbol)
        if not is_fresh:
            logger.warning(
                f"Order {client_order_id} rejected: Market tick for {signal.symbol} is stale ({age}s > {settings.MAX_TICK_AGE_SECONDS}s)",
                extra={"event": "STALE_TICK_REJECTED", "symbol": signal.symbol, "age": age},
            )
            return {
                "client_order_id": client_order_id,
                "status": OrderStatus.REJECTED,
                "rejection_reasons": [f"Market tick for {signal.symbol} is stale ({age}s > {settings.MAX_TICK_AGE_SECONDS}s)."],
                "order": None,
            }

        # 4. Fetch live market price & account info
        prices = mt5_client.get_symbol_price(signal.symbol)
        account = mt5_client.get_account_info()
        current_price = prices["ask"] if signal.direction.upper() == "BUY" else prices["bid"]
        if current_price <= 0:
            current_price = signal.suggested_entry

        # 5. Construct Risk Evaluation Request
        risk_req = RiskEvaluationRequest(
            strategy_id=signal.strategy_id,
            symbol=signal.symbol,
            side=signal.direction,
            entry_price=current_price,
            stop_loss=signal.suggested_sl,
            take_profit=signal.suggested_tp,
            account_equity=account.get("equity", 10000.0),
            account_balance=account.get("balance", 10000.0),
            current_spread_pips=prices.get("spread_pips", 1.5),
            open_positions_count=current_open_positions,
            symbol_positions_count=current_symbol_positions,
            daily_realized_loss=daily_realized_loss,
        )

        # 6. NON-BYPASSABLE RISK ENGINE GATE
        risk_result = risk_engine.evaluate_order(risk_req)

        if not risk_result.is_approved:
            logger.warning(
                f"Order {client_order_id} REJECTED by Risk Engine: {risk_result.rejection_reasons}",
                extra={"event": "ORDER_REJECTED", "symbol": signal.symbol, "reasons": risk_result.rejection_reasons},
            )
            return {
                "client_order_id": client_order_id,
                "status": OrderStatus.RISK_REJECTED,
                "rejection_reasons": risk_result.rejection_reasons,
                "order": None,
            }

        # Validate lot size ceiling in Demo mode
        lots_to_execute = risk_result.calculated_lots
        if settings.is_demo and lots_to_execute > settings.DEMO_MAX_ORDER_LOTS:
            lots_to_execute = settings.DEMO_MAX_ORDER_LOTS

        # 7. Approved by Risk Engine -> Submit to Broker via MT5 Gateway
        broker_res = mt5_client.place_order(
            symbol=signal.symbol,
            side=signal.direction,
            volume=lots_to_execute,
            price=current_price,
            sl=signal.suggested_sl,
            tp=signal.suggested_tp,
            comment=f"{signal.strategy_id[:10]}:{client_order_id[:8]}",
        )

        latency_ms = (time.perf_counter() - start_time) * 1000
        is_success = broker_res.get("success", False)
        order_status = OrderStatus.FILLED if is_success else OrderStatus.REJECTED

        if is_success:
            self._record_order_signature(signal.symbol, signal.direction, signal.strategy_id)

        # 8. Persist order audit trail in database
        order_record = None
        if self.db:
            order_record = Order(
                client_order_id=client_order_id,
                strategy_id=signal.strategy_id,
                symbol=signal.symbol,
                side=signal.direction,
                order_type="MARKET",
                quantity=lots_to_execute,
                price=current_price,
                sl=signal.suggested_sl,
                tp=signal.suggested_tp,
                status=order_status,
                risk_evaluation_json=str(risk_result.metrics_snapshot),
                broker_ticket=broker_res.get("ticket"),
                broker_response=broker_res.get("message") or broker_res.get("error") or broker_res.get("broker_comment"),
                execution_latency_ms=round(latency_ms, 2),
            )
            self.db.add(order_record)
            await self.db.commit()

        return {
            "client_order_id": client_order_id,
            "status": order_status,
            "quantity": lots_to_execute,
            "price": broker_res.get("price", current_price),
            "broker_ticket": broker_res.get("ticket"),
            "retcode": broker_res.get("retcode"),
            "latency_ms": round(latency_ms, 2),
            "broker_response": broker_res,
        }

    async def reconcile_positions(self) -> Dict[str, Any]:
        """
        Reconcile MT5 broker open positions with internally tracked records.
        Detects unmanaged positions, closed positions, and margin usage.
        """
        broker_positions = mt5_client.get_open_positions()
        broker_tickets = {p["ticket"]: p for p in broker_positions}

        db_positions = []
        if self.db:
            stmt = select(Position)
            res = await self.db.execute(stmt)
            db_positions = list(res.scalars().all())

        db_tickets = {p.ticket: p for p in db_positions}

        # Determine discrepancies
        untracked_in_db = [t for t in broker_tickets if t not in db_tickets]
        missing_at_broker = [t for t in db_tickets if t not in broker_tickets]

        status = "IN_SYNC" if not untracked_in_db and not missing_at_broker else "DISCREPANCY_DETECTED"
        logger.info(
            f"Position reconciliation: Status={status}, BrokerPositions={len(broker_positions)}, DBPositions={len(db_positions)}",
            extra={"event": "POSITION_RECONCILIATION", "status": status},
        )

        return {
            "status": status,
            "broker_positions_count": len(broker_positions),
            "db_positions_count": len(db_positions),
            "broker_positions": broker_positions,
            "untracked_in_db": untracked_in_db,
            "missing_at_broker": missing_at_broker,
            "reconciliation_time": datetime.now(timezone.utc).isoformat(),
        }


execution_agent = ExecutionAgent()
