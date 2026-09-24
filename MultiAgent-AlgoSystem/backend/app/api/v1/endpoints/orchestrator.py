"""Orchestrator Agent API endpoints."""
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.orchestrator.orchestrator_agent import OrchestratorAgent
from backend.app.database.session import get_db

router = APIRouter(prefix="/orchestrator", tags=["Orchestrator"])


@router.post("/task")
async def dispatch_task(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """Dispatch workflow task through Orchestrator."""
    agent = OrchestratorAgent(db_session=db)
    task_name = payload.get("task", "investigate_performance")
    result = await agent.execute_task(task_name, payload)
    return result


@router.post("/validate-deployment")
async def validate_deployment(payload: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    """Run verification of deployment gates before strategy promotion."""
    agent = OrchestratorAgent(db_session=db)
    return await agent.execute_task("run_full_validation_pipeline", payload)
