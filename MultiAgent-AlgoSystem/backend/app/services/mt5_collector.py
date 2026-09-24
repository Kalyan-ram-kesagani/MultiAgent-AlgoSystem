"""Continuous MT5 Monitoring and Telemetry Collector Service.

Runs a background collector polling MT5 at safe intervals (every 2s).
Detects:
- NEW_DEAL
- POSITION_OPENED
- POSITION_CLOSED
- POSITION_MODIFIED
- ACCOUNT_CHANGED
- MT5_CONNECTED
- MT5_DISCONNECTED

Persists events to Supabase PostgreSQL and publishes to the Agent Runtime Event Bus.
"""
import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Set
from sqlalchemy import select, delete

from backend.app.agents.runtime.event_bus import event_bus
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.trading import Position
from trading.execution.mt5_client import mt5_client


class MT5Collector:
    """Continuously monitors MT5 terminal state, positions, deals, and account changes."""

    def __init__(self, poll_interval_seconds: float = 2.0):
        self._poll_interval = poll_interval_seconds
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._db_session_factory: Optional[Callable] = None

        # State tracking
        self._last_connected = False
        self._known_positions: Dict[int, Dict[str, Any]] = {}
        self._known_deal_tickets: Set[int] = set()
        self._last_balance: Optional[float] = None
        self._last_equity: Optional[float] = None

    def set_session_factory(self, factory: Callable):
        self._db_session_factory = factory

    async def start(self):
        """Start the continuous background monitoring loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._collector_loop())
        logger.info("Continuous MT5 Telemetry Collector started (poll_interval=2.0s).")

    async def stop(self):
        """Stop collector background task."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Continuous MT5 Telemetry Collector stopped.")

    async def _collector_loop(self):
        """Main polling cycle."""
        # Initial seeding
        try:
            status = mt5_client.get_realtime_terminal_status()
            self._last_connected = status.get("terminal_connected", False) or status.get("is_simulation_mode", False)
            raw_deals = mt5_client.get_history_deals(days=30)
            for d in raw_deals:
                ticket = getattr(d, "ticket", 0)
                if ticket:
                    self._known_deal_tickets.add(ticket)
            
            positions = mt5_client.get_open_positions()
            for p in positions:
                t = p.get("ticket")
                if t:
                    self._known_positions[t] = p
        except Exception as e:
            logger.warning(f"Error seeding initial MT5 collector state: {e}")

        while self._running:
            try:
                await self._check_telemetry()
                await asyncio.sleep(self._poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in MT5 Collector loop: {e}")
                await asyncio.sleep(self._poll_interval)

    async def _check_telemetry(self):
        """Poll MT5 state, detect changes, and dispatch events."""
        # 1. Connection check
        status = mt5_client.get_realtime_terminal_status()
        is_conn = status.get("terminal_connected", False) or status.get("is_simulation_mode", False)

        if is_conn != self._last_connected:
            self._last_connected = is_conn
            if is_conn:
                await event_bus.publish(
                    event_type="MT5_CONNECTED",
                    component="mt5_collector",
                    message="MT5 terminal connection established and operational.",
                    level="INFO",
                    details=status,
                )
            else:
                await event_bus.publish(
                    event_type="MT5_DISCONNECTED",
                    component="mt5_collector",
                    message="MT5 terminal connection lost!",
                    level="CRITICAL",
                    details=status,
                )
                if (
                    settings.AUTO_KILL_ON_MT5_DISCONNECT
                    and not settings.is_sandbox
                    and settings.ENVIRONMENT not in ("BACKTEST", "TEST")
                ):
                    from backend.app.agents.risk.risk_engine import risk_engine
                    risk_engine.engage_kill_switch(
                        operator="MT5_COLLECTOR",
                        reason="Auto-tripped by MT5Collector: MT5 terminal connection lost",
                    )
                    await event_bus.publish(
                        event_type="KILL_SWITCH_ENGAGED",
                        component="mt5_collector",
                        message="Emergency Kill Switch auto-engaged due to MT5 disconnection",
                        level="CRITICAL",
                    )

        # 2. Account balance / equity check
        acc_info = mt5_client.get_account_info()
        curr_balance = acc_info.get("balance")
        curr_equity = acc_info.get("equity")

        if (
            self._last_balance is not None
            and (curr_balance != self._last_balance or abs((curr_equity or 0.0) - (self._last_equity or 0.0)) > 5.0)
        ):
            await event_bus.publish(
                event_type="ACCOUNT_CHANGED",
                component="mt5_collector",
                message=f"Account balance/equity updated: Balance=${curr_balance}, Equity=${curr_equity}",
                level="INFO",
                details={"balance": curr_balance, "equity": curr_equity, "prev_balance": self._last_balance},
            )
        self._last_balance = curr_balance
        self._last_equity = curr_equity

        # 3. Position tracking (Opened, Closed, Modified)
        current_positions_list = mt5_client.get_open_positions()
        current_positions_map = {p["ticket"]: p for p in current_positions_list if "ticket" in p}

        # Detect newly opened positions
        for ticket, p in current_positions_map.items():
            if ticket not in self._known_positions:
                await event_bus.publish(
                    event_type="POSITION_OPENED",
                    component="mt5_collector",
                    message=f"New position opened #{ticket}: {p.get('symbol')} {p.get('side')} {p.get('volume')} lots @ {p.get('price_open')}",
                    level="INFO",
                    details=p,
                )
            else:
                # Detect modifications (SL, TP, volume changes)
                old_p = self._known_positions[ticket]
                if (
                    old_p.get("sl") != p.get("sl")
                    or old_p.get("tp") != p.get("tp")
                    or old_p.get("volume") != p.get("volume")
                ):
                    await event_bus.publish(
                        event_type="POSITION_MODIFIED",
                        component="mt5_collector",
                        message=f"Position modified #{ticket}: SL={p.get('sl')}, TP={p.get('tp')}, Vol={p.get('volume')}",
                        level="INFO",
                        details={"ticket": ticket, "new": p, "old": old_p},
                    )

        # Detect closed positions
        for ticket, old_p in list(self._known_positions.items()):
            if ticket not in current_positions_map:
                await event_bus.publish(
                    event_type="POSITION_CLOSED",
                    component="mt5_collector",
                    message=f"Position closed #{ticket}: {old_p.get('symbol')} {old_p.get('side')} {old_p.get('volume')} lots",
                    level="INFO",
                    details=old_p,
                )
                # Position closed -> trigger trade reconciliation to capture the exit deal
                if self._db_session_factory:
                    try:
                        from backend.app.services.mt5_reconciler import mt5_reconciler
                        async with self._db_session_factory() as session:
                            await mt5_reconciler.reconcile_trades(session)
                    except Exception as e:
                        logger.warning(f"Error reconciling trades on position close: {e}")

        self._known_positions = current_positions_map

        # Update database positions table
        if self._db_session_factory:
            try:
                await self._sync_positions_to_db(current_positions_list)
            except Exception as e:
                logger.debug(f"Position DB sync notice: {e}")

        # 4. Check for newly appeared deals
        deals = mt5_client.get_history_deals(days=2)
        new_deals_found = False
        for d in deals:
            ticket = getattr(d, "ticket", 0)
            if ticket and ticket not in self._known_deal_tickets:
                self._known_deal_tickets.add(ticket)
                symbol = getattr(d, "symbol", "")
                deal_type = getattr(d, "type", -1)
                if symbol and deal_type in (0, 1):
                    new_deals_found = True
                    await event_bus.publish(
                        event_type="NEW_DEAL",
                        component="mt5_collector",
                        message=f"New MT5 Deal detected #{ticket}: {symbol} {getattr(d, 'volume', 0)} lots, PnL=${getattr(d, 'profit', 0):.2f}",
                        level="INFO",
                        details={"ticket": ticket, "symbol": symbol, "profit": getattr(d, "profit", 0)},
                    )

        if new_deals_found and self._db_session_factory:
            try:
                from backend.app.services.mt5_reconciler import mt5_reconciler
                async with self._db_session_factory() as session:
                    await mt5_reconciler.reconcile_trades(session)
            except Exception as e:
                logger.warning(f"Error running reconciler for new deals: {e}")

    async def _sync_positions_to_db(self, positions_list: list):
        """Synchronize current open positions table in database."""
        async with self._db_session_factory() as session:
            # Clear stale positions and insert current snapshot
            await session.execute(delete(Position))
            for p in positions_list:
                ticket = p.get("ticket")
                if not ticket:
                    continue
                pos_record = Position(
                    ticket=ticket,
                    strategy_id="active_mt5",
                    symbol=p.get("symbol", "UNKNOWN"),
                    side=p.get("side", "BUY"),
                    volume=float(p.get("volume", 0.0)),
                    open_price=float(p.get("price_open", 0.0)),
                    current_price=float(p.get("price_current", 0.0)),
                    sl=float(p.get("sl", 0.0)),
                    tp=float(p.get("tp", 0.0)),
                    unrealized_pnl=float(p.get("profit", 0.0)),
                    open_time=datetime.now(timezone.utc),
                )
                session.add(pos_record)
            await session.commit()


mt5_collector = MT5Collector(poll_interval_seconds=2.0)
