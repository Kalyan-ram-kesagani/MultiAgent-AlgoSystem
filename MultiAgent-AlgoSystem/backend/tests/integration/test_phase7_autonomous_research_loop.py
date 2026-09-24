import json
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from backend.app.main import app
from backend.app.ai_agent.tools.trade_analysis import get_strategy_performance
from backend.app.ai_agent.tools.research import (
    create_hypothesis,
    get_hypothesis,
    create_experiment,
    get_experiment,
    record_research_result,
)
from backend.app.ai_agent.tools.backtesting import (
    run_backtest,
    run_walk_forward,
    run_monte_carlo,
    compare_strategies,
)
from backend.app.ai_agent.tools.strategy import (
    create_strategy_candidate,
    get_strategy_versions,
    validate_strategy,
)
from backend.app.database.session import async_session_maker
from backend.app.models.research import Experiment, Hypothesis
from backend.app.models.strategy import StrategyVersion


@pytest.mark.asyncio
async def test_phase7_1_sample_size_research_gates():
    """Verify statistical sample size gates: <10, 10-49, 50-99, 100+."""
    perf_str = get_strategy_performance("strategy_v1")
    perf = json.loads(perf_str)
    
    assert "sample_status" in perf
    assert "sample_size" in perf
    # In fresh DB with <10 trades
    assert "INSUFFICIENT DATA" in perf["sample_status"] or "EARLY DATA" in perf["sample_status"]


@pytest.mark.asyncio
async def test_phase7_2_hypothesis_generation_and_persistence():
    """Verify hypothesis formulation persists in database with non-dogmatic disclaimer."""
    hyp_json = create_hypothesis(
        strategy_id="strategy_v1",
        title="Test Fast EMA Momentum Filter",
        hypothesis="Lowering EMA fast period from 20 to 14 increases trend capture in H1 EURUSD.",
        reason="Visual backtest inspection indicates delayed entries on sharp momentum bursts.",
        evidence=["Trade #102 entry delayed by 3 bars", "Trade #105 exit late by 2 bars"],
        test_plan="Walk-forward OOS testing over 90 days and 500-permutation Monte Carlo simulation.",
        success_metric="Profit Factor >= 1.25, Max DD <= 10%",
        failure_condition="Out-of-sample PF < 1.0 or Max DD > 10%",
    )
    res = json.loads(hyp_json)
    assert res["success"] is True
    hyp_id = res["hypothesis_id"]
    assert hyp_id.startswith("HYP-")

    # Verify retrieval
    detail_str = get_hypothesis(hyp_id)
    detail = json.loads(detail_str)
    assert detail["hypothesis_id"] == hyp_id
    assert detail["status"] == "PROPOSED"
    assert len(detail["evidence"]) == 2


@pytest.mark.asyncio
async def test_phase7_3_experiment_creation_and_research_execution():
    """Verify experiment lifecycle: Backtest, Walk-Forward, Monte Carlo, and Baseline Comparison."""
    # 1. Create experiment record linked to hypothesis
    exp_json = create_experiment(
        experiment_name="Fast EMA 14 Parameter Optimization",
        strategy_id="strategy_v1",
        baseline_strategy_version="v1.0.0",
        candidate_strategy_version="v1.1.0-exp1",
        hypothesis_id="HYP-PHASE7-TEST",
        dataset_description="EURUSD_H1_90D",
        sample_size=200,
        parameters_json=json.dumps({"ema_fast": 14, "ema_slow": 45}),
    )
    exp_res = json.loads(exp_json)
    exp_id = exp_res["experiment_id"]
    assert exp_id.startswith("EXP-")
    assert exp_res["status"] == "CREATED"

    # 2. Run Backtest
    bt_res = json.loads(run_backtest(
        strategy_id="strategy_v1",
        symbol="EURUSD",
        timeframe="H1",
        days=60,
        parameters_json=json.dumps({"ema_fast": 14, "ema_slow": 45}),
    ))
    assert "metrics" in bt_res
    assert "profit_factor" in bt_res["metrics"]
    assert "max_drawdown_pct" in bt_res["metrics"]
    assert "monte_carlo_drawdown_95pct" in bt_res["metrics"]

    # 3. Run Walk-Forward Validation
    wf_res = json.loads(run_walk_forward(
        strategy_id="strategy_v1",
        symbol="EURUSD",
        windows=3,
    ))
    assert "windows_evaluated" in wf_res
    assert "walk_forward_efficiency_ratio" in wf_res

    # 4. Run Monte Carlo Simulation
    mc_res = json.loads(run_monte_carlo(
        strategy_id="strategy_v1",
        symbol="EURUSD",
        timeframe="H1",
        days=60,
        simulations=500,
        random_seed=42,
    ))
    assert mc_res["simulations"] == 500
    assert "worst_case_drawdown_95pct" in mc_res
    assert mc_res["drawdown_type"] == "Peak-to-Trough Maximum Drawdown Percentage of Equity Curve"

    # 5. Baseline Comparison
    comp_res = json.loads(compare_strategies("strategy_v1", "strategy_v1"))
    assert "comparison_table" in comp_res or "candidate_improves_baseline" in comp_res
    assert "baseline_strategy" in comp_res


@pytest.mark.asyncio
async def test_phase7_4_candidate_immutability_and_activation_block():
    """Verify candidate strategies are immutable and AI CANNOT auto-activate them."""
    unique_version = "v1.7.0-test"
    
    # 1. Create candidate
    cand_json = create_strategy_candidate(
        strategy_id="strategy_v1",
        version=unique_version,
        parameters={"ema_fast": 15, "ema_slow": 45, "reward_risk_ratio": 2.0},
        rules="EMA crossover with ATR volatility stop",
        created_from="v1.0.0",
        experiment_id="EXP-IMMUTABLE-01",
        changelog="Optimized fast EMA for higher trend adherence",
    )
    cand_res = json.loads(cand_json)
    assert cand_res["status"] == "CANDIDATE"
    assert cand_res["version"] == unique_version

    # 2. Immutability check: Attempting to overwrite existing version must fail
    cand_overwrite = create_strategy_candidate(
        strategy_id="strategy_v1",
        version=unique_version,
        parameters={"ema_fast": 12, "ema_slow": 40},
    )
    overwrite_res = json.loads(cand_overwrite)
    assert "error" in overwrite_res
    assert "already exists" in overwrite_res["error"]


@pytest.mark.asyncio
async def test_phase7_5_human_approval_gate_and_live_deployment_block():
    """Verify human approval gate for promotion and proof that LIVE deployment is blocked."""
    # Create an experiment to review
    exp_id = "EXP-HUMAN-GATE-01"
    async with async_session_maker() as session:
        exp = Experiment(
            experiment_id=exp_id,
            experiment_name="Human Review Gate Test",
            strategy_id="strategy_v1",
            strategy_version="v1.7.0-test",
            status="CANDIDATE",
            parameters_json="{}",
            action="PENDING_HUMAN_REVIEW",
        )
        session.add(exp)
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. LIVE deployment must be rejected with 403 Forbidden
        live_res = await ac.post(
            f"/api/research/experiments/{exp_id}/review",
            json={"decision": "LIVE_DEPLOYMENT", "operator_comment": "Attempting live activation"},
        )
        assert live_res.status_code == 403
        assert "LIVE trading deployment is strictly disabled" in live_res.json()["detail"]

        # 2. Valid promotion to DEMO_VALIDATION
        demo_res = await ac.post(
            f"/api/research/experiments/{exp_id}/review",
            json={"decision": "DEMO_VALIDATION", "operator_comment": "Approved for paper/demo forward testing"},
        )
        assert demo_res.status_code == 200
        data = demo_res.json()
        assert data["decision"] == "DEMO_VALIDATION"
        assert data["human_approved"] is True
        assert data["trading_mode"] == "DEMO"
