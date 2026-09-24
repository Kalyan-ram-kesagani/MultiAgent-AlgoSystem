"""Market Data Ingestion, Retrieval, and Validation API endpoints."""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.data.data_agent import DataAgent
from backend.app.database.session import get_db
from backend.app.schemas.market_data import (
    BarData,
    BarDataBatch,
    DataFetchRequest,
    DataValidationReport,
)

router = APIRouter(prefix="/data", tags=["Market Data"])


@router.post("/validate", response_model=DataValidationReport)
def validate_market_data(batch: BarDataBatch):
    """Audit market bars for integrity, missing candles, abnormal spikes, and spread anomalies."""
    if not batch.bars:
        return DataValidationReport(
            symbol="UNKNOWN",
            timeframe="H1",
            total_bars=0,
            valid_bars=0,
            issues_detected=0,
            quality_status="REJECTED",
        )
    agent = DataAgent()
    return agent.validate_bars(
        symbol=batch.bars[0].symbol,
        timeframe=batch.bars[0].timeframe,
        bars=batch.bars,
    )


@router.get("/synthetic/{symbol}", response_model=List[BarData])
def get_synthetic_data(symbol: str = "EURUSD", timeframe: str = "H1", count: int = 200):
    """Generate realistic test market bars for offline development and testing."""
    return DataAgent.generate_synthetic_data(symbol=symbol, timeframe=timeframe, num_bars=count)


@router.post("/store")
async def store_bars(batch: BarDataBatch, db: AsyncSession = Depends(get_db)):
    """Persist validated market bars without overwriting historical records."""
    agent = DataAgent(db_session=db)
    inserted = await agent.store_bars(batch.bars)
    return {"inserted_bars": inserted}
