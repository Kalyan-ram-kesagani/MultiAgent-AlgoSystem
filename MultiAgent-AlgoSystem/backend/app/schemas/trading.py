"""Pydantic schemas for Signals, Orders, Trades, and Positions."""
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class SignalCreate(BaseModel):
    strategy_id: str
    strategy_version: str
    symbol: str
    direction: str  # BUY, SELL
    timeframe: str
    timestamp: datetime
    suggested_entry: float
    suggested_sl: float
    suggested_tp: float
    risk_points: float
    ml_confidence: Optional[float] = None
    market_regime: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None


class SignalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    signal_id: str
    strategy_id: str
    strategy_version: str
    symbol: str
    direction: str
    timeframe: str
    timestamp: datetime
    suggested_entry: float
    suggested_sl: float
    suggested_tp: float
    risk_points: float
    ml_confidence: Optional[float] = None
    market_regime: Optional[str] = None


class OrderCreate(BaseModel):
    strategy_id: str
    signal_id: Optional[str] = None
    symbol: str
    side: str  # BUY, SELL
    order_type: str = "MARKET"
    quantity: float = Field(gt=0, description="Lot size calculated by Risk Engine")
    price: float
    sl: float
    tp: float


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_order_id: str
    strategy_id: str
    signal_id: Optional[str] = None
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: float
    sl: float
    tp: float
    status: str
    broker_ticket: Optional[int] = None
    broker_response: Optional[str] = None
    created_at: datetime


class TradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trade_id: str
    strategy_id: str
    model_id: Optional[str] = None
    symbol: str
    direction: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    stop_price: float
    target_price: float
    exit_price: float
    quantity: float
    commission: float
    swap: float
    pnl: float
    r_multiple: float
    mfe: float
    mae: float
    duration_seconds: int
    session: str
    market_regime: Optional[str] = None
    exit_reason: str


class PositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket: int
    strategy_id: str
    symbol: str
    side: str
    volume: float
    open_price: float
    current_price: float
    sl: float
    tp: float
    unrealized_pnl: float
    open_time: datetime
