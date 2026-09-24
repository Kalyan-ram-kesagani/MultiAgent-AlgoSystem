"""Agent #3 — Data Agent: Ingestion, Validation, Cleaning, and Storage."""
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.constants import DataQualityStatus, TimeFrame
from backend.app.core.logging import logger
from backend.app.models.market_data import DataQualityAudit, MarketData
from backend.app.schemas.market_data import (
    BarData,
    DataQualityIssue,
    DataValidationReport,
)


class DataAgent:
    """Acquires, validates, stores, and audits market data."""

    TIMEFRAME_DELTAS = {
        TimeFrame.M1: timedelta(minutes=1),
        TimeFrame.M5: timedelta(minutes=5),
        TimeFrame.M15: timedelta(minutes=15),
        TimeFrame.M30: timedelta(minutes=30),
        TimeFrame.H1: timedelta(hours=1),
        TimeFrame.H4: timedelta(hours=4),
        TimeFrame.D1: timedelta(days=1),
    }

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session

    def validate_bars(
        self,
        symbol: str,
        timeframe: str,
        bars: List[BarData],
    ) -> DataValidationReport:
        """Thoroughly validate OHLCV series for integrity, sequence, and outliers."""
        if not bars:
            return DataValidationReport(
                symbol=symbol,
                timeframe=timeframe,
                total_bars=0,
                valid_bars=0,
                issues_detected=0,
                issues=[],
                quality_status=DataQualityStatus.REJECTED,
            )

        # Sort bars chronologically
        sorted_bars = sorted(bars, key=lambda b: b.timestamp)
        issues: List[DataQualityIssue] = []

        seen_timestamps = set()
        expected_delta = self.TIMEFRAME_DELTAS.get(TimeFrame(timeframe), timedelta(hours=1))

        # Rolling volatility estimation for price spike filtering
        price_ranges = []

        for i, bar in enumerate(sorted_bars):
            # 1. Duplicate check
            if bar.timestamp in seen_timestamps:
                issues.append(
                    DataQualityIssue(
                        issue_type="DUPLICATE_TIMESTAMP",
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=bar.timestamp,
                        details=f"Duplicate candle timestamp {bar.timestamp}",
                    )
                )
            seen_timestamps.add(bar.timestamp)

            # 2. Inverted candle or non-positive price check
            if bar.open <= 0 or bar.high <= 0 or bar.low <= 0 or bar.close <= 0:
                issues.append(
                    DataQualityIssue(
                        issue_type="NON_POSITIVE_PRICE",
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=bar.timestamp,
                        details=f"Bar has price <= 0: O={bar.open}, H={bar.high}, L={bar.low}, C={bar.close}",
                    )
                )

            if bar.high < bar.low:
                issues.append(
                    DataQualityIssue(
                        issue_type="INVERTED_HIGH_LOW",
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=bar.timestamp,
                        details=f"High {bar.high} is less than Low {bar.low}",
                    )
                )

            if bar.high < max(bar.open, bar.close) or bar.low > min(bar.open, bar.close):
                issues.append(
                    DataQualityIssue(
                        issue_type="OHLC_MISMATCH",
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=bar.timestamp,
                        details=f"Candle body exceeds bounds: O={bar.open}, H={bar.high}, L={bar.low}, C={bar.close}",
                    )
                )

            # 3. Negative spread check
            if bar.spread < 0:
                issues.append(
                    DataQualityIssue(
                        issue_type="NEGATIVE_SPREAD",
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=bar.timestamp,
                        details=f"Spread is negative: {bar.spread}",
                    )
                )

            # 4. Cadence & Gap detection (excluding weekends)
            if i > 0:
                prev_bar = sorted_bars[i - 1]
                gap = bar.timestamp - prev_bar.timestamp
                # Check for gap greater than expected, skipping Friday evening to Sunday night
                is_weekend = (
                    prev_bar.timestamp.weekday() == 4 and bar.timestamp.weekday() == 6
                ) or (prev_bar.timestamp.weekday() == 4 and bar.timestamp.weekday() == 0)

                if gap > expected_delta * 1.5 and not is_weekend:
                    missing_bars = int(gap.total_seconds() // expected_delta.total_seconds()) - 1
                    if missing_bars > 0:
                        issues.append(
                            DataQualityIssue(
                                issue_type="MISSING_CANDLES_GAP",
                                symbol=symbol,
                                timeframe=timeframe,
                                timestamp=bar.timestamp,
                                details=f"Gap of {gap} detected. Approximately {missing_bars} missing bars between {prev_bar.timestamp} and {bar.timestamp}",
                            )
                        )

            price_ranges.append(bar.high - bar.low)

        # 5. Extreme spike check (bar range > 10x median range)
        if len(price_ranges) >= 10:
            median_range = np.median(price_ranges)
            if median_range > 0:
                for bar, rng in zip(sorted_bars, price_ranges):
                    if rng > 10 * median_range:
                        issues.append(
                            DataQualityIssue(
                                issue_type="ABNORMAL_PRICE_SPIKE",
                                symbol=symbol,
                                timeframe=timeframe,
                                timestamp=bar.timestamp,
                                details=f"Range {rng:.5f} is > 10x median range {median_range:.5f}",
                            )
                        )

        # Determine overall quality
        critical_issues = [
            iss for iss in issues if iss.issue_type in ["INVERTED_HIGH_LOW", "NON_POSITIVE_PRICE"]
        ]
        if critical_issues:
            quality_status = DataQualityStatus.REJECTED
        elif issues:
            quality_status = DataQualityStatus.FLAGGED
        else:
            quality_status = DataQualityStatus.VALIDATED

        return DataValidationReport(
            symbol=symbol,
            timeframe=timeframe,
            total_bars=len(bars),
            valid_bars=len(bars) - len(critical_issues),
            issues_detected=len(issues),
            issues=issues,
            quality_status=quality_status,
        )

    async def store_bars(self, bars: List[BarData]) -> int:
        """Store validated bars idempotently without overwriting historical data."""
        if not self.db or not bars:
            return 0

        inserted_count = 0
        for bar in bars:
            # Check existing entry
            stmt = select(MarketData).where(
                MarketData.symbol == bar.symbol,
                MarketData.timeframe == bar.timeframe,
                MarketData.timestamp == bar.timestamp,
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                record = MarketData(
                    symbol=bar.symbol,
                    timeframe=bar.timeframe,
                    timestamp=bar.timestamp,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                    spread=bar.spread,
                    source=bar.source,
                    quality_status=bar.quality_status,
                )
                self.db.add(record)
                inserted_count += 1

        await self.db.commit()
        return inserted_count

    @staticmethod
    def generate_synthetic_data(
        symbol: str = "EURUSD",
        timeframe: str = "H1",
        num_bars: int = 500,
        start_price: float = 1.0850,
        volatility: float = 0.0008,
        seed: int = 42,
    ) -> List[BarData]:
        """Generate realistic synthetic OHLCV bars with random walk & trends for testing."""
        np.random.seed(seed)
        bars: List[BarData] = []
        current_time = datetime.now(timezone.utc) - timedelta(hours=num_bars)
        price = start_price

        for i in range(num_bars):
            drift = np.sin(i / 20.0) * 0.0001
            change = np.random.normal(drift, volatility)
            open_p = price
            close_p = open_p + change

            wick_high = abs(np.random.normal(0, volatility * 0.5))
            wick_low = abs(np.random.normal(0, volatility * 0.5))

            high_p = max(open_p, close_p) + wick_high
            low_p = min(open_p, close_p) - wick_low
            volume = float(np.random.randint(50, 1500))
            spread = 1.2 + np.random.uniform(0.0, 0.4)

            bars.append(
                BarData(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=current_time,
                    open=round(open_p, 5),
                    high=round(high_p, 5),
                    low=round(low_p, 5),
                    close=round(close_p, 5),
                    volume=volume,
                    spread=round(spread, 1),
                    source="SYNTHETIC_GENERATOR",
                    quality_status="VALIDATED",
                )
            )
            price = close_p
            current_time += timedelta(hours=1)

        return bars
