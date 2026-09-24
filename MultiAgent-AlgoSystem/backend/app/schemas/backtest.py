"""Pydantic schemas for backtesting and performance analytics."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BacktestRequest(BaseModel):
    strategy_id: str
    strategy_version: str = "v1.0.0"
    symbol: str = "EURUSD"
    timeframe: str = "H1"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    initial_capital: float = 10000.0
    spread_pips: float = 1.5
    slippage_points: int = 5
    commission_per_lot: float = 7.0
    parameters: Dict[str, Any] = {}
    is_out_of_sample: bool = False
    run_monte_carlo: bool = False
    monte_carlo_iterations: int = 250


class BacktestTradeSummary(BaseModel):
    symbol: str
    direction: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    sl: float
    tp: float
    quantity: float
    pnl: float
    r_multiple: float
    exit_reason: str


class BacktestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    backtest_id: str
    strategy_id: str
    strategy_version: str
    symbol: str
    timeframe: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    net_profit: float
    profit_factor: float
    expectancy: float
    average_win: float
    average_loss: float
    max_drawdown_pct: float
    max_drawdown_dollars: Optional[float] = 0.0
    sharpe_ratio: float
    sortino_ratio: float
    average_r: float
    monte_carlo_drawdown_95: Optional[float] = None
    equity_curve: List[Dict[str, Any]] = []
    trades: List[BacktestTradeSummary] = []
