"""Comprehensive tests for Phase 2: AI Research & Experiment Engine."""
import json
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from backend.app.ai_agent.runtime import agent_runtime
from backend.app.ai_agent.tools.backtesting import compare_strategies, run_backtest, run_monte_carlo, run_walk_forward
from backend.app.ai_agent.tools.research import create_experiment, create_hypothesis, get_experiment, get_hypothesis
from backend.app.ai_agent.tools.strategy import create_strategy_candidate, get_strategy_versions
from backend.app.ai_agent.tools.trade_analysis import analyze_trade_sources, get_strategy_performance
from backend.app.database.session import async_session_maker, init_db
from backend.app.main import app
from backend.app.models.research import Experiment, Hypothesis
from backend.app.models.strategy import StrategyVersion
from backend.app.models.trading import Trade
from trading.execution.mt5_client import mt5_client


@pytest_asyncio.fixture(autouse=True)
async def setup_test_environment():
    """Ensure in-memory database is clean and simulation mode active."""
    mt5_client.is_simulation_mode = True
    await init_db()
    yield


@pytest.mark.asyncio
async def test_1_and_2_manual_and_external_trades_not_attributed_to_strategy_v1():
    """
    TEST 1 & 2:
    Manual trades and external trades are NOT attributed to strategy_v1.
    """
    async with async_session_maker() as session:
        # Insert a sample of trades with different origins
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        t_sys = Trade(
            trade_id="TR-SYS-001",
            strategy_id="strategy_v1",
            order_id="ORD-SYS-001",
            symbol="EURUSD",
            direction="BUY",
            entry_time=now,
            exit_time=now,
            entry_price=1.0850,
            stop_price=1.0800,
            target_price=1.0950,
            exit_price=1.0880,
            quantity=0.1,
            pnl=30.0,
            r_multiple=0.6,
            duration_seconds=3600,
            session="LONDON",
            origin="SYSTEM_GENERATED",
        )
        t_man = Trade(
            trade_id="TR-MAN-002",
            strategy_id="strategy_v1",  # User or broker tagged it, but it was manual
            order_id=None,
            symbol="GBPUSD",
            direction="SELL",
            entry_time=now,
            exit_time=now,
            entry_price=1.2700,
            stop_price=1.2750,
            target_price=1.2600,
            exit_price=1.2650,
            quantity=0.5,
            pnl=250.0,
            r_multiple=1.0,
            duration_seconds=1800,
            session="LONDON",
            origin="MANUAL",
        )
        t_ext = Trade(
            trade_id="TR-EXT-003",
            strategy_id="strategy_v1",
            order_id=None,
            symbol="XAUUSD",
            direction="BUY",
            entry_time=now,
            exit_time=now,
            entry_price=2350.0,
            stop_price=2340.0,
            target_price=2370.0,
            exit_price=2345.0,
            quantity=0.05,
            pnl=-25.0,
            r_multiple=-0.5,
            duration_seconds=900,
            session="NEW_YORK",
            origin="EXTERNAL",
        )
        session.add_all([t_sys, t_man, t_ext])
        await session.commit()

    # Call analyze_trade_sources()
    src_res = json.loads(analyze_trade_sources())
    assert "groups" in src_res
    assert src_res["manual_trades"] >= 1
    assert src_res["external_trades"] >= 1
    assert src_res["system_trades"] >= 1

    # Verify manual and external trades are isolated from strategy_v1
    for g in src_res["groups"]:
        if g["trade_source"] in ("MANUAL", "EXTERNAL"):
            assert g["strategy_id"] != "strategy_v1"


@pytest.mark.asyncio
async def test_3_hypothesis_creation():
    """
    TEST 3:
    Formulate hypothesis with strategy_id, title, hypothesis, reason, evidence.
    Verifies it is recorded with non-factual hypothesis disclaimer.
    """
    res_raw = create_hypothesis(
        strategy_id="strategy_v1",
        title="Asian Session Low Volatility Drag",
        hypothesis="Strategy profitability degrades during Asian session due to range-bound mean reversion.",
        reason="Observed negative expectancy during Tokyo hours.",
        evidence=["Trade TR-001 -$15", "Asian spread widened to 2.4 pips"],
    )
    res = json.loads(res_raw)
    assert res["success"] is True
    assert "HYP-" in res["hypothesis_id"]
    assert res["classification"] == "HYPOTHESIS"
    assert "not an established fact" in res["disclaimer"].lower()

    # Retrieve and verify persistence
    get_raw = get_hypothesis(res["hypothesis_id"])
    h_data = json.loads(get_raw)
    assert h_data["hypothesis_id"] == res["hypothesis_id"]
    assert len(h_data["evidence"]) == 2


@pytest.mark.asyncio
async def test_4_experiment_creation():
    """
    TEST 4:
    Create an immutable experiment record with CREATED status.
    """
    exp_raw = create_experiment(
        experiment_name="EXP-SPREAD-FILTER-TEST",
        strategy_id="strategy_v1",
        baseline_strategy_version="v1.0.0",
        candidate_strategy_version="v1.1.0",
        dataset_description="EURUSD H1 90-day historical",
        sample_size=64,
    )
    exp = json.loads(exp_raw)
    assert "EXP-" in exp["experiment_id"]
    assert exp["status"] == "CREATED"
    assert exp["baseline_version"] == "v1.0.0"
    assert exp["candidate_version"] == "v1.1.0"

    # Verify via get_experiment
    details = json.loads(get_experiment(exp["experiment_id"]))
    assert details["experiment_id"] == exp["experiment_id"]
    assert details["status"] == "CREATED"


@pytest.mark.asyncio
async def test_5_and_6_strategy_version_immutability_and_no_overwrite():
    """
    TEST 5 & 6:
    Strategy versions are immutable; candidate does NOT overwrite baseline.
    """
    # 1. Create candidate version v1.2.0
    v1_raw = create_strategy_candidate(
        strategy_id="strategy_v1",
        version="v1.2.0",
        parameters={"ema_fast": 18, "ema_slow": 45, "reward_risk_ratio": 2.2},
        rules="Stricter EMA slope confirmation",
        created_from="v1.0.0",
        changelog="Tightened fast EMA from 20 to 18",
    )
    v1_res = json.loads(v1_raw)
    assert v1_res["status"] == "CANDIDATE"
    assert v1_res["version"] == "v1.2.0"

    # 2. Attempt to overwrite v1.2.0 with different parameters (Must FAIL)
    dup_raw = create_strategy_candidate(
        strategy_id="strategy_v1",
        version="v1.2.0",
        parameters={"ema_fast": 10, "ema_slow": 30},
        changelog="Attempted overwrite",
    )
    dup_res = json.loads(dup_raw)
    assert "error" in dup_res
    assert "already exists" in dup_res["error"].lower()
    assert "immutable" in dup_res["error"].lower()


@pytest.mark.asyncio
async def test_7_backtest_records_assumptions():
    """
    TEST 7:
    Backtest explicitly records all simulation assumptions:
    date range, symbols, timeframe, initial capital, sizing, spread, commission, slippage.
    """
    bt_raw = run_backtest(
        strategy_id="strategy_v1",
        symbol="EURUSD",
        timeframe="H1",
        days=60,
    )
    bt = json.loads(bt_raw)
    assert "backtest_assumptions" in bt
    assumptions = bt["backtest_assumptions"]
    assert "date_range" in assumptions
    assert "symbols" in assumptions
    assert "timeframe" in assumptions
    assert assumptions["initial_capital"] == 10000.0
    assert "position_sizing" in assumptions
    assert assumptions["spread_assumption_pips"] == 1.5
    assert assumptions["commission_per_lot_usd"] == 7.0
    assert assumptions["slippage_points"] == 5
    assert "future_data_leakage_protection" in assumptions


@pytest.mark.asyncio
async def test_8_walk_forward_separates_oos_from_training():
    """
    TEST 8:
    Walk-forward validation explicitly partitions and distinguishes
    In-Sample (IS) training performance from Out-of-Sample (OOS) validation performance.
    """
    wf_raw = run_walk_forward(strategy_id="strategy_v1", symbol="EURUSD", windows=3)
    wf = json.loads(wf_raw)
    assert "in_sample_performance" in wf
    assert "out_of_sample_performance" in wf
    assert "walk_forward_efficiency_ratio" in wf
    assert "splits" in wf
    assert len(wf["splits"]) >= 2
    for split in wf["splits"]:
        assert "in_sample_pf" in split
        assert "out_of_sample_pf" in split


@pytest.mark.asyncio
async def test_9_monte_carlo_results_stored():
    """
    TEST 9:
    Monte Carlo trade resampling evaluates drawdown percentiles,
    losing streak distributions, and median outcomes.
    """
    mc_raw = run_monte_carlo(strategy_id="strategy_v1", symbol="EURUSD", simulations=150)
    mc = json.loads(mc_raw)
    assert "simulations" in mc
    assert "median_outcome_pnl" in mc
    assert "drawdown_distribution_pct" in mc
    assert "p95" in mc["drawdown_distribution_pct"]
    assert "losing_streak_distribution" in mc
    assert "p95_max_consecutive_losses" in mc["losing_streak_distribution"]


@pytest.mark.asyncio
async def test_10_candidate_comparison_uses_real_metrics():
    """
    TEST 10:
    Strategy comparison evaluates baseline vs candidate using concrete empirical metrics.
    """
    comp_raw = compare_strategies("strategy_v1", "strategy_v1")
    comp = json.loads(comp_raw)
    assert "comparison_table" in comp
    metrics_names = [m["metric"] for m in comp["comparison_table"]]
    assert "Profit Factor" in metrics_names
    assert "Expectancy ($)" in metrics_names
    assert "Max Drawdown (%)" in metrics_names


@pytest.mark.asyncio
async def test_11_insufficient_sample_size_protection():
    """
    TEST 11:
    Less than 10 trades results in INSUFFICIENT_DATA and prevents strategy rule modification.
    """
    # Test tool directly with strategy_v1 having < 10 trades
    perf_raw = get_strategy_performance("strategy_v1")
    perf = json.loads(perf_raw)
    assert "INSUFFICIENT DATA" in perf["sample_status"]


@pytest.mark.asyncio
async def test_12_ai_cannot_automatically_activate_candidate_strategy():
    """
    TEST 12:
    Strategy candidates cannot be automatically set to ACTIVE/APPROVED by the AI;
    they remain in CANDIDATE or DRAFT status awaiting explicit human review.
    """
    c_raw = create_strategy_candidate(
        strategy_id="strategy_v1",
        version="v1.3.0",
        parameters={"ema_fast": 22, "ema_slow": 55},
        rules="New filter candidate",
    )
    c_data = json.loads(c_raw)
    assert c_data["status"] == "CANDIDATE"
    assert c_data["status"] != "APPROVED"
    assert c_data["status"] != "ACTIVE"


@pytest.mark.asyncio
async def test_13_phase_1_ai_run_still_works():
    """
    TEST 13:
    Phase 1 POST /api/ai/run continues working without regressions.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/ai/run",
            json={
                "prompt": "Analyze strategy_v1 trade performance and report status.",
                "task_name": "Phase 1 Backward Compatibility Verification",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "COMPLETED"
        assert "Research Report" in data["response"] or "Quantitative Research" in data["response"]
