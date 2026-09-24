"""Tests for Supabase models, MT5 trade reconciliation, and system endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from backend.app.database.session import async_session_maker
from backend.app.main import app
from backend.app.models.agent_state import (
    AgentEventModel,
    AgentStateModel,
    AgentTaskModel,
    PerformanceSnapshot,
)
from backend.app.models.trading import Trade
from backend.app.services.mt5_reconciler import mt5_reconciler


@pytest.mark.asyncio
async def test_reconciliation_endpoint():
    """Verify GET /api/system/reconciliation returns required schema."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/system/reconciliation?trigger_now=true")
        assert response.status_code == 200
        data = response.json()
        assert "mt5_deals" in data
        assert "database_trades" in data
        assert "missing_records" in data
        assert "imported_records" in data
        assert "duplicate_records" in data
        assert "last_reconciliation_time" in data


@pytest.mark.asyncio
async def test_system_health_endpoint():
    """Verify GET /api/system/health returns consolidated telemetry."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/system/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "mt5" in data
        assert "risk_engine" in data
        assert "agent_runtime" in data
        assert data["risk_engine"]["active"] is True


@pytest.mark.asyncio
async def test_trades_and_performance_endpoints():
    """Verify GET /api/trades and GET /api/performance."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        trades_res = await ac.get("/api/trades")
        assert trades_res.status_code == 200
        assert isinstance(trades_res.json(), list)

        perf_res = await ac.get("/api/performance")
        assert perf_res.status_code == 200
        perf_data = perf_res.json()
        assert "metrics" in perf_data
        assert "account" in perf_data


@pytest.mark.asyncio
async def test_agent_endpoints():
    """Verify GET /api/agents, /api/agents/{id}/tasks, /api/agents/{id}/events."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        agents_res = await ac.get("/api/agents/")
        assert agents_res.status_code == 200
        agents = agents_res.json()
        assert len(agents) >= 11

        target_agent = agents[0]["metadata"]["agent_id"]
        tasks_res = await ac.get(f"/api/agents/{target_agent}/tasks")
        assert tasks_res.status_code == 200
        assert isinstance(tasks_res.json(), list)

        events_res = await ac.get(f"/api/agents/{target_agent}/events")
        assert events_res.status_code == 200
        assert isinstance(events_res.json(), list)
