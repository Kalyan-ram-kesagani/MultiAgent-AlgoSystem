from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from uuid import UUID


# ─── Account ───
class AccountBase(BaseModel):
    broker: str
    account_name: str
    account_number: str
    currency: str = "USD"
    account_type: str = "live"

class AccountCreate(AccountBase):
    pass

class AccountResponse(AccountBase):
    id: UUID
    user_id: UUID
    balance: float
    equity: float
    status: str
    last_sync: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Trade ───
class TradeBase(BaseModel):
    symbol: str
    direction: str
    volume: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    entry_time: datetime

class TradeCreate(TradeBase):
    account_id: UUID
    strategy_id: Optional[UUID] = None

class TradeResponse(TradeBase):
    id: UUID
    account_id: UUID
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    profit_loss: Optional[float] = None
    commission: float = 0.0
    swap: float = 0.0
    status: str
    result: Optional[str] = None
    strategy_id: Optional[UUID] = None
    initial_risk_percent: Optional[float] = None
    initial_risk_amount: Optional[float] = None
    risk_free_status: str = "N/A"
    break_even_price: Optional[float] = None
    risk_free_activated_time: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Strategy ───
class StrategyBase(BaseModel):
    name: str
    version: str
    description: Optional[str] = None

class StrategyCreate(StrategyBase):
    pass

class StrategyResponse(StrategyBase):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Journal ───
class JournalBase(BaseModel):
    notes: Optional[str] = None
    reason: Optional[str] = None
    lessons: Optional[str] = None

class JournalCreate(JournalBase):
    trade_id: Optional[UUID] = None

class JournalResponse(JournalBase):
    id: UUID
    trade_id: Optional[UUID] = None
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Position ───
class PositionResponse(BaseModel):
    id: str
    account_id: str
    symbol: str
    direction: str
    volume: float
    entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    floating_pl: float
    open_time: datetime
    duration: str


# ─── Dashboard ───
class TodayMetrics(BaseModel):
    pnl: float
    trades: int
    win_rate: float
    wins: int
    losses: int
    drawdown: float

class AccountMetrics(BaseModel):
    balance: float
    equity: float
    floating_pl: float
    margin: float
    free_margin: float

class OverallMetrics(BaseModel):
    total_trades: int
    win_rate: float
    total_pnl: float
    profit_factor: float

class DashboardResponse(BaseModel):
    today: TodayMetrics
    account: AccountMetrics
    overall: OverallMetrics


# ─── Paginated ───
class PaginatedResponse(BaseModel):
    data: list
    total: int
    page: int
    page_size: int
    total_pages: int
