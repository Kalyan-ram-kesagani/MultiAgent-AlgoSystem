"""Pydantic schemas for AI Trading & Research Agent tools and responses."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentRuntimeState(str, Enum):
    IDLE = "IDLE"
    THINKING = "THINKING"
    TOOL_CALL = "TOOL_CALL"
    RESEARCHING = "RESEARCHING"
    BACKTESTING = "BACKTESTING"
    RISK_CHECK = "RISK_CHECK"
    EXECUTING = "EXECUTING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    ERROR = "ERROR"
    STOPPED = "STOPPED"


class Candle(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class CandlesResponse(BaseModel):
    symbol: str
    timeframe: str
    count: int
    candles: List[Candle]


class CurrentPriceResponse(BaseModel):
    symbol: str
    bid: float
    ask: float
    spread_pips: float
    timestamp: str


class MarketSessionResponse(BaseModel):
    session: str  # ASIAN, LONDON, NY, OVERLAP, CLOSED
    utc_time: str
    is_active: bool


class MarketRegimeResponse(BaseModel):
    symbol: str
    regime: str  # TRENDING_BULL, TRENDING_BEAR, RANGING, HIGH_VOLATILITY, LOW_VOLATILITY
    volatility: float
    trend_strength: float
    description: str


class MT5AccountInfo(BaseModel):
    login: Optional[int] = None
    server: Optional[str] = None
    balance: float = 0.0
    equity: float = 0.0
    margin: float = 0.0
    free_margin: float = 0.0
    leverage: int = 100
    currency: str = "USD"
    trade_mode: str = "DEMO"
    connected: bool = False


class MT5Position(BaseModel):
    ticket: int
    symbol: str
    side: str
    volume: float
    open_price: float
    current_price: float
    sl: float
    tp: float
    profit: float
    open_time: str


class StrategyPerformanceResponse(BaseModel):
    strategy_id: str
    total_trades: int
    win_rate: float
    profit_factor: float
    expectancy: float
    net_pnl: float
    max_drawdown: float
    sample_status: str  # INSUFFICIENT DATA (<10), EARLY DATA (10-49), PRELIMINARY (50-99), RESEARCHABLE (100+)
    origin_breakdown: Dict[str, Any] = Field(default_factory=dict)
    summary: str


class ResearchHypothesisInput(BaseModel):
    title: str = Field(..., description="Short hypothesis title")
    hypothesis_statement: str = Field(..., description="Clear, falsifiable hypothesis statement")
    reasoning: str = Field(..., description="Economic or quantitative rationale")
    test_plan: str = Field(..., description="Methodology to test the hypothesis")
    success_metric: str = Field(..., description="Measurable metric defining success")
    failure_condition: str = Field(..., description="Measurable condition defining failure")


class ResearchHypothesisResponse(BaseModel):
    hypothesis_id: str
    title: str
    hypothesis_statement: str
    reasoning: str
    test_plan: str
    success_metric: str
    failure_condition: str
    status: str
    created_at: str


class BacktestRunInput(BaseModel):
    strategy_id: str = Field(default="strategy_v1", description="Baseline or candidate strategy ID")
    symbol: str = Field(default="EURUSD", description="Market symbol (e.g. EURUSD, XAUUSD)")
    timeframe: str = Field(default="H1", description="Timeframe bar interval (e.g. M15, H1, D1)")
    days: int = Field(default=90, ge=10, le=730, description="Historical period in days")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Custom strategy parameters to evaluate")


class BacktestRunResponse(BaseModel):
    run_id: str
    strategy_id: str
    symbol: str
    timeframe: str
    period_days: int
    total_trades: int
    win_rate: float
    profit_factor: float
    expectancy: float
    net_pnl: float
    max_drawdown: float
    monte_carlo_drawdown_95: float
    sample_status: str
    metrics: Dict[str, Any]


class WalkForwardInput(BaseModel):
    strategy_id: str = Field(default="strategy_v1")
    symbol: str = Field(default="EURUSD")
    windows: int = Field(default=4, ge=2, le=10, description="Number of rolling out-of-sample test splits")
    parameters: Optional[Dict[str, Any]] = None


class WalkForwardResponse(BaseModel):
    strategy_id: str
    symbol: str
    windows: int
    in_sample_pf: float
    out_of_sample_pf: float
    stability_score: float
    is_robust: bool
    summary: str


class MonteCarloInput(BaseModel):
    strategy_id: str = Field(default="strategy_v1")
    symbol: str = Field(default="EURUSD")
    simulations: int = Field(default=1000, ge=100, le=5000)


class MonteCarloResponse(BaseModel):
    strategy_id: str
    simulations: int
    worst_case_drawdown_95pct: float
    median_expectancy: float
    prob_ruin_pct: float
    is_acceptable: bool


class StrategyCandidateInput(BaseModel):
    base_strategy_id: str = Field(..., description="ID of baseline strategy being evolved")
    new_version: str = Field(..., description="Semantic version string, e.g. v1.1.0")
    parameters: Dict[str, Any] = Field(..., description="Parameter dictionary for new version")
    hypothesis_id: Optional[str] = Field(default=None, description="Related research hypothesis ID")
    changelog: str = Field(..., description="Explanation of modifications made")


class OrderRequestInput(BaseModel):
    symbol: str = Field(..., description="Currency pair or commodity, e.g. EURUSD, XAUUSD")
    side: str = Field(..., description="BUY or SELL")
    quantity: float = Field(..., ge=0.01, le=10.0, description="Requested lot volume")
    stop_loss: float = Field(..., description="Explicit stop loss price")
    take_profit: float = Field(..., description="Explicit take profit price")
    strategy_id: str = Field(..., description="Originating strategy version ID")
    reason: str = Field(..., description="Explicit structured reasoning for trade request")


class OrderRequestResponse(BaseModel):
    approved: bool
    reason: str
    request_id: Optional[str] = None
    client_order_id: Optional[str] = None
    broker_ticket: Optional[int] = None
    executed_quantity: Optional[float] = None
    executed_price: Optional[float] = None
    risk_check: Dict[str, Any] = Field(default_factory=dict)


class SystemHealthResponse(BaseModel):
    status: str
    mt5_status: str
    db_status: str
    risk_engine_status: str
    kill_switch_active: bool
    kill_switch_reason: Optional[str] = None
    trading_mode: str
    environment: str
