"""System Reconciliation, Unified Endpoints, and Real-Time SSE Stream."""
import asyncio
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.journal.journal_agent import JournalAgent
from backend.app.agents.monitoring.monitoring_agent import monitoring_agent
from backend.app.agents.performance.performance_agent import performance_agent
from backend.app.agents.risk.risk_engine import risk_engine
from backend.app.agents.runtime import agent_registry, event_bus
from backend.app.core.config import settings
from backend.app.database.session import get_db
from backend.app.models.agent_state import AgentEventModel, AgentStateModel, AgentTaskModel, PerformanceSnapshot
from backend.app.models.trading import Position, Trade
from backend.app.ai_agent.background_supervisor import ai_supervisor
from backend.app.ai_agent.runtime import agent_runtime
from backend.app.services.mt5_reconciler import mt5_reconciler
from trading.execution.mt5_client import mt5_client

router = APIRouter(tags=["System Reconciliation & Real-Time API"])


@router.get("/system/reconciliation")
async def get_reconciliation_status(
    trigger_now: bool = Query(default=False, description="Whether to trigger an immediate reconciliation pass"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve broker deal reconciliation telemetry against Supabase PostgreSQL:
    - MT5 deals
    - Database trades
    - Missing records
    - Imported records
    - Duplicate records
    - Last reconciliation time
    """
    if trigger_now or mt5_reconciler.last_summary.get("last_reconciliation_time") is None:
        summary = await mt5_reconciler.reconcile_trades(db)
        return summary
    return mt5_reconciler.last_summary


@router.post("/system/reconciliation")
async def trigger_reconciliation(db: AsyncSession = Depends(get_db)):
    """Trigger an immediate trade reconciliation run."""
    summary = await mt5_reconciler.reconcile_trades(db)
    return summary


@router.get("/trades")
async def get_all_trades(
    symbol: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all reconciled and recorded trades from Supabase PostgreSQL."""
    stmt = select(Trade).order_by(Trade.exit_time.desc()).limit(limit)
    if symbol:
        stmt = stmt.where(Trade.symbol == symbol)
    res = await db.execute(stmt)
    trades = list(res.scalars().all())
    return trades


@router.get("/positions")
async def get_current_positions():
    """Retrieve all active open positions from MT5 Gateway."""
    return mt5_client.get_open_positions()


@router.get("/performance")
async def get_performance(db: AsyncSession = Depends(get_db)):
    """Retrieve statistical performance attribution and historical snapshots from Supabase."""
    # 1. Fetch trades
    stmt = select(Trade).order_by(Trade.exit_time.desc()).limit(500)
    res = await db.execute(stmt)
    trades = list(res.scalars().all())

    stats = performance_agent.analyze_performance(trades)

    # 2. Fetch latest snapshot
    snap_stmt = select(PerformanceSnapshot).order_by(PerformanceSnapshot.timestamp.desc()).limit(1)
    snap_res = await db.execute(snap_stmt)
    latest_snapshot = snap_res.scalar_one_or_none()

    acc_info = mt5_client.get_account_info()

    return {
        "metrics": stats,
        "latest_snapshot": {
            "snapshot_id": latest_snapshot.snapshot_id if latest_snapshot else None,
            "timestamp": latest_snapshot.timestamp.isoformat() if latest_snapshot and latest_snapshot.timestamp else None,
            "win_rate": latest_snapshot.win_rate if latest_snapshot else stats.get("win_rate", 0.0),
            "profit_factor": latest_snapshot.profit_factor if latest_snapshot else stats.get("profit_factor", 0.0),
            "total_pnl": latest_snapshot.total_pnl if latest_snapshot else stats.get("total_net_pnl", 0.0),
            "equity": latest_snapshot.equity if latest_snapshot else acc_info.get("equity", 10000.0),
            "balance": latest_snapshot.balance if latest_snapshot else acc_info.get("balance", 10000.0),
        } if latest_snapshot else None,
        "account": acc_info,
    }


@router.get("/system/health")
async def get_system_health():
    """Consolidated health status for MT5, Supabase Database, Risk Engine, and Multi-Agent Runtime."""
    db_ok = await monitoring_agent.check_database_health()
    mt5_info = await monitoring_agent.check_mt5_health()
    agents = agent_registry.get_all_agents()

    all_agents_healthy = all(
        a.get("state", {}).get("status") not in ("ERROR", "OFFLINE")
        for a in agents
    )

    sup_status = ai_supervisor.get_status()

    return {
        "status": "OPERATIONAL" if (not risk_engine.kill_switch_active and db_ok) else "DEGRADED",
        "environment": settings.ENVIRONMENT,
        "database": {
            "status": "CONNECTED" if db_ok else "DISCONNECTED",
            "engine": "PostgreSQL (Supabase)" if "postgresql" in settings.DATABASE_URL else "SQLite (Fallback)",
        },
        "supabase": {
            "status": "CONNECTED" if db_ok else "DISCONNECTED",
            "engine": "PostgreSQL (Supabase)" if "postgresql" in settings.DATABASE_URL else "SQLite (Fallback)",
        },
        "mt5": {
            "connected": mt5_info.get("connected", False),
            "mode": mt5_info.get("gateway_mode", "SIMULATION"),
            "account": mt5_info.get("login"),
            "server": mt5_info.get("server"),
            "trade_allowed": mt5_info.get("trade_allowed", False),
            "equity": mt5_info.get("equity"),
            "balance": mt5_info.get("balance"),
        },
        "ai_runtime": {
            "status": agent_runtime.state.value if hasattr(agent_runtime.state, "value") else str(agent_runtime.state),
            "current_task": agent_runtime.current_task,
            "current_tool": agent_runtime.current_tool,
            "model": settings.OPENAI_MODEL,
        },
        "agent_runtime": {
            "total_agents": len(agents),
            "healthy": all_agents_healthy,
            "status": agent_runtime.state.value if hasattr(agent_runtime.state, "value") else str(agent_runtime.state),
        },
        "risk_engine": {
            "active": True,
            "kill_switch_active": risk_engine.kill_switch_active,
            "circuit_breaker_tripped": (risk_engine.consecutive_losses >= settings.CONSECUTIVE_LOSS_LIMIT),
            "consecutive_losses": risk_engine.consecutive_losses,
        },
        "execution_engine": {
            "status": "OPERATIONAL" if mt5_info.get("connected") else "DEGRADED",
            "mode": "DEMO ONLY",
            "max_order_lots": settings.DEMO_MAX_ORDER_LOTS,
        },
        "backtest_engine": {
            "status": "OPERATIONAL",
            "capabilities": ["Monte Carlo 500 permutations", "Walk-Forward OOS"],
        },
        "supervisor": {
            "status": "RUNNING" if ai_supervisor.is_running else "STOPPED",
            "last_heartbeat": sup_status.get("last_heartbeat"),
            "events_detected_count": sup_status.get("events_detected_count", 0),
        },
        "kill_switch": {
            "active": risk_engine.kill_switch_active,
            "reason": risk_engine.kill_switch_reason,
            "operator": risk_engine.kill_switch_operator,
        },
        "agent_runtime_summary": {
            "total_agents": len(agents),
            "healthy": all_agents_healthy,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/stream")
async def sse_event_stream(request: Request):
    """
    Server-Sent Events (SSE) real-time stream.
    Pushes:
    - Agent status and heartbeats
    - Task updates
    - Trade detection events
    - Risk events
    - MT5 connectivity & telemetry
    """
    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)

        # Wildcard event listener
        async def on_bus_event(event):
            try:
                queue.put_nowait({
                    "type": "BUS_EVENT",
                    "event_type": event.event_type,
                    "component": event.component,
                    "message": event.message,
                    "timestamp": event.timestamp.isoformat(),
                    "details": event.details,
                })
            except asyncio.QueueFull:
                pass

        event_bus.subscribe("*", on_bus_event)

        try:
            # Send initial sync payload
            initial_payload = {
                "type": "INITIAL_SYNC",
                "agents": agent_registry.get_all_agents(),
                "account": mt5_client.get_account_info(),
                "terminal": mt5_client.get_realtime_terminal_status(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            yield f"data: {json.dumps(initial_payload, default=str)}\n\n"

            while not await request.is_disconnected():
                try:
                    # Wait up to 1 second for a bus event, otherwise send a periodic heartbeat
                    data = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(data, default=str)}\n\n"
                except asyncio.TimeoutError:
                    if await request.is_disconnected():
                        break
                    # Send periodic keepalive with current MT5 & agent state
                    hb = {
                        "type": "HEARTBEAT",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "mt5_connected": mt5_client.connected,
                        "agents": [
                            {"agent_id": aid, "status": st.get("status"), "last_heartbeat": st.get("heartbeat_timestamp")}
                            for aid, st in [(a["metadata"]["agent_id"], a["state"]) for a in agent_registry.get_all_agents()]
                        ],
                    }
                    yield f"data: {json.dumps(hb, default=str)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            event_bus.unsubscribe("*", on_bus_event)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
