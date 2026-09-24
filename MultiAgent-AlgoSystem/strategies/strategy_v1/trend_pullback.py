"""Strategy v1 — Deterministic Trend-Pullback Strategy for EURUSD & XAUUSD."""
import uuid
from typing import Any, Dict, List, Optional
import pandas as pd
from backend.app.schemas.trading import SignalCreate
from strategies.shared.base_strategy import BaseStrategy, StrategyMetadata
from strategies.shared.indicators import calculate_atr, calculate_ema, calculate_rsi, identify_swing_levels


class StrategyV1(BaseStrategy):
    """
    Deterministic Trend Pullback Strategy.
    
    Rules:
    BUY:
      1. EMA_fast > EMA_slow (Upward Trend)
      2. Previous Close pulled back near EMA_fast (<= atr_pullback_multiplier * ATR)
      3. Current Close > Current Open (Bullish candle confirmation)
      4. Current Close > EMA_fast
      5. RSI between 45 and 65 (Not overbought)
    
    SELL:
      1. EMA_fast < EMA_slow (Downward Trend)
      2. Previous Close pulled back near EMA_fast (<= atr_pullback_multiplier * ATR)
      3. Current Close < Current Open (Bearish candle confirmation)
      4. Current Close < EMA_fast
      5. RSI between 35 and 55 (Not oversold)
    
    Stop Loss:
      BUY: Swing Low - (atr_stop_multiplier * ATR)
      SELL: Swing High + (atr_stop_multiplier * ATR)
    
    Take Profit:
      Entry + (Reward_Risk_Ratio * Stop_Distance)
    """

    def get_metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            strategy_id="strategy_v1",
            version="1.0.0",
            name="Trend Pullback Confirmation",
            description="Deterministic trend-following pullback strategy using EMA, ATR, and RSI filters.",
            author="System Architect",
            timeframe="H1",
            supported_symbols=["EURUSD", "XAUUSD", "GBPUSD"],
        )

    def get_default_parameters(self) -> Dict[str, Any]:
        return {
            "ema_fast": 20,
            "ema_slow": 50,
            "atr_period": 14,
            "rsi_period": 14,
            "swing_lookback": 5,
            "atr_stop_multiplier": 1.5,
            "reward_risk_ratio": 2.0,
            "min_stop_distance": 0.0010,  # 10 pips min for FX
        }

    def generate_signals(self, df: pd.DataFrame) -> List[SignalCreate]:
        if len(df) < max(self.params["ema_slow"], self.params["atr_period"]) + 10:
            return []

        df = df.copy()
        df["ema_fast"] = calculate_ema(df["close"], self.params["ema_fast"])
        df["ema_slow"] = calculate_ema(df["close"], self.params["ema_slow"])
        df["atr"] = calculate_atr(df, self.params["atr_period"])
        df["rsi"] = calculate_rsi(df["close"], self.params["rsi_period"])
        swing_high, swing_low = identify_swing_levels(df, self.params["swing_lookback"])
        df["swing_high"] = swing_high
        df["swing_low"] = swing_low

        signals: List[SignalCreate] = []

        # Iterate over bars (leaving lookback for indicators)
        start_idx = max(self.params["ema_slow"], self.params["atr_period"]) + 1

        for i in range(start_idx, len(df)):
            curr = df.iloc[i]
            prev = df.iloc[i - 1]

            symbol = curr["symbol"] if "symbol" in curr else "EURUSD"
            timeframe = curr["timeframe"] if "timeframe" in curr else "H1"
            timestamp = curr["timestamp"]
            close_price = curr["close"]
            atr = curr["atr"]

            if pd.isna(atr) or atr <= 0:
                continue

            # BUY CONDITION
            is_uptrend = curr["ema_fast"] > curr["ema_slow"]
            is_bullish_bar = curr["close"] > curr["open"]
            was_pullback = abs(prev["close"] - prev["ema_fast"]) <= (atr * 1.0)
            is_above_fast = curr["close"] > curr["ema_fast"]
            is_rsi_buy = 40.0 <= curr["rsi"] <= 68.0

            if is_uptrend and is_bullish_bar and was_pullback and is_above_fast and is_rsi_buy:
                sl_ref = curr["swing_low"] if not pd.isna(curr["swing_low"]) else (curr["low"] - atr)
                stop_loss = round(sl_ref - (atr * self.params["atr_stop_multiplier"]), 5)
                stop_dist = max(close_price - stop_loss, self.params["min_stop_distance"])
                stop_loss = round(close_price - stop_dist, 5)
                take_profit = round(close_price + (stop_dist * self.params["reward_risk_ratio"]), 5)

                signals.append(
                    SignalCreate(
                        strategy_id="strategy_v1",
                        strategy_version="1.0.0",
                        symbol=symbol,
                        direction="BUY",
                        timeframe=timeframe,
                        timestamp=timestamp,
                        suggested_entry=close_price,
                        suggested_sl=stop_loss,
                        suggested_tp=take_profit,
                        risk_points=stop_dist,
                        market_regime="TREND_UP",
                    )
                )

            # SELL CONDITION
            is_downtrend = curr["ema_fast"] < curr["ema_slow"]
            is_bearish_bar = curr["close"] < curr["open"]
            was_pullback_sell = abs(prev["close"] - prev["ema_fast"]) <= (atr * 1.0)
            is_below_fast = curr["close"] < curr["ema_fast"]
            is_rsi_sell = 32.0 <= curr["rsi"] <= 60.0

            if is_downtrend and is_bearish_bar and was_pullback_sell and is_below_fast and is_rsi_sell:
                sl_ref = curr["swing_high"] if not pd.isna(curr["swing_high"]) else (curr["high"] + atr)
                stop_loss = round(sl_ref + (atr * self.params["atr_stop_multiplier"]), 5)
                stop_dist = max(stop_loss - close_price, self.params["min_stop_distance"])
                stop_loss = round(close_price + stop_dist, 5)
                take_profit = round(close_price - (stop_dist * self.params["reward_risk_ratio"]), 5)

                signals.append(
                    SignalCreate(
                        strategy_id="strategy_v1",
                        strategy_version="1.0.0",
                        symbol=symbol,
                        direction="SELL",
                        timeframe=timeframe,
                        timestamp=timestamp,
                        suggested_entry=close_price,
                        suggested_sl=stop_loss,
                        suggested_tp=take_profit,
                        risk_points=stop_dist,
                        market_regime="TREND_DOWN",
                    )
                )

        return signals
