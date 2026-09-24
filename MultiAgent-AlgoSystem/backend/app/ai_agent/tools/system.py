"""System Health, Watchdog, and Telemetry Tools for AI Agent."""
import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select

from backend.app.agents.monitoring.monitoring_agent import monitoring_agent
from backend.app.agents.risk.risk_engine import risk_engine
from backend.app.core.config import settings
from backend.app.database.session import async_session_maker
from backend.app.models.agent_state import AgentEventModel
from trading.execution.mt5_client import mt5_client


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


def get_system_health() -> str:
    """Fetch health and connectivity status of MT5 terminal, database, risk engine, and execution gateway."""
    async def _async_health():
        db_ok = await monitoring_agent.check_database_health()
        mt5_info = await monitoring_agent.check_mt5_health()
        return {
            "status": "OPERATIONAL" if (not risk_engine.kill_switch_active and db_ok) else "DEGRADED",
            "environment": settings.ENVIRONMENT,
            "trading_mode": settings.TRADING_MODE,
            "database_connected": db_ok,
            "mt5": {
                "connected": mt5_info.get("connected", False),
                "gateway_mode": mt5_info.get("gateway_mode", "SIMULATION"),
                "account": mt5_info.get("login"),
                "equity": mt5_info.get("equity"),
                "balance": mt5_info.get("balance"),
            },
            "risk_engine": {
                "kill_switch_active": risk_engine.kill_switch_active,
                "consecutive_losses": risk_engine.consecutive_losses,
            },
        }

    data = _run_async(_async_health())
    return json.dumps(data, indent=2)


def get_agent_status() -> str:
    """Get current status of the AI Trading & Research Agent."""
    from backend.app.ai_agent.runtime import agent_runtime
    return json.dumps(agent_runtime.get_status(), indent=2)


def get_kill_switch_status() -> str:
    """Check emergency circuit breaker kill switch state, reason, and operator."""
    return json.dumps({
        "kill_switch_active": risk_engine.kill_switch_active,
        "reason": risk_engine.kill_switch_reason,
        "operator": risk_engine.kill_switch_operator,
        "persistence": "DISK_AND_DB_SYNCHRONIZED",
    }, indent=2)


def get_recent_events(limit: int = 15) -> str:
    """Retrieve recent trade, risk, and system events from audit trail."""
    async def _async_events():
        async with async_session_maker() as session:
            stmt = select(AgentEventModel).order_by(AgentEventModel.timestamp.desc()).limit(max(5, min(limit, 50)))
            res = await session.execute(stmt)
            events = list(res.scalars().all())
            return [
                {
                    "event_type": e.event_type,
                    "component": e.agent_id or "system",
                    "message": e.message,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                }
                for e in events
            ]

    data = _run_async(_async_events())
    return json.dumps({"count": len(data), "events": data}, indent=2)
