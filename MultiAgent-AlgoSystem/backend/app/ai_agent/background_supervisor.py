"""Autonomous Background Supervisor for AI Trading & Research System."""
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select, text

from backend.app.ai_agent.runtime import agent_runtime
from backend.app.ai_agent.schemas import AgentRuntimeState
from backend.app.agents.performance.performance_agent import performance_agent
from backend.app.agents.risk.risk_engine import risk_engine
from backend.app.agents.runtime.event_bus import event_bus
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.session import async_session_maker
from backend.app.models.trading import Trade
from backend.app.services.mt5_reconciler import mt5_reconciler
from trading.execution.mt5_client import mt5_client


class AIBackgroundSupervisor:
    """
    Supervises background MT5 trade monitoring, periodic reconciliation into Supabase,
    performance degradation detection, autonomous research triggers, risk monitoring,
    system health watchdog, and error recovery with graceful shutdown.
    """

    def __init__(self, check_interval_seconds: float = 5.0):
        self.check_interval = check_interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._last_research_trigger: Optional[datetime] = None
        self._last_reconciliation: Optional[datetime] = None
        self.last_heartbeat: Optional[datetime] = None
        self._known_positions: Dict[int, Dict[str, Any]] = {}
        self._peak_equity: float = 0.0
        self._current_drawdown_pct: float = 0.0
        self._db_healthy: bool = True
        self._events_detected_count: int = 0
        self._trades_reconciled_count: int = 0
        self._errors_recovered_count: int = 0
        self._last_event: Optional[Dict[str, Any]] = None

    @property
    def is_running(self) -> bool:
        return self._running

    def get_status(self) -> Dict[str, Any]:
        """Telemetry snapshot of supervisor state."""
        state_val = agent_runtime.current_state.value if hasattr(agent_runtime.current_state, "value") else str(agent_runtime.current_state)
        return {
            "running": self._running,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "ai_runtime_state": state_val,
            "mt5_connected": bool(mt5_client.connected or mt5_client.is_simulation_mode),
            "db_healthy": self._db_healthy,
            "kill_switch_active": risk_engine.kill_switch_active,
            "peak_equity": self._peak_equity,
            "current_drawdown_pct": round(self._current_drawdown_pct, 2),
            "open_positions_count": len(self._known_positions),
            "events_detected_count": self._events_detected_count,
            "trades_reconciled_count": self._trades_reconciled_count,
            "errors_recovered_count": self._errors_recovered_count,
            "last_reconciliation": self._last_reconciliation.isoformat() if self._last_reconciliation else None,
            "last_event": self._last_event,
        }

    def _record_event(self, event_type: str, message: str, details: Optional[Dict[str, Any]] = None):
        self._last_event = {
            "event_type": event_type,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        }

    async def start(self):
        """Start background supervision loop."""
        if self._running:
            return
        self._running = True
        self.last_heartbeat = datetime.now(timezone.utc)
        self._task = asyncio.create_task(self._supervision_loop())
        logger.info("AI Background Supervisor started.")
        await event_bus.publish(
            event_type="SUPERVISOR_STARTED",
            component="AIBackgroundSupervisor",
            message="AI Background Supervisor started.",
            details={"check_interval": self.check_interval},
        )

    async def stop(self):
        """Stop background supervision loop cleanly."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        logger.info("AI Background Supervisor stopped.")
        await event_bus.publish(
            event_type="SUPERVISOR_STOPPED",
            component="AIBackgroundSupervisor",
            message="AI Background Supervisor stopped gracefully.",
            details={"timestamp": datetime.now(timezone.utc).isoformat()},
        )

    async def _supervision_loop(self):
        """Continuous background execution loop with error recovery."""
        iteration = 0
        while self._running:
            try:
                iteration += 1
                now = datetime.now(timezone.utc)
                self.last_heartbeat = now
                agent_runtime.last_heartbeat = now

                # 1. MT5 Connectivity Check
                await self._check_mt5_connectivity()

                # 2. MT5 Position Monitoring & New/Closed Trade Detection
                await self._monitor_positions_and_trades()

                # 3. Portfolio Drawdown & Risk Limit Watchdog
                await self._check_drawdown_and_risk_limits()

                # 4. Supabase Database Health Check (every 3 iterations)
                if iteration % 3 == 0:
                    await self._check_database_health()

                # 5. AI Runtime Health and Error Recovery
                await self._check_ai_runtime_health()

                # 6. Periodic Performance Degradation Check (every 10 iterations)
                if iteration % 10 == 0:
                    await self._evaluate_performance_degradation()

                # 7. Publish Heartbeat (every 2 iterations)
                if iteration % 2 == 0:
                    await event_bus.publish(
                        event_type="SUPERVISOR_HEARTBEAT",
                        component="AIBackgroundSupervisor",
                        message="Supervisor heartbeat ok.",
                        details=self.get_status(),
                    )

                await asyncio.sleep(self.check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._errors_recovered_count += 1
                logger.error(f"Error in AI Background Supervisor loop (recovered): {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)

    async def _check_mt5_connectivity(self):
        """Monitor MT5 connection; emit event and trip kill switch if disconnected."""
        try:
            if not mt5_client.connected and not mt5_client.is_simulation_mode:
                self._record_event("MT5_DISCONNECTED", "MT5 broker terminal connection lost.")
                await event_bus.publish(
                    event_type="MT5_DISCONNECTED",
                    component="AIBackgroundSupervisor",
                    message="MT5 broker connection lost.",
                    details={"time": datetime.now(timezone.utc).isoformat()},
                )
                if settings.AUTO_KILL_ON_MT5_DISCONNECT and not risk_engine.kill_switch_active:
                    risk_engine.engage_kill_switch(
                        "MT5 broker terminal connection lost.",
                        operator="AIBackgroundSupervisor_Watchdog",
                    )
        except Exception as e:
            self._errors_recovered_count += 1
            logger.warning(f"Error checking MT5 connectivity: {e}")

    async def _monitor_positions_and_trades(self):
        """Detect new open positions and closed trades from MT5 broker telemetry."""
        try:
            current_positions = mt5_client.get_open_positions()
            current_by_ticket = {p["ticket"]: p for p in current_positions if "ticket" in p}

            # A. Detect New Trade
            for ticket, pos in current_by_ticket.items():
                if ticket not in self._known_positions:
                    self._events_detected_count += 1
                    msg = f"New position detected #{ticket}: {pos.get('symbol')} {pos.get('side')} {pos.get('volume')} lots"
                    self._record_event("TRADE_DETECTED", msg, {"ticket": ticket, "position": pos})
                    await event_bus.publish(
                        event_type="TRADE_DETECTED",
                        component="AIBackgroundSupervisor",
                        message=msg,
                        details={"ticket": ticket, "position": pos},
                    )

            # B. Detect Closed Trade
            closed_tickets = [t for t in self._known_positions if t not in current_by_ticket]
            if closed_tickets:
                for t in closed_tickets:
                    self._events_detected_count += 1
                    msg = f"Closed position detected #{t}"
                    self._record_event("TRADE_CLOSED", msg, {"ticket": t})
                    await event_bus.publish(
                        event_type="TRADE_CLOSED",
                        component="AIBackgroundSupervisor",
                        message=msg,
                        details={"ticket": t},
                    )

                # Reconcile closed trades immediately into Supabase
                async with async_session_maker() as session:
                    reconcile_res = await mt5_reconciler.reconcile_trades(session)
                    self._last_reconciliation = datetime.now(timezone.utc)
                    imported = reconcile_res.get("imported_records", 0)
                    self._trades_reconciled_count += imported
                    if imported > 0:
                        logger.info(f"Supervisor reconciled {imported} closed trades into database.")

            self._known_positions = current_by_ticket
        except Exception as e:
            self._errors_recovered_count += 1
            logger.warning(f"Error monitoring MT5 positions and trades: {e}")

    async def _check_drawdown_and_risk_limits(self):
        """Monitor portfolio equity, drawdown percentage, and enforce kill switch on breach."""
        try:
            acc = mt5_client.get_account_info()
            if not acc or "equity" not in acc:
                return

            equity = float(acc.get("equity", 0.0))
            if equity > self._peak_equity:
                self._peak_equity = equity

            if self._peak_equity > 0.0:
                dd_pct = max(0.0, ((self._peak_equity - equity) / self._peak_equity) * 100.0)
            else:
                dd_pct = 0.0

            # Detect meaningful drawdown increase (> 1% change)
            if dd_pct > (self._current_drawdown_pct + 1.0) and dd_pct >= 2.0:
                msg = f"Drawdown increase detected: {dd_pct:.2f}% (Peak: ${self._peak_equity:,.2f}, Equity: ${equity:,.2f})"
                self._record_event("DRAWDOWN_INCREASED", msg, {"drawdown_pct": dd_pct, "equity": equity})
                await event_bus.publish(
                    event_type="DRAWDOWN_INCREASED",
                    component="AIBackgroundSupervisor",
                    message=msg,
                    details={"drawdown_pct": dd_pct, "peak_equity": self._peak_equity, "equity": equity},
                )

            self._current_drawdown_pct = dd_pct

            # Enforce Max Portfolio Drawdown Limit (Fail Closed)
            max_dd_threshold = settings.MAX_ACCOUNT_DRAWDOWN_PCT * 100.0
            if dd_pct >= max_dd_threshold:
                if not risk_engine.kill_switch_active:
                    risk_engine.engage_kill_switch(
                        f"Portfolio drawdown limit breached: {dd_pct:.2f}% >= {max_dd_threshold}%",
                        operator="AIBackgroundSupervisor",
                    )
                    self._record_event("RISK_VIOLATION", f"Portfolio drawdown {dd_pct:.2f}% breached limit.")
                    await event_bus.publish(
                        event_type="RISK_VIOLATION",
                        component="AIBackgroundSupervisor",
                        message=f"Drawdown breach ({dd_pct:.2f}%). Kill switch engaged.",
                        details={"drawdown_pct": dd_pct, "limit": max_dd_threshold},
                    )

            # Check Daily Loss Limit
            daily_loss_pct = (risk_engine.calculate_daily_loss_pct() if hasattr(risk_engine, "calculate_daily_loss_pct") else 0.0)
            max_daily_threshold = settings.MAX_DAILY_LOSS_PCT * 100.0 if settings.MAX_DAILY_LOSS_PCT <= 1.0 else settings.MAX_DAILY_LOSS_PCT
            if daily_loss_pct >= max_daily_threshold and daily_loss_pct > 0.0:
                if not risk_engine.kill_switch_active:
                    risk_engine.engage_kill_switch(
                        f"Daily loss limit breached: {daily_loss_pct:.2f}% >= {max_daily_threshold}%",
                        operator="AIBackgroundSupervisor",
                    )
                    self._record_event("RISK_VIOLATION", f"Daily loss {daily_loss_pct:.2f}% breached limit.")
                    await event_bus.publish(
                        event_type="RISK_VIOLATION",
                        component="AIBackgroundSupervisor",
                        message=f"Daily loss breach ({daily_loss_pct:.2f}%). Kill switch engaged.",
                        details={"daily_loss_pct": daily_loss_pct, "limit": max_daily_threshold},
                    )

        except Exception as e:
            self._errors_recovered_count += 1
            logger.warning(f"Error checking drawdown and risk limits: {e}")

    async def _check_database_health(self):
        """Check database / Supabase connectivity and fail closed if unavailable."""
        try:
            async with async_session_maker() as session:
                await session.execute(text("SELECT 1"))
            self._db_healthy = True
        except Exception as e:
            self._db_healthy = False
            self._errors_recovered_count += 1
            msg = f"Database health check failed: {e}"
            logger.error(msg)
            self._record_event("DATABASE_FAILURE", msg)
            await event_bus.publish(
                event_type="DATABASE_FAILURE",
                component="AIBackgroundSupervisor",
                message=msg,
                details={"error": str(e)},
            )

    async def _check_ai_runtime_health(self):
        """Monitor AI runtime state and perform safe error recovery."""
        try:
            curr_state = agent_runtime.current_state
            if curr_state == AgentRuntimeState.ERROR:
                msg = "AI Runtime entered ERROR state. Initiating supervisor recovery to IDLE."
                logger.warning(msg)
                self._record_event("AI_FAILURE", msg)
                await event_bus.publish(
                    event_type="AI_FAILURE",
                    component="AIBackgroundSupervisor",
                    message=msg,
                    details={"error": agent_runtime.last_error},
                )
                # Recover AI runtime back to safe IDLE state
                agent_runtime.update_state(AgentRuntimeState.IDLE)
        except Exception as e:
            self._errors_recovered_count += 1
            logger.warning(f"Error checking AI runtime health: {e}")

    async def _evaluate_performance_degradation(self):
        """Analyze recent trade history to detect degradation and trigger autonomous research."""
        try:
            async with async_session_maker() as session:
                stmt = select(Trade).where(Trade.origin == "SYSTEM_GENERATED").order_by(Trade.exit_time.desc()).limit(30)
                res = await session.execute(stmt)
                recent_trades = list(res.scalars().all())

                if len(recent_trades) >= 10:
                    perf = performance_agent.analyze_performance(recent_trades)
                    win_rate = perf.get("win_rate", 0.0)
                    consecutive_losses = perf.get("consecutive_losses", 0)

                    # Trigger autonomous research if consecutive losses >= 2 or win rate < 35%
                    now = datetime.now(timezone.utc)
                    can_trigger = (
                        self._last_research_trigger is None
                        or (now - self._last_research_trigger).total_seconds() > 300  # Debounce 5 mins
                    )

                    if can_trigger and (consecutive_losses >= 2 or win_rate < 35.0):
                        self._last_research_trigger = now
                        logger.warning(
                            f"Performance degradation alert (WinRate={win_rate}%, ConsecutiveLosses={consecutive_losses}). "
                            "Triggering autonomous AI research investigation."
                        )
                        self._record_event("RESEARCH_STARTED", "Autonomous research triggered by performance degradation.")
                        await event_bus.publish(
                            event_type="RESEARCH_STARTED",
                            component="AIBackgroundSupervisor",
                            message="Autonomous research triggered by performance degradation monitor.",
                            details={"win_rate": win_rate, "consecutive_losses": consecutive_losses},
                        )
                        asyncio.create_task(
                            agent_runtime.run(
                                task_name="Automated Performance Investigation",
                                user_prompt=f"Consecutive losses reached {consecutive_losses} and win rate dropped to {win_rate}%. "
                                "Analyze recent trade drawdowns, identify market regimes, and evaluate if spread or volatility is degrading performance.",
                            )
                        )
        except Exception as e:
            self._errors_recovered_count += 1
            logger.error(f"Error in degradation evaluation: {e}")


ai_supervisor = AIBackgroundSupervisor()
