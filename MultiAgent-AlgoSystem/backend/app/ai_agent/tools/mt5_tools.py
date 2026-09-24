"""MetaTrader 5 Account, Position, and Trade Inspection Tools for AI Agent."""
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional

from trading.execution.mt5_client import mt5_client


def get_mt5_account() -> str:
    """Fetch current MT5 demo account equity, balance, margin, leverage, and currency."""
    info = mt5_client.get_account_info()
    return json.dumps({
        "login": info.get("login"),
        "server": info.get("server"),
        "balance": info.get("balance", 0.0),
        "equity": info.get("equity", 0.0),
        "margin": info.get("margin", 0.0),
        "free_margin": info.get("free_margin", 0.0),
        "margin_level_pct": info.get("margin_level", 0.0),
        "leverage": info.get("leverage", 100),
        "currency": info.get("currency", "USD"),
        "trade_mode": "DEMO",
        "connected": mt5_client.connected,
    }, indent=2)


def get_mt5_positions() -> str:
    """Fetch all open positions currently held in the MT5 account with unrealized PnL."""
    positions = mt5_client.get_open_positions()
    res = []
    for p in positions:
        res.append({
            "ticket": p.get("ticket"),
            "symbol": p.get("symbol"),
            "side": p.get("type", "BUY"),
            "volume": p.get("volume"),
            "open_price": p.get("price_open"),
            "current_price": p.get("price_current"),
            "sl": p.get("sl"),
            "tp": p.get("tp"),
            "unrealized_pnl": p.get("profit"),
            "open_time": p.get("time"),
        })
    return json.dumps({"count": len(res), "positions": res}, indent=2)


def get_mt5_orders() -> str:
    """Fetch pending limit or stop orders currently registered on the MT5 terminal."""
    status = mt5_client.get_realtime_terminal_status()
    return json.dumps({
        "pending_orders": status.get("pending_orders", 0),
        "connected": status.get("connected", False),
        "gateway_mode": status.get("gateway_mode", "SIMULATION"),
    }, indent=2)


def get_mt5_trade_history(days: int = 30) -> str:
    """Fetch historical closed deals directly from MT5 terminal for the specified period."""
    safe_days = max(1, min(days, 365))
    raw_deals = mt5_client.get_history_deals(days=safe_days)
    
    deals_data = []
    for d in raw_deals[:50]:  # Cap at 50 most recent deals
        symbol = getattr(d, "symbol", "")
        if not symbol:
            continue
        deals_data.append({
            "ticket": getattr(d, "ticket", 0),
            "order": getattr(d, "order", 0),
            "symbol": symbol,
            "type": "BUY" if getattr(d, "type", 0) == 0 else "SELL",
            "volume": getattr(d, "volume", 0.0),
            "price": getattr(d, "price", 0.0),
            "profit": getattr(d, "profit", 0.0),
            "commission": getattr(d, "commission", 0.0),
            "swap": getattr(d, "swap", 0.0),
            "entry": getattr(d, "entry", 0),
            "magic": getattr(d, "magic", 0),
            "comment": getattr(d, "comment", ""),
        })
    return json.dumps({"days": safe_days, "count": len(deals_data), "deals": deals_data}, indent=2)


def get_mt5_symbol_info(symbol: str) -> str:
    """Fetch broker specifications for a symbol: contract size, digits, point size, tick value, and stops level."""
    clean_sym = symbol.upper().strip()
    prices = mt5_client.get_symbol_price(clean_sym)
    contract_size = 100.0 if "XAU" in clean_sym else 100000.0
    digits = 3 if "JPY" in clean_sym or "XAU" in clean_sym else 5
    point = 0.001 if digits == 3 else 0.00001
    
    return json.dumps({
        "symbol": clean_sym,
        "digits": digits,
        "point": point,
        "contract_size": contract_size,
        "current_bid": prices.get("bid", 0.0),
        "current_ask": prices.get("ask", 0.0),
        "spread_pips": prices.get("spread_pips", 1.5),
        "trade_mode": "DEMO_ENABLED",
    }, indent=2)
