"""Pydantic schemas for market data and data quality."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BarData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    spread: float = 0.0
    source: str = "MT5"
    quality_status: str = "VALIDATED"


class BarDataBatch(BaseModel):
    bars: List[BarData]


class DataFetchRequest(BaseModel):
    symbol: str
    timeframe: str = "H1"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    count: int = Field(default=500, le=10000)


class DataQualityIssue(BaseModel):
    issue_type: str
    symbol: str
    timeframe: str
    timestamp: Optional[datetime] = None
    details: str


class DataValidationReport(BaseModel):
    symbol: str
    timeframe: str
    total_bars: int
    valid_bars: int
    issues_detected: int
    issues: List[DataQualityIssue] = []
    quality_status: str
