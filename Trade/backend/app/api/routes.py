"""
API Routes

All REST API endpoints for the trading platform.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.models import TradingAccount, Trade, Strategy, JournalEntry
from app.schemas import (
    AccountResponse,
    AccountCreate,
    TradeResponse,
    StrategyResponse,
    StrategyCreate,
    JournalResponse,
    JournalCreate,
    DashboardResponse,
    TodayMetrics,
    AccountMetrics,
    OverallMetrics,
)

router = APIRouter()


# ─── Dashboard ───
@router.get("/dashboard")
async def get_dashboard(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard metrics for the selected account."""
    # Placeholder response — will be computed from real data when MT5 is connected
    return {
        "today": {
            "pnl": 0.0,
            "trades": 0,
            "win_rate": 0.0,
            "wins": 0,
            "losses": 0,
            "drawdown": 0.0,
        },
        "account": {
            "balance": 0.0,
            "equity": 0.0,
            "floating_pl": 0.0,
            "margin": 0.0,
            "free_margin": 0.0,
        },
        "overall": {
            "total_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "profit_factor": 0.0,
        },
    }


# ─── Accounts ───
@router.get("/accounts", response_model=list[AccountResponse])
async def get_accounts(db: AsyncSession = Depends(get_db)):
    """Get all trading accounts."""
    result = await db.execute(select(TradingAccount))
    return result.scalars().all()


@router.post("/accounts", response_model=AccountResponse)
async def create_account(data: AccountCreate, db: AsyncSession = Depends(get_db)):
    """Add a new trading account."""
    account = TradingAccount(**data.model_dump())
    db.add(account)
    await db.flush()
    await db.refresh(account)
    return account


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(account_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific trading account."""
    result = await db.execute(
        select(TradingAccount).where(TradingAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.delete("/accounts/{account_id}")
async def delete_account(account_id: UUID, db: AsyncSession = Depends(get_db)):
    """Remove a trading account."""
    result = await db.execute(
        select(TradingAccount).where(TradingAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    await db.delete(account)
    return {"status": "deleted"}


# ─── Trades ───
@router.get("/trades", response_model=list[TradeResponse])
async def get_trades(
    account_id: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    direction: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get trade history with optional filters."""
    query = select(Trade)

    if account_id:
        query = query.where(Trade.account_id == account_id)
    if symbol:
        query = query.where(Trade.symbol == symbol.upper())
    if direction:
        query = query.where(Trade.direction == direction.upper())
    if status:
        query = query.where(Trade.status == status.upper())
    if result:
        query = query.where(Trade.result == result.upper())

    query = query.order_by(Trade.entry_time.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result_set = await db.execute(query)
    return result_set.scalars().all()


@router.get("/trades/{trade_id}", response_model=TradeResponse)
async def get_trade(trade_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific trade by ID."""
    result = await db.execute(select(Trade).where(Trade.id == trade_id))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


# ─── Positions ───
@router.get("/positions")
async def get_positions(
    account_id: Optional[str] = Query(None),
):
    """
    Get open positions.

    In Phase 2, this will query MT5 directly for live positions.
    For now, returns an empty list.
    """
    return []


# ─── Strategies ───
@router.get("/strategies", response_model=list[StrategyResponse])
async def get_strategies(db: AsyncSession = Depends(get_db)):
    """Get all strategies."""
    result = await db.execute(select(Strategy).order_by(Strategy.created_at.desc()))
    return result.scalars().all()


@router.get("/strategies/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific strategy."""
    result = await db.execute(select(Strategy).where(Strategy.id == strategy_id))
    strategy = result.scalar_one_or_none()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@router.post("/strategies", response_model=StrategyResponse)
async def create_strategy(data: StrategyCreate, db: AsyncSession = Depends(get_db)):
    """Create a new strategy."""
    strategy = Strategy(**data.model_dump())
    db.add(strategy)
    await db.flush()
    await db.refresh(strategy)
    return strategy


# ─── Journal ───
@router.get("/journal", response_model=list[JournalResponse])
async def get_journal(
    user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get journal entries."""
    query = select(JournalEntry).order_by(JournalEntry.created_at.desc())
    if user_id:
        query = query.where(JournalEntry.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/journal", response_model=JournalResponse)
async def create_journal_entry(data: JournalCreate, db: AsyncSession = Depends(get_db)):
    """Create a new journal entry."""
    entry = JournalEntry(**data.model_dump())
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


# ─── Analytics ───
@router.get("/analytics")
async def get_analytics(
    account_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Get trading analytics.

    In Phase 4+, this will compute detailed analytics.
    For now, returns a placeholder structure.
    """
    return {
        "win_rate": 0.0,
        "total_trades": 0,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "profit_factor": 0.0,
        "best_trade": 0.0,
        "worst_trade": 0.0,
        "avg_hold_time": "0m",
        "symbol_breakdown": [],
        "strategy_breakdown": [],
        "monthly_pnl": [],
    }


# ─── Health ───
@router.get("/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "ok",
        "services": {
            "trading_system": "ok",
            "database": "ok",
            "mt5_connection": "disconnected",
            "strategy_engine": "ok",
            "risk_engine": "ok",
            "ai_engine": "coming_soon",
        },
    }
