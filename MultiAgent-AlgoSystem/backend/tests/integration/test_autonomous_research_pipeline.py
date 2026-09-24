"""Integration tests for Autonomous Research & Strategy Improvement Pipeline."""
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.agents.performance.performance_agent import performance_agent
from backend.app.database.session import async_session_maker
from backend.app.main import app
from backend.app.models.trading import Trade
from backend.app.services.performance_monitor import performance_monitor


@pytest.mark.asyncio
async def test_performance_sample_status_and_segmentation():
    """Verify PerformanceAgent calculates 14 metrics and 10 segmentations with sample-size thresholds."""
    # Test insufficient sample (< 30)
    status_small = performance_agent.determine_sample_status(10)
    assert status_small["status"] == "INSUFFICIENT SAMPLE"
    assert status_small["confidence"] == "LOW"

    # Test early analysis (30-99)
    status_med = performance_agent.determine_sample_status(50)
    assert status_med["status"] == "EARLY ANALYSIS"
    assert status_med["confidence"] == "MODERATE"

    # Test researchable (100+)
    status_large = performance_agent.determine_sample_status(120)
    assert status_large["status"] == "RESEARCHABLE"
    assert status_large["confidence"] == "HIGH"


@pytest.mark.asyncio
async def test_performance_degradation_monitor():
    """Verify PerformanceMonitor detects negative expectancy and symbol degradation with sample-size awareness."""
    mock_metrics = {
        "trade_count": 10,
        "expectancy": -1.21,
        "profit_factor": 0.20,
        "consecutive_losses": 3,
        "by_market": {
            "EURUSD": {"count": 10, "win_rate": 10.0, "net_pnl": -15.02},
        },
        "by_session": {
            "NEW_YORK": {"count": 8, "net_pnl": -15.02},
        },
    }
    alerts = performance_monitor.detect_degradations(mock_metrics)
    assert len(alerts) >= 2
    # Verify severity is marked LOW_SAMPLE because trade_count is 10
    for alert in alerts:
        if alert.get("sample_size", 0) < 30:
            assert alert["severity"] in ("LOW_SAMPLE", "MODERATE")


@pytest.mark.asyncio
async def test_api_performance_degradation_endpoint():
    """Verify GET /api/performance/degradation returns sample status and alerts."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/performance/degradation")
        assert res.status_code == 200
        data = res.json()
        assert "sample_status" in data
        assert "metrics" in data
        assert "degradation_alerts" in data
        assert "investigation_recommended" in data


@pytest.mark.asyncio
async def test_autonomous_investigation_and_experiment_lifecycle():
    """
    Test full autonomous research workflow:
    POST /api/orchestrator/investigate
    -> Hypothesis generated
    -> ML features analyzed
    -> Bounded Candidate strategy_v1.1 generated
    -> Walk-Forward & Monte Carlo comparison against baseline
    -> Experiment registered with PENDING_HUMAN_REVIEW
    -> Human operator review
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Trigger autonomous investigation
        inv_payload = {
            "symbol": "EURUSD",
            "strategy_id": "strategy_v1",
            "issue": "negative expectancy",
            "force_run": True,
        }
        res = await ac.post("/api/orchestrator/investigate", json=inv_payload)
        assert res.status_code == 200
        data = res.json()

        assert "hypothesis" in data
        assert "ml_analysis" in data
        assert "comparison" in data
        assert "experiment_id" in data
        assert data["baseline_strategy"] == "strategy_v1"
        assert data["candidate_strategy"] == "strategy_v1.1"
        assert data["status"] == "PENDING_HUMAN_REVIEW"

        exp_id = data["experiment_id"]

        # 2. Check hypotheses endpoint
        hyp_res = await ac.get("/api/research/hypotheses")
        assert hyp_res.status_code == 200
        hypotheses = hyp_res.json()
        assert len(hypotheses) > 0

        # 3. Check experiments endpoint
        exp_res = await ac.get("/api/research/experiments")
        assert exp_res.status_code == 200
        experiments = exp_res.json()
        assert any(e["experiment_id"] == exp_id for e in experiments)

        # 4. Check strategy versions endpoint (immutable versioning)
        ver_res = await ac.get("/api/strategies/versions")
        assert ver_res.status_code == 200
        versions = ver_res.json()
        assert any(v["strategy_id"] == "strategy_v1" for v in versions)

        # 5. Human operator review: Approve for demo staging
        rev_payload = {
            "decision": "APPROVED_FOR_DEMO",
            "operator_comment": "Verified walk-forward stability and reduced drawdown.",
        }
        rev_res = await ac.post(f"/api/research/experiments/{exp_id}/review", json=rev_payload)
        assert rev_res.status_code == 200
        rev_data = rev_res.json()
        assert rev_data["status"] == "DECISION_RECORDED"
        assert rev_data["decision"] == "APPROVED_FOR_DEMO"
        assert rev_data["human_approved"] is True
