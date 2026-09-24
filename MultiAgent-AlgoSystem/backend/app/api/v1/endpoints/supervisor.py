"""Background Supervisor API Endpoints."""
from fastapi import APIRouter
from backend.app.ai_agent.background_supervisor import ai_supervisor

router = APIRouter(prefix="/supervisor", tags=["Supervisor & Autonomous Runtime"])


@router.get("/status")
def get_supervisor_status():
    """Retrieve autonomous background supervisor health, metrics, and runtime telemetry."""
    return ai_supervisor.get_status()
