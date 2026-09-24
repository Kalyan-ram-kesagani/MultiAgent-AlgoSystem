"""Unit tests for deterministic strategy indicators and signal logic."""
import pandas as pd
import pytest
from backend.app.agents.data.data_agent import DataAgent
from strategies.shared.indicators import calculate_atr, calculate_ema, calculate_rsi
from strategies.strategy_v1.trend_pullback import StrategyV1


def test_indicator_calculations():
    """Verify indicators compute cleanly without NaN explosions."""
    bars = DataAgent.generate_synthetic_data("EURUSD", "H1", num_bars=100)
    df = pd.DataFrame([b.model_dump() for b in bars])

    ema20 = calculate_ema(df["close"], 20)
    assert len(ema20) == 100
    assert not ema20.iloc[-1] != ema20.iloc[-1]  # not NaN

    atr = calculate_atr(df, 14)
    assert len(atr) == 100
    assert atr.iloc[-1] > 0

    rsi = calculate_rsi(df["close"], 14)
    assert len(rsi) == 100
    assert 0 <= rsi.dropna().iloc[-1] <= 100


def test_strategy_v1_signal_generation():
    """Verify StrategyV1 emits signals with complete deterministic SL and TP."""
    strategy = StrategyV1()
    bars = DataAgent.generate_synthetic_data("EURUSD", "H1", num_bars=300)
    df = pd.DataFrame([b.model_dump() for b in bars])

    signals = strategy.generate_signals(df)
    assert isinstance(signals, list)

    for sig in signals:
        assert sig.strategy_id == "strategy_v1"
        assert sig.direction in ["BUY", "SELL"]
        assert sig.suggested_sl > 0
        assert sig.suggested_tp > 0
        if sig.direction == "BUY":
            assert sig.suggested_sl < sig.suggested_entry < sig.suggested_tp
        else:
            assert sig.suggested_tp < sig.suggested_entry < sig.suggested_sl
