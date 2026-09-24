"""API v1 router aggregator."""
from fastapi import APIRouter

from backend.app.api.v1.endpoints.backtest import router as backtest_router
from backend.app.api.v1.endpoints.execution import router as execution_router
from backend.app.api.v1.endpoints.journal import router as journal_router
from backend.app.api.v1.endpoints.market_data import router as data_router
from backend.app.api.v1.endpoints.ml import router as ml_router
from backend.app.api.v1.endpoints.monitoring import router as monitoring_router
from backend.app.api.v1.endpoints.orchestrator import router as orchestrator_router
from backend.app.api.v1.endpoints.risk import router as risk_router
from backend.app.api.v1.endpoints.strategies import router as strategies_router

from backend.app.api.v1.endpoints.agents import router as agents_router, events_router
from backend.app.api.v1.endpoints.research import router as research_router
from backend.app.api.v1.endpoints.system_reconciliation import router as reconciliation_router
from backend.app.api.v1.endpoints.research_pipeline import router as research_pipeline_router
from backend.app.api.v1.endpoints.ai_agent import router as ai_agent_router
from backend.app.api.v1.endpoints.supervisor import router as supervisor_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(monitoring_router)
api_router.include_router(risk_router)
api_router.include_router(strategies_router)
api_router.include_router(backtest_router)
api_router.include_router(execution_router)
api_router.include_router(data_router)
api_router.include_router(journal_router)
api_router.include_router(ml_router)
api_router.include_router(orchestrator_router)
api_router.include_router(agents_router)
api_router.include_router(events_router)
api_router.include_router(research_router)
api_router.include_router(reconciliation_router)
api_router.include_router(research_pipeline_router)
api_router.include_router(ai_agent_router)
api_router.include_router(supervisor_router)


