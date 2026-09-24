"""Integration tests for FastAPI endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.main import app


@pytest.mark.asyncio
async def test_root_and_health_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "HEALTHY"

        res = await client.get("/")
        assert res.status_code == 200
        assert res.json()["status"] == "OPERATIONAL"


@pytest.mark.asyncio
async def test_strategies_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/strategies/")
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1
        assert any(s["strategy_id"] == "strategy_v1" for s in data)


@pytest.mark.asyncio
async def test_risk_circuit_breaker_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/risk/circuit-breaker")
        assert res.status_code == 200
        data = res.json()
        assert "kill_switch_active" in data
        assert "max_drawdown_threshold_pct" in data


@pytest.mark.asyncio
async def test_run_backtest_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "strategy_id": "strategy_v1",
            "symbol": "EURUSD",
            "timeframe": "H1",
            "initial_capital": 10000.0,
            "run_monte_carlo": False,
        }
        res = await client.post("/api/v1/backtest/run", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["strategy_id"] == "strategy_v1"
        assert "win_rate" in data
