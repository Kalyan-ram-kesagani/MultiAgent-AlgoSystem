"""Agent #10 — Journal Agent: Trade Recording, R-Multiple Auditing, and Execution Metrics."""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.logging import logger
from backend.app.models.trading import Trade
from backend.app.schemas.trading import TradeResponse


class JournalAgent:
    """Automatically records, audits, and journals every closed trade."""

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session

    @staticmethod
    def identify_session(entry_time: datetime) -> str:
        """Determine trading session based on UTC hour."""
        hour = entry_time.hour
        if 0 <= hour < 7:
            return "ASIAN"
        elif 7 <= hour < 12:
            return "LONDON"
        elif 12 <= hour < 16:
            return "LONDON_NY_OVERLAP"
        elif 16 <= hour < 21:
            return "NEW_YORK"
        else:
            return "LATE_US"

    async def record_closed_trade(
        self,
        strategy_id: str,
        symbol: str,
        direction: str,
        entry_time: datetime,
        exit_time: datetime,
        entry_price: float,
        stop_price: float,
        target_price: float,
        exit_price: float,
        quantity: float,
        commission: float = 7.0,
        swap: float = 0.0,
        model_id: Optional[str] = None,
        market_regime: Optional[str] = None,
        exit_reason: str = "TP",
    ) -> Trade:
        """Calculate PnL, R-multiple, MFE, MAE and persist trade journal record."""
        trade_id = f"TRD-{uuid.uuid4().hex[:8].upper()}"

        contract_size = 100.0 if "XAU" in symbol.upper() else 100000.0
        price_diff = (exit_price - entry_price) if direction == "BUY" else (entry_price - exit_price)
        gross_pnl = price_diff * contract_size * quantity
        net_pnl = gross_pnl - commission - swap

        risk_distance = abs(entry_price - stop_price)
        risk_dollars = risk_distance * contract_size * quantity
        r_multiple = net_pnl / (risk_dollars + 1e-9)

        duration = int((exit_time - entry_time).total_seconds())
        session = self.identify_session(entry_time)

        # Estimate MFE / MAE conservatively
        mfe = abs(target_price - entry_price) if net_pnl > 0 else 0.0
        mae = risk_distance if net_pnl < 0 else 0.0

        trade_record = Trade(
            trade_id=trade_id,
            strategy_id=strategy_id,
            model_id=model_id,
            symbol=symbol,
            direction=direction,
            entry_time=entry_time,
            exit_time=exit_time,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            exit_price=exit_price,
            quantity=quantity,
            commission=commission,
            swap=swap,
            pnl=round(net_pnl, 2),
            r_multiple=round(r_multiple, 2),
            mfe=round(mfe, 5),
            mae=round(mae, 5),
            duration_seconds=duration,
            session=session,
            market_regime=market_regime,
            exit_reason=exit_reason,
        )

        if self.db:
            self.db.add(trade_record)
            await self.db.commit()

        logger.info(
            f"Journaled trade {trade_id}: {symbol} {direction} PnL=${net_pnl:.2f} ({r_multiple:.2f}R)",
            extra={"event": "TRADE_JOURNALED", "trade_id": trade_id, "pnl": net_pnl, "r": r_multiple},
        )

        return trade_record

    async def get_trades(
        self,
        symbol: Optional[str] = None,
        strategy_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Trade]:
        if not self.db:
            return []
        stmt = select(Trade).order_by(Trade.exit_time.desc()).limit(limit)
        if symbol:
            stmt = stmt.where(Trade.symbol == symbol)
        if strategy_id:
            stmt = stmt.where(Trade.strategy_id == strategy_id)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
