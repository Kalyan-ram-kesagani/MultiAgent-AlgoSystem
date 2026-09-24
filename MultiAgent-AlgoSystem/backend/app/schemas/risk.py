"""Pydantic schemas for risk evaluations and circuit breakers."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class RiskEvaluationRequest(BaseModel):
    strategy_id: str
    symbol: str
    side: str
    entry_price: float
    stop_loss: float
    take_profit: float
    account_equity: float
    account_balance: float
    current_spread_pips: float
    open_positions_count: int
    symbol_positions_count: int
    daily_realized_loss: float = 0.0
    daily_unrealized_loss: float = 0.0


class RiskEvaluationResult(BaseModel):
    is_approved: bool
    calculated_lots: float
    rejection_reasons: List[str] = []
    risk_amount_dollars: float
    risk_percentage: float
    stop_distance_points: float
    metrics_snapshot: Dict[str, Any] = {}


class KillSwitchRequest(BaseModel):
    activate: bool
    reason: str
    requested_by: str = "operator"


class CircuitBreakerStatusResponse(BaseModel):
    kill_switch_active: bool
    trading_paused: bool
    pause_reason: Optional[str] = None
    consecutive_losses: int
    current_day_loss: float
    current_week_loss: float
    peak_equity: float
    current_drawdown_pct: float
    max_drawdown_threshold_pct: float
    max_daily_loss_threshold_pct: float
