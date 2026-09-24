"""Market Data Tools for AI Agent."""
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from backend.app.agents.journal.journal_agent import JournalAgent
from trading.execution.mt5_client import mt5_client


def get_market_data() -> str:
    """Fetch consolidated market summary across EURUSD, GBPUSD, and XAUUSD with current bid, ask, and spread."""
    symbols = ["EURUSD", "GBPUSD", "XAUUSD", "USDJPY"]
    data = {}
    for sym in symbols:
        prices = mt5_client.get_symbol_price(sym)
        data[sym] = {
            "bid": prices.get("bid", 0.0),
            "ask": prices.get("ask", 0.0),
            "spread_pips": prices.get("spread_pips", 0.0),
            "time": datetime.now(timezone.utc).isoformat(),
        }
    return json.dumps(data, indent=2)


def get_candles(symbol: str, timeframe: str = "H1", limit: int = 50) -> str:
    """
    Fetch recent OHLCV candlestick bars for a given symbol and timeframe.
    Timeframe options: M15, H1, H4, D1.
    """
    clean_sym = symbol.upper().strip()
    safe_limit = max(10, min(limit, 200))
    candles = mt5_client.get_historical_candles(symbol=clean_sym, timeframe=timeframe, count=safe_limit)
    
    formatted = []
    for c in candles:
        formatted.append({
            "time": c.get("time", ""),
            "open": round(c.get("open", 0.0), 5),
            "high": round(c.get("high", 0.0), 5),
            "low": round(c.get("low", 0.0), 5),
            "close": round(c.get("close", 0.0), 5),
            "volume": c.get("volume", 0),
        })
    return json.dumps({"symbol": clean_sym, "timeframe": timeframe, "count": len(formatted), "candles": formatted}, indent=2)


def get_current_price(symbol: str) -> str:
    """Get the latest real-time bid, ask, and spread for a specific symbol."""
    clean_sym = symbol.upper().strip()
    prices = mt5_client.get_symbol_price(clean_sym)
    return json.dumps({
        "symbol": clean_sym,
        "bid": prices.get("bid", 0.0),
        "ask": prices.get("ask", 0.0),
        "spread_pips": prices.get("spread_pips", 0.0),
        "freshness": "REAL_TIME",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, indent=2)


def get_spread(symbol: str) -> str:
    """Get current spread in pips and check if it is within institutional risk thresholds (<5.0 pips)."""
    clean_sym = symbol.upper().strip()
    prices = mt5_client.get_symbol_price(clean_sym)
    spread = prices.get("spread_pips", 1.5)
    is_acceptable = spread <= 5.0
    return json.dumps({
        "symbol": clean_sym,
        "spread_pips": spread,
        "max_allowed_pips": 5.0,
        "acceptable_for_trading": is_acceptable,
    }, indent=2)


def get_market_session() -> str:
    """Determine currently active trading session (Asian, London, New York, or Overlap)."""
    now = datetime.now(timezone.utc)
    session_name = JournalAgent.identify_session(now)
    hour = now.hour
    return json.dumps({
        "current_session": session_name,
        "utc_time": now.isoformat(),
        "utc_hour": hour,
        "high_liquidity_window": session_name in ("LONDON", "NEW_YORK", "LONDON_NY_OVERLAP"),
    }, indent=2)


def get_market_regime(symbol: str) -> str:
    """
    Analyze recent price action and volatility to identify market regime:
    TRENDING_BULL, TRENDING_BEAR, RANGING, or HIGH_VOLATILITY.
    """
    clean_sym = symbol.upper().strip()
    candles = mt5_client.get_historical_candles(symbol=clean_sym, timeframe="H1", count=60)
    if len(candles) < 20:
        return json.dumps({"symbol": clean_sym, "regime": "UNKNOWN", "reason": "INSUFFICIENT DATA"}, indent=2)

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    # Calculate 20-period and 50-period EMAs
    ema20 = sum(closes[-20:]) / 20.0
    ema50 = sum(closes[-50:]) / 50.0 if len(closes) >= 50 else ema20
    current_price = closes[-1]

    # Approximate ATR (14)
    trs = [max(h - l, abs(h - c_prev), abs(l - c_prev)) for h, l, c_prev in zip(highs[-14:], lows[-14:], closes[-15:-1])]
    atr = sum(trs) / len(trs) if trs else 0.001
    atr_pct = (atr / current_price) * 100

    if current_price > ema20 > ema50:
        regime = "TRENDING_BULL"
        desc = "Price above EMA20 and EMA50; upward momentum."
    elif current_price < ema20 < ema50:
        regime = "TRENDING_BEAR"
        desc = "Price below EMA20 and EMA50; downward momentum."
    elif atr_pct > 1.0:
        regime = "HIGH_VOLATILITY"
        desc = f"ATR is {atr_pct:.2f}% of price; elevated volatility."
    else:
        regime = "RANGING"
        desc = "Price oscillating between EMAs; mean-reverting environment."

    return json.dumps({
        "symbol": clean_sym,
        "regime": regime,
        "current_price": current_price,
        "ema20": round(ema20, 5),
        "ema50": round(ema50, 5),
        "atr": round(atr, 5),
        "description": desc,
    }, indent=2)
