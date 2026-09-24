"""Main FastAPI application for Autonomous AI Trading System."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.api_router import api_router
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.session import init_db
from trading.execution.mt5_client import mt5_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    logger.info(
        f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]",
        extra={"env": settings.ENVIRONMENT},
    )
    # Initialize database tables
    try:
        await init_db()
        logger.info("Database schema initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")

    # Connect to MT5 gateway (or simulation fallback) first so telemetry is initialized
    try:
        mt5_client.connect()
    except Exception as e:
        logger.warning(f"MT5 gateway initialization warning: {e}")

    # Initialize Agent Runtime Directory and Supervisor
    try:
        from backend.app.agents.runtime import agent_supervisor, agent_registry, event_bus
        from backend.app.database.session import async_session_maker
        event_bus.set_session_factory(async_session_maker)
        agent_registry.set_session_factory(async_session_maker)
        agent_supervisor.initialize_baseline_agents()
        await agent_supervisor.start()
        logger.info("Agent Runtime initialized with 11 baseline agents.")
    except Exception as e:
        logger.error(f"Failed to initialize Agent Runtime: {e}")

    # Startup MT5 Trade Reconciliation & Telemetry Collector
    try:
        from backend.app.database.session import async_session_maker
        from backend.app.services.mt5_reconciler import mt5_reconciler
        from backend.app.services.mt5_collector import mt5_collector

        mt5_collector.set_session_factory(async_session_maker)
        await mt5_collector.start()

        # Perform startup trade reconciliation
        async with async_session_maker() as session:
            reconcile_res = await mt5_reconciler.reconcile_trades(session)
            logger.info(
                f"Startup MT5 Trade Reconciliation: Found={reconcile_res.get('mt5_deals')}, "
                f"Imported={reconcile_res.get('imported_records')}, "
                f"Already recorded={reconcile_res.get('duplicate_records')}"
            )
    except Exception as e:
        logger.warning(f"Startup trade reconciliation notice: {e}")

    # Initialize Risk Engine DB synchronization
    try:
        from backend.app.agents.risk.risk_engine import risk_engine
        from backend.app.database.session import async_session_maker
        risk_engine.set_session_factory(async_session_maker)
        await risk_engine.sync_with_db()
        logger.info("Risk Engine dual-persistence initialized.")
    except Exception as e:
        logger.warning(f"Risk Engine DB sync warning: {e}")

    # Startup AI Background Supervisor
    try:
        from backend.app.ai_agent import ai_supervisor
        await ai_supervisor.start()
        logger.info("AI Background Supervisor started.")
    except Exception as e:
        logger.warning(f"AI Background Supervisor startup warning: {e}")

    yield

    # Shutdown hooks
    logger.info("Shutting down trading system application...")
    try:
        from backend.app.ai_agent import ai_supervisor
        await ai_supervisor.stop()
    except Exception:
        pass
    try:
        from backend.app.services.mt5_collector import mt5_collector
        await mt5_collector.stop()
    except Exception:
        pass
    try:
        from backend.app.agents.runtime import agent_supervisor
        await agent_supervisor.stop()
    except Exception:
        pass
    mt5_client.disconnect()



app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-grade, risk-controlled, AI-assisted algorithmic trading platform.",
    lifespan=lifespan,
)

# CORS Configuration for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach API Router under /api/v1
app.include_router(api_router)

# Also expose direct /api routes as required for seamless frontend integration
from fastapi import APIRouter
from backend.app.api.v1.endpoints.agents import router as direct_agents_router
from backend.app.api.v1.endpoints.system_reconciliation import router as direct_reconcile_router
from backend.app.api.v1.endpoints.research_pipeline import router as direct_research_router
from backend.app.api.v1.endpoints.ai_agent import router as direct_ai_router
from backend.app.api.v1.endpoints.risk import router as direct_risk_router
from backend.app.api.v1.endpoints.supervisor import router as direct_supervisor_router

direct_api = APIRouter(prefix="/api")
direct_api.include_router(direct_agents_router)
direct_api.include_router(direct_reconcile_router)
direct_api.include_router(direct_research_router)
direct_api.include_router(direct_ai_router)
direct_api.include_router(direct_risk_router)
direct_api.include_router(direct_supervisor_router)
app.include_router(direct_api)


@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "OPERATIONAL",
    }


@app.get("/health")
def health():
    return {"status": "HEALTHY", "timestamp": "OK"}
