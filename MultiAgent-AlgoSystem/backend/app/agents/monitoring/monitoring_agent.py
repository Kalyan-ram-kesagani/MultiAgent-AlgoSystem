"""Agent #9 — Monitoring Agent: Telemetry, Spread Watchdog, Latency, and Kill Switch Triggers."""
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.risk.risk_engine import risk_engine
from backend.app.core.config import settings
from backend.app.core.constants import AlertLevel
from backend.app.core.logging import logger
from backend.app.models.system import SystemEvent
from trading.execution.mt5_client import mt5_client


class MonitoringAgent:
    """Continuously observes system state, MT5 link health, execution latency, and spread anomalies."""

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session
        self.alerts: List[Dict[str, Any]] = []

    async def check_database_health(self) -> bool:
        if not self.db:
            return True
        try:
            await self.db.execute(text("SELECT 1"))
            return True
        except Exception as e:
            await self.emit_alert(
                level=AlertLevel.CRITICAL,
                component="DATABASE",
                event_type="DB_CONNECTION_FAILED",
                message=f"Database unreachable: {str(e)}",
            )
            return False

    async def check_mt5_health(self) -> Dict[str, Any]:
        """Verify MT5 gateway connectivity and latency with proactive IPC check."""
        t0 = time.perf_counter()
        term_status = mt5_client.get_realtime_terminal_status()
        is_simulation = mt5_client.is_simulation_mode
        connected = bool(term_status.get("terminal_connected", False)) if not is_simulation else False
        account = mt5_client.get_account_info()
        latency_ms = term_status.get("ping_ms") or round((time.perf_counter() - t0) * 1000, 2)

        # In DEMO or LIVE mode: Disconnection triggers immediate critical alert & fail-closed kill switch
        if (settings.is_demo or settings.is_live) and not is_simulation and not connected:
            await self.emit_alert(
                level=AlertLevel.CRITICAL,
                component="MT5_GATEWAY",
                event_type="MT5_DISCONNECTED",
                message="MT5 connection lost or disconnected from broker. Auto kill switch activated.",
                details={"terminal_status": term_status},
            )
            if settings.AUTO_KILL_ON_MT5_DISCONNECT:
                risk_engine.engage_kill_switch("Automatic trigger: MT5 terminal disconnected", operator="MONITORING_AGENT")

        return {
            "connected": connected,
            "is_simulation": is_simulation,
            "gateway_mode": "SIMULATION" if is_simulation else ("DEMO" if settings.is_demo else "LIVE"),
            "latency_ms": latency_ms,
            "account_login": account.get("login"),
            "server": account.get("server"),
            "equity": account.get("equity"),
            "trade_allowed": account.get("trade_allowed", False),
        }

    async def check_spread(self, symbol: str) -> Dict[str, Any]:
        """Check for abnormal spread spikes exceeding thresholds."""
        prices = mt5_client.get_symbol_price(symbol)
        spread = prices.get("spread_pips", 0.0)

        if spread > settings.MAX_ALLOWED_SPREAD_PIPS:
            msg = f"{symbol} spread abnormal ({spread:.1f} > {settings.MAX_ALLOWED_SPREAD_PIPS:.1f} pips). Trading restricted."
            await self.emit_alert(
                level=AlertLevel.CRITICAL,
                component="MARKET_WATCHDOG",
                event_type="SPREAD_ABNORMAL",
                message=msg,
                details={"symbol": symbol, "spread_pips": spread},
            )
            return {"status": "ABNORMAL", "spread_pips": spread}

        return {"status": "NORMAL", "spread_pips": spread}

    async def check_tick_freshness(self, symbol: str) -> Dict[str, Any]:
        """Check if market ticks for symbol are arriving within acceptable latency."""
        is_fresh, age, _ = mt5_client.is_tick_fresh(symbol)
        if not is_fresh:
            msg = f"{symbol} tick feed is stale ({age}s > {settings.MAX_TICK_AGE_SECONDS}s). Halting new signals."
            await self.emit_alert(
                level=AlertLevel.CRITICAL,
                component="MARKET_WATCHDOG",
                event_type="TICK_STALE",
                message=msg,
                details={"symbol": symbol, "age_seconds": age},
            )
            return {"status": "STALE", "age_seconds": age}
        return {"status": "FRESH", "age_seconds": age}

    async def emit_alert(
        self,
        level: str,
        component: str,
        event_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create structured system alert and log event."""
        alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "component": component,
            "event_type": event_type,
            "message": message,
            "details": details,
        }
        self.alerts.append(alert)

        logger.warning(
            f"[{level}] [{component}] {message}",
            extra={"level": level, "component": component, "event": event_type, "details": details},
        )

        if self.db:
            import json
            evt = SystemEvent(
                timestamp=datetime.now(timezone.utc),
                level=level,
                component=component,
                event_type=event_type,
                message=message,
                details_json=json.dumps(details) if details else None,
            )
            self.db.add(evt)
            await self.db.commit()


monitoring_agent = MonitoringAgent()
