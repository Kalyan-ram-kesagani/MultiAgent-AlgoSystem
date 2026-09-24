"""Shared deterministic technical indicators computed via NumPy and Pandas."""
from typing import List, Tuple
import numpy as np
import pandas as pd


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    return series.rolling(window=period).mean()


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range (ATR)."""
    high = df["high"]
    low = df["low"]
    close_prev = df["close"].shift(1)

    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index (RSI)."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / (avg_loss + 1e-9)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


def identify_swing_levels(
    df: pd.DataFrame, lookback: int = 5
) -> Tuple[pd.Series, pd.Series]:
    """Identify deterministic Swing High and Swing Low pivot points."""
    swing_highs = pd.Series(index=df.index, dtype=float)
    swing_lows = pd.Series(index=df.index, dtype=float)

    for i in range(lookback, len(df) - lookback):
        window_highs = df["high"].iloc[i - lookback : i + lookback + 1]
        window_lows = df["low"].iloc[i - lookback : i + lookback + 1]

        if df["high"].iloc[i] == window_highs.max():
            swing_highs.iloc[i] = df["high"].iloc[i]
        if df["low"].iloc[i] == window_lows.min():
            swing_lows.iloc[i] = df["low"].iloc[i]

    return swing_highs.ffill(), swing_lows.ffill()
