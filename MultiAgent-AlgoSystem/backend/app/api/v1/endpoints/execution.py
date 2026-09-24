"""Execution Agent API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.execution.execution_agent import ExecutionAgent
from backend.app.database.session import get_db
from backend.app.models.trading import Position
from backend.app.schemas.trading import SignalCreate
from trading.execution.mt5_client import mt5_client

router = APIRouter(prefix="/execution", tags=["Execution & MT5"])


@router.post("/process-signal")
async def process_signal(signal: SignalCreate, db: AsyncSession = Depends(get_db)):
    """Pass signal through Risk Engine and submit to MT5 if approved."""
    agent = ExecutionAgent(db_session=db)
    result = await agent.execute_signal(signal)
    return result


@router.get("/account")
def get_broker_account():
    """Retrieve MT5/Broker account metrics."""
    return mt5_client.get_account_info()


@router.get("/price/{symbol}")
def get_symbol_price(symbol: str):
    """Retrieve current symbol prices and spread."""
    return mt5_client.get_symbol_price(symbol)


@router.get("/positions")
def get_open_positions(symbol: Optional[str] = None):
    """Retrieve all active open positions from MT5."""
    return mt5_client.get_open_positions(symbol=symbol)


@router.post("/positions/{ticket}/close")
async def close_open_position(ticket: int, db: AsyncSession = Depends(get_db)):
    """Close an open position by ticket number in MT5."""
    res = mt5_client.close_position(ticket=ticket)
    if res and res.get("success"):
        try:
            await db.execute(delete(Position).where(Position.ticket == ticket))
            await db.commit()
        except Exception:
            pass
    return res


@router.get("/reconcile")
async def reconcile_positions(db: AsyncSession = Depends(get_db)):
    """Reconcile broker open positions against internal records."""
    agent = ExecutionAgent(db_session=db)
    return await agent.reconcile_positions()


@router.get("/health-report")
def get_gateway_health_report():
    """Get full MT5 gateway telemetry and connection health report."""
    return mt5_client.get_health_report()
