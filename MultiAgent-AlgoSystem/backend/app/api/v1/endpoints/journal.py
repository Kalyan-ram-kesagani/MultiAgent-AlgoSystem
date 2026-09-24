"""Trade Journal and Performance Attribution API endpoints."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.journal.journal_agent import JournalAgent
from backend.app.agents.performance.performance_agent import performance_agent
from backend.app.database.session import get_db
from backend.app.schemas.trading import TradeResponse

router = APIRouter(prefix="/journal", tags=["Journal & Performance"])


@router.get("/trades")
async def list_trades(
    symbol: Optional[str] = None,
    strategy_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve logged trade journal entries."""
    agent = JournalAgent(db_session=db)
    trades = await agent.get_trades(symbol=symbol, strategy_id=strategy_id, limit=limit)
    return trades


@router.get("/performance")
async def get_performance_attribution(
    symbol: Optional[str] = None,
    strategy_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Compute performance breakdown across market, session, and regime."""
    agent = JournalAgent(db_session=db)
    trades = await agent.get_trades(symbol=symbol, strategy_id=strategy_id, limit=500)
    return performance_agent.analyze_performance(trades)
