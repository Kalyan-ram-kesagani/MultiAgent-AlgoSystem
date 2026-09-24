"""Unit tests for Backtesting Engine and Monte Carlo simulation."""
import pandas as pd
from backend.app.agents.backtest.backtest_engine import BacktestEngine
from backend.app.agents.data.data_agent import DataAgent
from backend.app.schemas.backtest import BacktestRequest
from strategies.strategy_v1.trend_pullback import StrategyV1


def test_backtest_engine_execution():
    engine = BacktestEngine()
    strategy = StrategyV1()
    bars = DataAgent.generate_synthetic_data("EURUSD", "H1", num_bars=500, seed=123)
    df = pd.DataFrame([b.model_dump() for b in bars])

    req = BacktestRequest(
        strategy_id="strategy_v1",
        symbol="EURUSD",
        timeframe="H1",
        initial_capital=10000.0,
        spread_pips=1.5,
        slippage_points=5,
        commission_per_lot=7.0,
        run_monte_carlo=True,
        monte_carlo_iterations=50,
    )
    res = engine.run_backtest(strategy, df, req)

    assert res.backtest_id.startswith("BT-")
    assert res.win_rate >= 0.0
    assert len(res.equity_curve) > 0
    if res.trades:
        assert res.monte_carlo_drawdown_95 is not None
        assert res.monte_carlo_drawdown_95 >= 0.0
