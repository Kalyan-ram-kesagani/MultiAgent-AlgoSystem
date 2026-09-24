"""Pytest configuration and global test fixtures."""
import asyncio
import os
import pytest
from httpx import ASGITransport, AsyncClient

# Set environment variables for testing
os.environ["ENVIRONMENT"] = "BACKTEST"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from backend.app.database.session import init_db
from backend.app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def prepare_database():
    """Ensure in-memory database tables exist and kill switch is disengaged for tests."""
    from backend.app.agents.risk.risk_engine import risk_engine
    from trading.execution.mt5_client import mt5_client
    mt5_client.is_simulation_mode = True
    risk_engine.disengage_kill_switch(operator="TEST_FIXTURE")
    await init_db()
