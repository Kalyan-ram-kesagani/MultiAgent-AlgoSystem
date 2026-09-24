import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.risk import RiskEvaluationRequest, RiskEvaluationResult

STATE_FILE = Path(__file__).resolve().parents[4] / ".kill_switch_state.json"


class RiskEngine:
    """
    Independent Risk Engine enforcing hard safety rules and sizing.
    NO order may be sent to MT5 without approval from this engine.
    State persists durably across application restarts.
    """

    def __init__(self, state_file: Optional[Path] = None):
        self.state_file = state_file or STATE_FILE
        self.kill_switch_active: bool = settings.EMERGENCY_KILL_SWITCH_ACTIVE
        self.kill_switch_reason: Optional[str] = None
        self.kill_switch_operator: Optional[str] = None
        self.consecutive_losses: int = 0
        self.peak_equity: float = 0.0

        self._session_factory = None
        # Load persisted kill switch state if present
        self._load_persisted_state()

    def set_session_factory(self, session_factory) -> None:
        """Attach database session factory for dual-persistence across PostgreSQL/Supabase and disk."""
        self._session_factory = session_factory

    def _load_persisted_state(self) -> None:
        """Load durable kill switch state from disk."""
        try:
            if self.state_file.exists():
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("kill_switch_active"):
                        self.kill_switch_active = True
                        self.kill_switch_reason = data.get("reason", "Restored from persistent state")
                        self.kill_switch_operator = data.get("operator", "PERSISTENT_STORE")
                        logger.warning(
                            f"Restored PERSISTENT KILL SWITCH STATE: {self.kill_switch_reason}",
                            extra={"event": "KILL_SWITCH_RESTORED", "reason": self.kill_switch_reason},
                        )
        except Exception as e:
            logger.error(f"Failed to read kill switch state file: {e}")

    def _persist_state(self) -> None:
        """Atomically persist durable kill switch state to disk and database."""
        try:
            payload = {
                "kill_switch_active": self.kill_switch_active,
                "reason": self.kill_switch_reason,
                "operator": self.kill_switch_operator,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            tmp_file = self.state_file.with_suffix(".tmp")
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            tmp_file.replace(self.state_file)
        except Exception as e:
            logger.error(f"Failed to persist kill switch state to {self.state_file}: {e}")

        # Sync to database asynchronously if factory is set
        if self._session_factory:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._persist_db_state())
            except Exception:
                pass

    async def _persist_db_state(self) -> None:
        """Persist state to database KillSwitchStateModel table."""
        if not self._session_factory:
            return
        try:
            from backend.app.models.ai_audit import KillSwitchStateModel
            async with self._session_factory() as session:
                record = KillSwitchStateModel(
                    is_active=self.kill_switch_active,
                    reason=self.kill_switch_reason,
                    operator=self.kill_switch_operator,
                    activated_at=datetime.now(timezone.utc) if self.kill_switch_active else None,
                    deactivated_at=datetime.now(timezone.utc) if not self.kill_switch_active else None,
                )
                session.add(record)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to sync kill switch state to DB: {e}")

    async def sync_with_db(self, session=None) -> None:
        """Fail-closed dual-persistence sync: If either DB or disk has active kill switch, engage."""
        try:
            from backend.app.models.ai_audit import KillSwitchStateModel
            from sqlalchemy import select

            async def _do_sync(sess):
                stmt = select(KillSwitchStateModel).order_by(KillSwitchStateModel.created_at.desc()).limit(1)
                res = await sess.execute(stmt)
                latest = res.scalar_one_or_none()
                if latest and latest.is_active:
                    self.kill_switch_active = True
                    self.kill_switch_reason = latest.reason or "Restored from database state"
                    self.kill_switch_operator = latest.operator or "DATABASE_SYNC"
                    self._persist_state()
                elif self.kill_switch_active:
                    # Sync disk state to DB
                    await self._persist_db_state()

            if session:
                await _do_sync(session)
            elif self._session_factory:
                async with self._session_factory() as sess:
                    await _do_sync(sess)
        except Exception as e:
            logger.warning(f"Could not complete DB kill switch sync (relying on disk): {e}")

    def engage_kill_switch(self, reason: str, operator: str = "SYSTEM") -> None:
        """Immediately trigger emergency kill switch halting all new trade placements."""
        self.kill_switch_active = True
        self.kill_switch_reason = f"Engaged by {operator}: {reason}"
        self.kill_switch_operator = operator
        self._persist_state()
        logger.critical(
            f"EMERGENCY KILL SWITCH ENGAGED: {self.kill_switch_reason}",
            extra={"event": "KILL_SWITCH_ENGAGED", "reason": reason, "operator": operator},
        )
        try:
            from backend.app.agents.runtime import agent_registry
            agent_registry.heartbeat("agent_risk")
        except Exception:
            pass

    def disengage_kill_switch(self, operator: str = "OPERATOR") -> None:
        """Reset emergency kill switch (requires explicit manual intervention)."""
        self.kill_switch_active = False
        self.kill_switch_reason = None
        self.kill_switch_operator = operator
        self._persist_state()
        logger.info(
            f"Emergency kill switch disengaged by {operator}",
            extra={"event": "KILL_SWITCH_DISENGAGED", "operator": operator},
        )
        try:
            from backend.app.agents.runtime import agent_registry
            agent_registry.heartbeat("agent_risk")
        except Exception:
            pass


    def record_trade_outcome(self, pnl: float) -> None:
        """Update consecutive loss counter for circuit breaker."""
        if pnl < 0:
            self.consecutive_losses += 1
            if self.consecutive_losses >= settings.CONSECUTIVE_LOSS_LIMIT:
                self.engage_kill_switch(
                    f"Consecutive loss limit ({settings.CONSECUTIVE_LOSS_LIMIT}) breached.",
                    operator="AUTOMATIC_CIRCUIT_BREAKER",
                )
        else:
            self.consecutive_losses = 0

    def evaluate_order(self, req: RiskEvaluationRequest) -> RiskEvaluationResult:
        """
        Validate incoming order proposal against all safety checks and determine position size.
        """
        rejection_reasons: List[str] = []

        # 0. Check Trading Mode: LIVE trading is strictly prohibited across all phases.
        if settings.is_live or settings.TRADING_MODE.upper() == "LIVE":
            rejection_reasons.append("Trading mode violation: LIVE trading is prohibited. System runs in DEMO/SANDBOX mode only.")

        # 1. Check Hard Kill Switch (fail closed if checking state fails)
        try:
            from backend.app.agents.runtime import agent_registry
            agent_registry.heartbeat("agent_risk")
        except Exception:
            pass

        try:
            if self.kill_switch_active:
                rejection_reasons.append(f"Emergency kill switch is ACTIVE ({self.kill_switch_reason})")
        except Exception as e:
            rejection_reasons.append(f"Kill switch state check failed (fail-closed): {e}")

        # 2. Check Symbol validity
        clean_sym = (req.symbol or "").strip().upper()
        if not clean_sym or len(clean_sym) < 3 or not clean_sym.replace("/", "").isalnum():
            rejection_reasons.append(f"Invalid symbol '{req.symbol}'. Symbol must be a valid currency or asset identifier.")

        # 3. Check Strategy Permission
        clean_strat = (req.strategy_id or "").strip()
        if not clean_strat:
            rejection_reasons.append("Strategy permission denied: Strategy ID must not be empty.")

        # 4. Check Account Balance / Equity validity
        if req.account_equity is None or req.account_balance is None or req.account_equity <= 0 or req.account_balance <= 0:
            rejection_reasons.append(f"Account state invalid or unavailable (Equity: {req.account_equity}, Balance: {req.account_balance})")
            return RiskEvaluationResult(
                is_approved=False,
                calculated_lots=0.0,
                rejection_reasons=rejection_reasons,
                risk_amount_dollars=0.0,
                risk_percentage=0.0,
                stop_distance_points=0.0,
            )

        # Update peak equity tracking
        if req.account_equity > self.peak_equity:
            self.peak_equity = req.account_equity

        # 5. Check Maximum Account Drawdown limit
        current_drawdown = (self.peak_equity - req.account_equity) / (self.peak_equity + 1e-9)
        if current_drawdown >= settings.MAX_ACCOUNT_DRAWDOWN_PCT:
            msg = f"Maximum drawdown threshold reached ({current_drawdown*100:.2f}% >= {settings.MAX_ACCOUNT_DRAWDOWN_PCT*100:.1f}%)"
            rejection_reasons.append(msg)
            self.engage_kill_switch(msg, operator="AUTO_DRAWDOWN_BREAKER")

        # 6. Check Daily Loss Limit (realized + unrealized)
        total_daily_loss = req.daily_realized_loss + min(0.0, req.daily_unrealized_loss)
        daily_loss_pct = abs(min(0.0, total_daily_loss)) / req.account_equity
        if daily_loss_pct >= settings.MAX_DAILY_LOSS_PCT:
            rejection_reasons.append(
                f"Daily loss limit breached ({daily_loss_pct*100:.2f}% >= {settings.MAX_DAILY_LOSS_PCT*100:.1f}%)"
            )

        # 7. Check Maximum Open Positions limit
        if req.open_positions_count >= settings.MAX_OPEN_POSITIONS:
            rejection_reasons.append(
                f"Maximum open positions limit reached ({req.open_positions_count} >= {settings.MAX_OPEN_POSITIONS})"
            )

        # 8. Check Maximum Symbol Exposure limit
        if req.symbol_positions_count >= settings.MAX_SYMBOL_EXPOSURE:
            rejection_reasons.append(
                f"Maximum symbol positions reached for {req.symbol} ({req.symbol_positions_count} >= {settings.MAX_SYMBOL_EXPOSURE})"
            )

        # 9. Check Spread Filter
        if req.current_spread_pips > settings.MAX_ALLOWED_SPREAD_PIPS:
            rejection_reasons.append(
                f"Spread too wide for {req.symbol} ({req.current_spread_pips:.1f} > {settings.MAX_ALLOWED_SPREAD_PIPS:.1f} pips)"
            )

        # 10. Check Stop Loss Requirement, Distance & Direction Consistency
        if req.stop_loss is None or req.stop_loss <= 0:
            rejection_reasons.append("Mandatory Stop Loss missing or non-positive. Orders without stop loss are strictly prohibited.")
        else:
            stop_dist = abs(req.entry_price - req.stop_loss)
            if stop_dist <= 0:
                rejection_reasons.append("Stop loss is equal to or invalid relative to entry price.")

            if req.side == "BUY" and req.stop_loss >= req.entry_price:
                rejection_reasons.append("BUY order stop loss must be below entry price.")
            elif req.side == "SELL" and req.stop_loss <= req.entry_price:
                rejection_reasons.append("SELL order stop loss must be above entry price.")

        # 9. Dynamic Position Sizing Calculation
        # Risk Amount = Account Equity * Risk % (e.g. 1%)
        risk_dollars = req.account_equity * settings.RISK_PER_TRADE_PCT

        # Standard FX: 1 lot = 100,000 units. For standard pairs like EURUSD, 1 pip (0.0001) = $10.
        # XAUUSD: 1 lot = 100 oz. $1 price move = $100.
        if "XAU" in req.symbol.upper():
            contract_size = 100.0
        elif "JPY" in req.symbol.upper():
            contract_size = 100000.0 / 150.0  # Approx JPY conversion
        else:
            contract_size = 100000.0

        risk_per_lot = stop_dist * contract_size
        calculated_lots = 0.0

        if risk_per_lot > 0:
            raw_lots = risk_dollars / risk_per_lot
            # Floor to standard micro-lot step (0.01) and clamp between 0.01 and 10.0 lots
            calculated_lots = round(max(0.01, min(raw_lots, 10.0)), 2)

        is_approved = len(rejection_reasons) == 0

        result = RiskEvaluationResult(
            is_approved=is_approved,
            calculated_lots=calculated_lots if is_approved else 0.0,
            rejection_reasons=rejection_reasons,
            risk_amount_dollars=round(risk_dollars, 2),
            risk_percentage=settings.RISK_PER_TRADE_PCT * 100,
            stop_distance_points=round(stop_dist, 5),
            metrics_snapshot={
                "equity": req.account_equity,
                "current_drawdown_pct": round(current_drawdown * 100, 2),
                "daily_loss_pct": round(daily_loss_pct * 100, 2),
                "open_positions": req.open_positions_count,
                "consecutive_losses": self.consecutive_losses,
                "kill_switch": self.kill_switch_active,
            },
        )

        log_level = logger.info if is_approved else logger.warning
        log_level(
            f"Risk Engine evaluation for {req.symbol} {req.side}: {'APPROVED' if is_approved else 'REJECTED'}",
            extra={
                "event": "RISK_EVALUATION",
                "symbol": req.symbol,
                "approved": is_approved,
                "reasons": rejection_reasons,
                "calculated_lots": calculated_lots,
            },
        )

        return result


risk_engine = RiskEngine()
