import pytest
import json
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.ai_agent.schemas import AgentRuntimeState
from backend.app.ai_agent.runtime import agent_runtime
from backend.app.agents.risk.risk_engine import risk_engine
from backend.app.core.config import settings


@pytest.mark.asyncio
async def test_phase6_1_system_health_all_eight_services():
    """Verify GET /api/system/health returns live telemetry for all 8 deterministic services."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/system/health")
        assert res.status_code == 200
        data = res.json()

        # All 8 services
        assert "mt5" in data
        assert "supabase" in data
        assert "ai_runtime" in data
        assert "risk_engine" in data
        assert "execution_engine" in data
        assert "backtest_engine" in data
        assert "supervisor" in data
        assert "kill_switch" in data

        # Deterministic fields
        assert data["execution_engine"]["mode"] == "DEMO ONLY"
        assert data["backtest_engine"]["status"] == "OPERATIONAL"
        assert isinstance(data["risk_engine"]["active"], bool)
        assert isinstance(data["kill_switch"]["active"], bool)


@pytest.mark.asyncio
async def test_phase6_2_ai_panel_telemetry():
    """Verify GET /api/ai/status provides complete AI panel fields without fake states."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/ai/status")
        assert res.status_code == 200
        data = res.json()

        assert "status" in data
        assert "current_task" in data
        assert "current_tool" in data
        assert "current_run" in data
        assert "last_action" in data
        assert "last_result" in data
        assert "last_error" in data

        # Real states only
        valid_states = [s.value for s in AgentRuntimeState]
        assert data["status"] in valid_states
        assert data["status"] not in ["ACTIVE", "WAITING", "RUNNING_FAKE"]


@pytest.mark.asyncio
async def test_phase6_3_risk_panel_telemetry():
    """Verify GET /api/risk/status and /api/risk/limits return real limits."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_limits = await ac.get("/api/risk/limits")
        assert res_limits.status_code == 200
        limits = res_limits.json()

        assert limits["max_risk_per_trade_pct"] == settings.RISK_PER_TRADE_PCT * 100
        assert limits["max_portfolio_drawdown_pct"] == settings.MAX_ACCOUNT_DRAWDOWN_PCT * 100
        assert limits["max_daily_loss_pct"] == settings.MAX_DAILY_LOSS_PCT * 100
        assert limits["max_open_positions"] == settings.MAX_OPEN_POSITIONS
        assert limits["max_symbol_exposure"] == settings.MAX_SYMBOL_EXPOSURE
        assert limits["ai_modification_permitted"] is False

        res_status = await ac.get("/api/risk/status")
        assert res_status.status_code == 200
        status = res_status.json()
        assert "kill_switch_active" in status
        assert "daily_loss_pct" in status
        assert "peak_equity" in status
        assert "current_drawdown_pct" in status
        assert "open_positions_count" in status


@pytest.mark.asyncio
async def test_phase6_4_stream_endpoint_initial_sync():
    """Verify sse_event_stream provides real SSE initial sync without errors."""
    from unittest.mock import AsyncMock
    from backend.app.api.v1.endpoints.system_reconciliation import sse_event_stream
    
    mock_request = AsyncMock()
    mock_request.is_disconnected.return_value = False
    
    response = await sse_event_stream(mock_request)
    assert response.status_code == 200
    assert response.media_type == "text/event-stream"
    
    gen = response.body_iterator
    first_chunk = await gen.__anext__()
    assert first_chunk.startswith("data: ")
    payload = json.loads(first_chunk.strip()[6:])
    assert payload.get("type") == "INITIAL_SYNC"
    assert "account" in payload
    assert "terminal" in payload
    await gen.aclose()
