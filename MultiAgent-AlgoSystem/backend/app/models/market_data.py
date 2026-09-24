"""Market data and quality audit models."""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database.base import Base, TimestampMixin


class MarketData(Base, TimestampMixin):
    """OHLCV market bar data."""
    __tablename__ = "market_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    spread: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    source: Mapped[str] = mapped_column(String(64), default="MT5", nullable=False)
    quality_status: Mapped[str] = mapped_column(String(32), default="VALIDATED", nullable=False)

    __table_args__ = (
        Index("idx_symbol_tf_time", "symbol", "timeframe", "timestamp", unique=True),
    )


class DataQualityAudit(Base, TimestampMixin):
    """Data validation and quality exception log."""
    __tablename__ = "data_quality_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(16), nullable=False)
    issue_type: Mapped[str] = mapped_column(String(64), nullable=False)  # MISSING_BAR, BAD_TIMESTAMP, ABNORMAL_PRICE, SPREAD_ANOMALY
    details: Mapped[str] = mapped_column(Text, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved: Mapped[bool] = mapped_column(default=False)
