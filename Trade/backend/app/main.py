"""
Trading Platform — FastAPI Application

Main entry point for the backend server.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import get_settings
from app.database import init_db
from app.api.routes import router

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Starting Trading Platform backend...")
    try:
        await init_db()
        logger.info("Database tables initialized.")
    except Exception as e:
        logger.warning(f"Database initialization skipped: {e}")
    yield
    logger.info("Shutting down Trading Platform backend...")


app = FastAPI(
    title="Trading Platform API",
    description="Professional AI-ready automated trading platform backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "Trading Platform API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }
