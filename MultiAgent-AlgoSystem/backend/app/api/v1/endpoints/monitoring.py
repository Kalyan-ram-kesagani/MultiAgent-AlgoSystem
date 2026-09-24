"""System Monitoring and Health API endpoints."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.monitoring.monitoring_agent import monitoring_agent
from backend.app.agents.risk.risk_engine import risk_engine
from backend.app.core.config import settings
from backend.app.database.session import get_db
from backend.app.schemas.system import SystemStatusResponse

router = APIRouter(prefix="/monitoring", tags=["Monitoring & Health"])


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(db: AsyncSession = Depends(get_db)):
    """System-wide operational telemetry and health status."""
    db_ok = await monitoring_agent.check_database_health()
    mt5_info = await monitoring_agent.check_mt5_health()

    return SystemStatusResponse(
        environment=settings.ENVIRONMENT,
        status="OPERATIONAL" if not risk_engine.kill_switch_active else "EMERGENCY_STOPPED",
        api_online=True,
        database_connected=db_ok,
        mt5_connected=mt5_info.get("connected", False),
        is_simulation=mt5_info.get("is_simulation", True),
        gateway_mode=mt5_info.get("gateway_mode", "SIMULATION"),
        kill_switch_active=risk_engine.kill_switch_active,
        active_strategies_count=1,
        open_positions_count=0,
        daily_pnl=0.0,
        total_equity=mt5_info.get("equity") or 10000.0,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/alerts")
def get_recent_alerts():
    """Retrieve active system alerts."""
    return monitoring_agent.alerts[-20:]
