"""Backtesting and Monte Carlo API endpoints."""
import pandas as pd
from fastapi import APIRouter, HTTPException
from backend.app.agents.backtest.backtest_engine import BacktestEngine
from backend.app.agents.data.data_agent import DataAgent
from backend.app.agents.strategy.strategy_agent import StrategyAgent
from backend.app.schemas.backtest import BacktestRequest, BacktestResponse

router = APIRouter(prefix="/backtest", tags=["Backtesting"])
backtest_engine = BacktestEngine()
strategy_agent = StrategyAgent()
data_agent = DataAgent()


@router.post("/run", response_model=BacktestResponse)
def run_backtest(req: BacktestRequest):
    """Run deterministic historical backtest with transaction costs and Monte Carlo."""
    strategy = strategy_agent.get_strategy(req.strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail=f"Strategy '{req.strategy_id}' not found.")

    # Ingest / Generate synthetic bars for backtest if live DB bars not loaded
    bars = data_agent.generate_synthetic_data(
        symbol=req.symbol,
        timeframe=req.timeframe,
        num_bars=600,
    )
    df = pd.DataFrame([b.model_dump() for b in bars])

    result = backtest_engine.run_backtest(strategy, df, req)
    return result
