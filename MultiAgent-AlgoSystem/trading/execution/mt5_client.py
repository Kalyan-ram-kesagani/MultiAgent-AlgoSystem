"""MetaTrader 5 Python Gateway wrapper with resilient connection management, demo validation, and sandbox fallback."""
from datetime import datetime, timezone
import math
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from backend.app.core.config import settings
from backend.app.core.logging import logger

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    mt5 = None
    MT5_AVAILABLE = False


# Comprehensive MT5 Trade Return Code Mapping
RETCODE_DESCRIPTIONS: Dict[int, str] = {
    10004: "REQUOTE: Price quote changed during order processing",
    10006: "REJECTED: Broker rejected the order",
    10007: "CANCELLED: Order cancelled by client or server",
    10008: "PLACED: Order placed in queue",
    10009: "DONE: Trade deal executed successfully",
    10010: "DONE_PARTIAL: Order executed partially",
    10011: "ERROR: General order processing error",
    10012: "TIMEOUT: Request timed out at broker",
    10013: "INVALID: Invalid trade request format",
    10014: "INVALID_VOLUME: Invalid order volume",
    10015: "INVALID_PRICE: Invalid order price",
    10016: "INVALID_STOPS: Invalid Stop Loss or Take Profit levels",
    10017: "TRADE_DISABLED: Trading is disabled for this account/broker",
    10018: "MARKET_CLOSED: Market is currently closed",
    10019: "NO_MONEY: Insufficient margin/equity to place order",
    10020: "PRICE_CHANGED: Prices have changed since quote request",
    10021: "OFF_QUOTES: No quotes available from broker",
    10022: "BROKER_BUSY: Broker trade server is busy",
    10024: "TOO_MANY_REQUESTS: Frequent requests throttled",
    10026: "AUTOTRADING_DISABLED_SERVER: Auto-trading disabled by broker server",
    10027: "AUTOTRADING_DISABLED_CLIENT: Auto-trading disabled in terminal settings",
    10030: "UNSUPPORTED_FILLING_MODE: Requested order filling mode unsupported",
    10031: "CONNECTION_LOST: Connection with trade server lost",
}


class MT5SafetyException(Exception):
    """Raised when an MT5 safety lock or environment boundary is violated."""
    pass


class MT5Client:
    """Gateway interface for MetaTrader 5 terminal interaction supporting SANDBOX, DEMO, and LIVE modes."""

    def __init__(self):
        self.connected: bool = False
        self.is_simulation_mode: bool = False
        self.mode: str = settings.ENVIRONMENT.upper()
        self.account_id: Optional[int] = None
        self.server_name: Optional[str] = None
        self.trade_mode_name: str = "SIMULATION"

    def connect(self) -> bool:
        """
        Establish connection to MT5 terminal based on configured environment mode:
        - SANDBOX: Always uses safe in-memory simulation gateway.
        - DEMO: Connects to real MT5 terminal, enforces ACCOUNT_TRADE_MODE_DEMO.
        - LIVE: Strictly guarded; requires explicit acknowledgment and verification.
        """
        self.mode = settings.ENVIRONMENT.upper()

        # 1. SANDBOX MODE: Pure simulation
        if settings.is_sandbox:
            logger.info("Initializing in SANDBOX Simulation Gateway (no live orders will be placed).")
            self.is_simulation_mode = True
            self.connected = False  # False for native MT5 connection; simulation active
            self.trade_mode_name = "SANDBOX_SIMULATION"
            return True

        # 2. DEMO or LIVE MODE requires MetaTrader5 library
        if not MT5_AVAILABLE:
            logger.error("MetaTrader5 python package not available. Falling back to SANDBOX simulation.")
            self.is_simulation_mode = True
            self.connected = False
            self.trade_mode_name = "SANDBOX_FALLBACK"
            return True

        # Helper: check if terminal64.exe process is actually running
        terminal_running = False
        try:
            import subprocess
            tasklist_path = r"C:\Windows\System32\tasklist.exe"
            if os.path.exists(tasklist_path):
                out = subprocess.run([tasklist_path, "/FI", "IMAGENAME eq terminal64.exe", "/NH"], capture_output=True, text=True, timeout=2)
                terminal_running = "terminal64.exe" in out.stdout.lower()
        except Exception:
            terminal_running = False

        # If terminal process is not active and no password was provided in .env, default gracefully to simulation
        has_password = bool(settings.MT5_PASSWORD and settings.MT5_PASSWORD.strip())
        if not terminal_running and not has_password:
            logger.info("MT5 terminal64.exe process is not currently active and MT5_PASSWORD is empty. Operating in safe Sandbox Simulation Gateway.")
            self.is_simulation_mode = True
            self.connected = False
            self.trade_mode_name = "SANDBOX_SIMULATION"
            return True

        # Build initialization arguments with fail-fast timeout (max 5s)
        init_timeout = min(settings.MT5_TIMEOUT_MS, 5000)
        init_kwargs: Dict[str, Any] = {"timeout": init_timeout}
        if settings.MT5_PATH and os.path.exists(settings.MT5_PATH):
            init_kwargs["path"] = settings.MT5_PATH
        if settings.MT5_LOGIN:
            init_kwargs["login"] = settings.MT5_LOGIN
        if settings.MT5_PASSWORD and settings.MT5_PASSWORD.strip():
            init_kwargs["password"] = settings.MT5_PASSWORD.strip()
        if settings.MT5_SERVER:
            init_kwargs["server"] = settings.MT5_SERVER

        # Attempt connection
        initialized = mt5.initialize(**init_kwargs)
        if not initialized:
            # Fallback attempt without explicit credentials (attaches to active open terminal session)
            logger.info("Attempting attach to currently active MT5 terminal session...")
            initialized = mt5.initialize(timeout=init_timeout)

        if not initialized:
            err = mt5.last_error()
            logger.error(
                f"MT5 initialization failed: code={err[0]}, message='{err[1]}'. Defaulting to safe simulation.",
                extra={"error_code": err[0], "error_msg": err[1]},
            )
            self.is_simulation_mode = True
            self.connected = False
            return False

        # Retrieve account and terminal metadata
        acc_info = mt5.account_info()
        term_info = mt5.terminal_info()

        if acc_info is None or term_info is None:
            logger.error("Connected to MT5 terminal, but failed to retrieve account/terminal info.")
            self.connected = False
            return False

        self.account_id = acc_info.login
        self.server_name = acc_info.server
        self.connected = True
        self.is_simulation_mode = False

        # Map trade_mode (0=DEMO, 1=CONTEST, 2=REAL)
        trade_mode_val = getattr(acc_info, "trade_mode", 0)
        mode_names = {0: "DEMO", 1: "CONTEST", 2: "REAL"}
        self.trade_mode_name = mode_names.get(trade_mode_val, f"UNKNOWN({trade_mode_val})")

        # 3. SAFETY CHECKS: Prevent cross-environment order leaks
        if settings.is_demo:
            if trade_mode_val == 2:  # ACCOUNT_TRADE_MODE_REAL
                self.disconnect()
                raise MT5SafetyException(
                    "CRITICAL SAFETY VIOLATION: Environment is set to DEMO, but connected MT5 account is a REAL-MONEY account! "
                    "Connection terminated to protect funds. Switch terminal to a Demo account."
                )
            logger.info(
                f"Connected to MT5 DEMO Gateway successfully: Account={self.account_id}, Server='{self.server_name}', "
                f"Balance={acc_info.balance:.2f} {acc_info.currency}, Equity={acc_info.equity:.2f} {acc_info.currency}"
            )

        elif settings.is_live:
            # Require explicit confirmation gate
            if not settings.LIVE_TRADING_ACKNOWLEDGED:
                self.disconnect()
                raise MT5SafetyException(
                    "LIVE SAFETY GATE ACTIVE: Environment is set to LIVE, but LIVE_TRADING_ACKNOWLEDGED is False. "
                    "Live execution is hard-locked. Set LIVE_TRADING_ACKNOWLEDGED=true in .env only after full validation."
                )
            if trade_mode_val != 2:
                logger.warning(
                    f"System in LIVE mode but connected account trade_mode is {self.trade_mode_name}."
                )

        return True

    def disconnect(self) -> None:
        """Safely shut down connection with MT5 terminal."""
        if MT5_AVAILABLE and not self.is_simulation_mode:
            mt5.shutdown()
        self.connected = False
        self.account_id = None
        self.server_name = None

    def get_realtime_terminal_status(self) -> Dict[str, Any]:
        """Proactively query active MT5 terminal process and IPC socket."""
        if self.is_simulation_mode or not MT5_AVAILABLE:
            return {
                "native_mt5_available": MT5_AVAILABLE,
                "is_simulation_mode": True,
                "terminal_connected": False,
                "trade_allowed": True,
                "ping_ms": 0.1,
            }

        try:
            t0 = time.perf_counter()
            term_info = mt5.terminal_info()
            ping_ms = round((time.perf_counter() - t0) * 1000, 2)
            if term_info is None:
                self.connected = False
                return {
                    "native_mt5_available": True,
                    "is_simulation_mode": False,
                    "terminal_connected": False,
                    "trade_allowed": False,
                    "ping_ms": ping_ms,
                    "error": "terminal_info returned None",
                }

            is_connected = bool(term_info.connected)
            self.connected = is_connected
            return {
                "native_mt5_available": True,
                "is_simulation_mode": False,
                "terminal_connected": is_connected,
                "trade_allowed": bool(term_info.trade_allowed),
                "ping_ms": ping_ms,
                "build": getattr(term_info, "build", None),
            }
        except Exception as e:
            self.connected = False
            return {
                "native_mt5_available": True,
                "is_simulation_mode": False,
                "terminal_connected": False,
                "trade_allowed": False,
                "ping_ms": 999.0,
                "error": str(e),
            }

    def get_account_info(self) -> Dict[str, Any]:
        """Fetch account balance, equity, margin, leverage, and currency."""
        if self.is_simulation_mode or not MT5_AVAILABLE:
            return {
                "login": 99999999,
                "server": "Sandbox-Simulation",
                "trade_mode": "SANDBOX",
                "balance": 10000.0,
                "equity": 10000.0,
                "margin": 0.0,
                "free_margin": 10000.0,
                "currency": "USD",
                "leverage": 100,
                "trade_allowed": True,
            }

        info = mt5.account_info()
        if info is None:
            return {"error": "Failed to retrieve account info from MT5"}

        mode_names = {0: "DEMO", 1: "CONTEST", 2: "REAL"}
        return {
            "login": info.login,
            "server": info.server,
            "trade_mode": mode_names.get(info.trade_mode, str(info.trade_mode)),
            "balance": round(info.balance, 2),
            "equity": round(info.equity, 2),
            "margin": round(info.margin, 2),
            "free_margin": round(info.margin_free, 2),
            "currency": info.currency,
            "leverage": info.leverage,
            "trade_allowed": info.trade_allowed,
        }

    def validate_symbol(self, symbol: str) -> Dict[str, Any]:
        """Validate symbol exists, is tradeable, and enabled in Market Watch."""
        if self.is_simulation_mode or not MT5_AVAILABLE:
            return {
                "valid": True,
                "symbol": symbol,
                "visible": True,
                "trade_mode": "FULL",
                "volume_min": 0.01,
                "volume_max": 100.0,
                "volume_step": 0.01,
            }

        sym_info = mt5.symbol_info(symbol)
        if sym_info is None:
            return {"valid": False, "symbol": symbol, "error": f"Symbol '{symbol}' not found on broker server"}

        if not sym_info.visible:
            # Attempt to select symbol into Market Watch
            selected = mt5.symbol_select(symbol, True)
            if not selected:
                return {"valid": False, "symbol": symbol, "error": f"Failed to add '{symbol}' to Market Watch"}

        # Refresh symbol info
        sym_info = mt5.symbol_info(symbol)
        trade_modes = {
            0: "DISABLED",
            1: "LONGONLY",
            2: "SHORTONLY",
            3: "CLOSEONLY",
            4: "FULL",
        }

        return {
            "valid": True,
            "symbol": sym_info.name,
            "visible": sym_info.visible,
            "trade_mode": trade_modes.get(sym_info.trade_mode, "UNKNOWN"),
            "trade_allowed": sym_info.trade_mode == 4,  # SYMBOL_TRADE_MODE_FULL
            "volume_min": sym_info.volume_min,
            "volume_max": sym_info.volume_max,
            "volume_step": sym_info.volume_step,
            "digits": sym_info.digits,
            "point": sym_info.point,
            "filling_mode": sym_info.filling_mode,
        }

    def is_tick_fresh(self, symbol: str, max_age_seconds: Optional[float] = None) -> Tuple[bool, float, Optional[Dict[str, Any]]]:
        """
        Check if the latest market tick for a symbol is within the acceptable freshness threshold.
        Returns: (is_fresh, age_seconds, tick_data)
        """
        threshold = max_age_seconds if max_age_seconds is not None else settings.MAX_TICK_AGE_SECONDS

        if self.is_simulation_mode or not MT5_AVAILABLE:
            return True, 0.1, {"bid": 1.08500, "ask": 1.08515, "spread_pips": 1.5, "time": datetime.now(timezone.utc).timestamp()}

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            mt5.symbol_select(symbol, True)
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return False, 999.0, None

        # Compare tick time with current UTC epoch
        now_ts = datetime.now(timezone.utc).timestamp()
        tick_ts = tick.time
        age_seconds = max(0.0, now_ts - tick_ts)

        is_fresh = age_seconds <= threshold
        return is_fresh, round(age_seconds, 2), {
            "bid": tick.bid,
            "ask": tick.ask,
            "last": tick.last,
            "time": tick.time,
        }

    def get_symbol_price(self, symbol: str) -> Dict[str, float]:
        """Retrieve current bid, ask, and spread in pips for a symbol."""
        if self.is_simulation_mode or not MT5_AVAILABLE:
            base_prices = {"EURUSD": 1.08500, "XAUUSD": 2350.00, "GBPUSD": 1.27000}
            bid = base_prices.get(symbol.upper(), 1.0000)
            ask = bid + 0.00015
            spread_pips = (ask - bid) * 10000
            return {"bid": bid, "ask": ask, "spread_pips": round(spread_pips, 2)}

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            # Fallback attempt by selecting symbol
            mt5.symbol_select(symbol, True)
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return {"bid": 0.0, "ask": 0.0, "spread_pips": 0.0}

        info = mt5.symbol_info(symbol)
        digits = info.digits if info else 5
        multiplier = 100.0 if "XAU" in symbol.upper() or digits in (2, 3) else 10000.0
        spread_pips = (tick.ask - tick.bid) * multiplier
        return {
            "bid": round(tick.bid, digits),
            "ask": round(tick.ask, digits),
            "spread_pips": round(spread_pips, 2),
        }

    def get_historical_candles(
        self,
        symbol: str,
        timeframe: str = "H1",
        count: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch historical candle rates from MT5 terminal or high-fidelity fallback."""
        if not self.is_simulation_mode and MT5_AVAILABLE and self.connected:
            try:
                tf_map = {
                    "M1": getattr(mt5, "TIMEFRAME_M1", 1),
                    "M5": getattr(mt5, "TIMEFRAME_M5", 5),
                    "M15": getattr(mt5, "TIMEFRAME_M15", 15),
                    "M30": getattr(mt5, "TIMEFRAME_M30", 30),
                    "H1": getattr(mt5, "TIMEFRAME_H1", 16385),
                    "H4": getattr(mt5, "TIMEFRAME_H4", 16388),
                    "D1": getattr(mt5, "TIMEFRAME_D1", 16408),
                }
                tf = tf_map.get(timeframe.upper(), getattr(mt5, "TIMEFRAME_H1", 16385))
                rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
                if rates is not None and len(rates) > 0:
                    bars = []
                    for r in rates:
                        spread_val = float(r["spread"]) if "spread" in rates.dtype.names else 1.5
                        bars.append({
                            "time": datetime.fromtimestamp(r["time"], tz=timezone.utc).isoformat(),
                            "open": float(r["open"]),
                            "high": float(r["high"]),
                            "low": float(r["low"]),
                            "close": float(r["close"]),
                            "volume": float(r["tick_volume"]),
                            "spread": spread_val,
                        })
                    return bars
            except Exception as e:
                logger.warning(f"Error fetching MT5 candles: {e}, falling back to synthetic generator")

        # Fallback to realistic synthetic generator
        from backend.app.agents.data.data_agent import DataAgent
        synth = DataAgent.generate_synthetic_data(symbol=symbol, timeframe=timeframe, num_bars=count)
        return [
            {
                "time": b.timestamp.isoformat(),
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
                "spread": b.spread,
            }
            for b in synth
        ]

    def validate_volume(self, symbol: str, volume: float) -> Tuple[bool, float, str]:
        """
        Validate and quantize volume against broker's volume_min, volume_max, and volume_step.
        Also enforces DEMO_MAX_ORDER_LOTS safety ceiling.
        Returns: (is_valid, normalized_volume, reason)
        """
        if volume <= 0:
            return False, 0.0, "Volume must be strictly positive"

        # Check demo volume ceiling
        if settings.is_demo and volume > settings.DEMO_MAX_ORDER_LOTS:
            return False, volume, f"Requested volume {volume} exceeds DEMO safety ceiling of {settings.DEMO_MAX_ORDER_LOTS} lots"

        if self.is_simulation_mode or not MT5_AVAILABLE:
            return True, round(volume, 2), "OK"

        sym_info = mt5.symbol_info(symbol)
        if sym_info is None:
            return False, volume, f"Cannot validate volume: symbol '{symbol}' not found"

        vol_min = sym_info.volume_min
        vol_max = sym_info.volume_max
        vol_step = sym_info.volume_step

        if volume < vol_min:
            return False, vol_min, f"Volume {volume} is below minimum allowed ({vol_min})"
        if volume > vol_max:
            return False, vol_max, f"Volume {volume} is above maximum allowed ({vol_max})"

        # Quantize to nearest step
        steps = round((volume - vol_min) / vol_step)
        normalized = round(vol_min + (steps * vol_step), 4)

        return True, normalized, "OK"

    def _resolve_filling_mode(self, symbol_info: Any) -> int:
        """
        Dynamically determine supported MT5 order filling mode:
        Bitmask: 1 = FOK, 2 = IOC, 4 = RETURN.
        """
        if symbol_info is None or not hasattr(symbol_info, "filling_mode"):
            return mt5.ORDER_FILLING_IOC

        modes = symbol_info.filling_mode
        if modes & 2:  # IOC supported
            return mt5.ORDER_FILLING_IOC
        elif modes & 1:  # FOK supported (e.g. MetaQuotes-Demo EURUSD)
            return mt5.ORDER_FILLING_FOK
        elif modes & 4:  # RETURN supported
            return mt5.ORDER_FILLING_RETURN

        return mt5.ORDER_FILLING_IOC

    def place_order(
        self,
        symbol: str,
        side: str,
        volume: float,
        price: float,
        sl: float,
        tp: float,
        comment: str = "",
    ) -> Dict[str, Any]:
        """
        Execute market order through MT5 or simulation with comprehensive retcode audit.
        """
        start_time = time.perf_counter()

        # 1. Simulation Gateway Fallback
        if self.is_simulation_mode or not MT5_AVAILABLE:
            import random
            ticket = random.randint(1000000, 9999999)
            latency_ms = (time.perf_counter() - start_time) * 1000
            return {
                "success": True,
                "ticket": ticket,
                "price": price,
                "volume": volume,
                "comment": comment,
                "retcode": 10009,
                "message": "Order executed in Simulation Gateway",
                "latency_ms": round(latency_ms, 2),
            }

        # 2. Safety Gate Check: Terminal must be connected
        if not self.connected or not mt5.terminal_info().connected:
            return {
                "success": False,
                "error": "MT5 terminal is disconnected from broker trade server",
                "retcode": 10031,
                "message": RETCODE_DESCRIPTIONS.get(10031, "Connection lost"),
            }

        # 3. Symbol & Volume Validation
        sym_info = mt5.symbol_info(symbol)
        if sym_info is None:
            return {"success": False, "error": f"Symbol {symbol} info not found", "retcode": 10013}

        valid_vol, normalized_vol, vol_reason = self.validate_volume(symbol, volume)
        if not valid_vol:
            return {"success": False, "error": f"Volume validation failed: {vol_reason}", "retcode": 10014}

        # 4. Refresh live price
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return {"success": False, "error": f"No live price tick available for {symbol}", "retcode": 10021}

        order_type = mt5.ORDER_TYPE_BUY if side.upper() == "BUY" else mt5.ORDER_TYPE_SELL
        exec_price = tick.ask if side.upper() == "BUY" else tick.bid
        filling_mode = self._resolve_filling_mode(sym_info)

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(normalized_vol),
            "type": order_type,
            "price": float(exec_price),
            "sl": float(sl) if sl > 0 else 0.0,
            "tp": float(tp) if tp > 0 else 0.0,
            "deviation": settings.MAX_SLIPPAGE_POINTS,
            "magic": 123456,
            "comment": comment[:31],
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }

        # 5. Submit Order to Broker
        result = mt5.order_send(request)
        latency_ms = (time.perf_counter() - start_time) * 1000

        if result is None:
            last_err = mt5.last_error()
            return {
                "success": False,
                "error": f"order_send returned None (MT5 error code: {last_err[0]}, message: {last_err[1]})",
                "retcode": -1,
                "latency_ms": round(latency_ms, 2),
            }

        retcode_desc = RETCODE_DESCRIPTIONS.get(result.retcode, f"Broker retcode: {result.retcode}")

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.warning(
                f"Broker rejected order: retcode={result.retcode} ({retcode_desc}), comment='{result.comment}'",
                extra={"event": "BROKER_REJECTION", "retcode": result.retcode, "comment": result.comment},
            )
            return {
                "success": False,
                "retcode": result.retcode,
                "error": retcode_desc,
                "broker_comment": result.comment,
                "latency_ms": round(latency_ms, 2),
            }

        logger.info(
            f"Broker confirmed deal: Ticket={result.order}, Symbol={symbol}, Side={side}, Volume={result.volume}, Price={result.price}",
            extra={"event": "BROKER_ORDER_FILLED", "ticket": result.order, "price": result.price, "volume": result.volume},
        )

        return {
            "success": True,
            "ticket": result.order,
            "deal": result.deal,
            "price": result.price,
            "volume": result.volume,
            "retcode": result.retcode,
            "message": retcode_desc,
            "broker_comment": result.comment,
            "latency_ms": round(latency_ms, 2),
        }

    def get_open_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all currently open positions from MT5 or simulation."""
        if self.is_simulation_mode or not MT5_AVAILABLE:
            return []

        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        if positions is None:
            return []

        result = []
        for pos in positions:
            result.append({
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "side": "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                "volume": pos.volume,
                "price_open": pos.price_open,
                "price_current": pos.price_current,
                "sl": pos.sl,
                "tp": pos.tp,
                "profit": round(pos.profit, 2),
                "swap": pos.swap,
                "magic": pos.magic,
                "comment": pos.comment,
                "time": datetime.fromtimestamp(pos.time, tz=timezone.utc).isoformat(),
            })
        return result

    def get_history_deals(self, days: int = 90) -> List[Any]:
        """Fetch historical trade deals from MT5 terminal."""
        if self.is_simulation_mode or not MT5_AVAILABLE:
            return []
        from datetime import timedelta
        utc_now = datetime.now(timezone.utc)
        date_from = utc_now - timedelta(days=days)
        deals = mt5.history_deals_get(date_from, utc_now)
        if deals is None:
            return []
        return list(deals)

    def get_history_orders(self, days: int = 90) -> List[Any]:
        """Fetch historical orders from MT5 terminal."""
        if self.is_simulation_mode or not MT5_AVAILABLE:
            return []
        from datetime import timedelta
        utc_now = datetime.now(timezone.utc)
        date_from = utc_now - timedelta(days=days)
        orders = mt5.history_orders_get(date_from, utc_now)
        if orders is None:
            return []
        return list(orders)

    def close_position(self, ticket: int) -> Dict[str, Any]:
        """
        Close an existing open position by ticket using an opposite market order.
        """
        if self.is_simulation_mode or not MT5_AVAILABLE:
            return {
                "success": True,
                "ticket": ticket,
                "close_price": 1.0860,
                "message": "Closed in simulation mode",
            }

        # Find position
        positions = mt5.positions_get(ticket=ticket)
        if not positions or len(positions) == 0:
            return {"success": False, "error": f"Position ticket {ticket} not found in MT5"}

        pos = positions[0]
        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY

        tick = mt5.symbol_info_tick(pos.symbol)
        if tick is None:
            return {"success": False, "error": f"Cannot close position: tick unavailable for {pos.symbol}"}

        close_price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask
        sym_info = mt5.symbol_info(pos.symbol)
        filling_mode = self._resolve_filling_mode(sym_info)

        close_request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "price": close_price,
            "deviation": settings.MAX_SLIPPAGE_POINTS,
            "magic": 123456,
            "comment": f"Close #{ticket}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }

        res = mt5.order_send(close_request)
        if res is None or res.retcode != mt5.TRADE_RETCODE_DONE:
            err = res.comment if res else str(mt5.last_error())
            return {"success": False, "error": f"Failed to close position {ticket}: {err}", "retcode": res.retcode if res else -1}

        return {
            "success": True,
            "ticket": ticket,
            "close_deal": res.deal,
            "close_price": res.price,
            "volume": res.volume,
            "profit": round(pos.profit, 2),
            "message": "Position closed successfully",
        }

    def get_health_report(self) -> Dict[str, Any]:
        """Compile comprehensive startup and telemetry health diagnostics (secrets masked)."""
        acc = self.get_account_info()
        symbols_to_check = ["EURUSD", "XAUUSD", "GBPUSD"]
        symbols_data = {}

        for sym in symbols_to_check:
            p = self.get_symbol_price(sym)
            fresh, age, _ = self.is_tick_fresh(sym, max_age_seconds=10.0)
            symbols_data[sym] = {
                "bid": p.get("bid", 0.0),
                "ask": p.get("ask", 0.0),
                "spread_pips": p.get("spread_pips", 0.0),
                "tick_fresh": fresh,
                "tick_age_seconds": age,
            }

        return {
            "environment": self.mode,
            "is_simulation_mode": self.is_simulation_mode,
            "connected": self.connected,
            "account": {
                "login": acc.get("login"),
                "server": acc.get("server"),
                "trade_mode": acc.get("trade_mode"),
                "balance": acc.get("balance"),
                "equity": acc.get("equity"),
                "currency": acc.get("currency"),
                "trade_allowed": acc.get("trade_allowed"),
            },
            "symbols": symbols_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def print_startup_report(self) -> None:
        """Print a structured, clean startup diagnostic report without exposing secrets."""
        rep = self.get_health_report()
        acc = rep.get("account", {})
        conn_str = "CONNECTED" if rep['connected'] else ("SIMULATION (Sandbox Gateway)" if rep['is_simulation_mode'] else "DISCONNECTED")
        term_str = "CONNECTED" if rep['connected'] else ("STANDBY (Simulation)" if rep['is_simulation_mode'] else "OFFLINE")
        market_ok = all(s.get('tick_fresh') for s in rep.get('symbols', {}).values())
        market_str = "HEALTHY (Ticks fresh)" if market_ok else "DEGRADED (Stale ticks detected)"

        print("\n" + "=" * 65)
        print("          AUTONOMOUS AI TRADING SYSTEM — MT5 GATEWAY REPORT")
        print("=" * 65)
        print(f"  Environment        : {rep['environment']}")
        print(f"  MT5 connection     : {conn_str}")
        print(f"  Broker/server      : {acc.get('server') or 'N/A'}")
        print(f"  Account            : {acc.get('login') or 'N/A'}")
        print(f"  Balance            : {acc.get('balance')} {acc.get('currency', 'USD')}")
        print(f"  Equity             : {acc.get('equity')} {acc.get('currency', 'USD')}")
        print(f"  Terminal status    : {term_str}")
        print(f"  Market data status : {market_str}")
        print(f"  Trading permission : {'ALLOWED' if acc.get('trade_allowed') else 'RESTRICTED'}")
        print("-" * 65)
        print("  Market Data Freshness & Spreads:")
        for sym, data in rep.get("symbols", {}).items():
            fresh_str = "FRESH" if data['tick_fresh'] else f"STALE ({data['tick_age_seconds']}s)"
            print(f"    {sym:8} : Bid={data['bid']:<9} Ask={data['ask']:<9} Spread={data['spread_pips']:<4} pips [{fresh_str}]")
        print("=" * 65 + "\n")


mt5_client = MT5Client()
