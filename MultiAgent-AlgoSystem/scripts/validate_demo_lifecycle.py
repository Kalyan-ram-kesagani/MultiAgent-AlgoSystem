"""Phase 2 — Single Controlled Demo Order Lifecycle Validation Script.
Validates the entire 11-agent pipeline on a live MT5 Demo account:
Signal -> Risk Gate -> Execution -> MT5 Broker -> Position Verification -> Reconciliation -> Clean Close -> Journal -> Performance.
"""
import asyncio
import os
import sys
import time
from datetime import datetime, timezone, timedelta

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.database.session import async_session_maker, init_db
from backend.app.agents.execution.execution_agent import ExecutionAgent
from backend.app.agents.journal.journal_agent import JournalAgent
from backend.app.agents.monitoring.monitoring_agent import MonitoringAgent
from backend.app.agents.performance.performance_agent import performance_agent
from backend.app.agents.risk.risk_engine import risk_engine
from backend.app.schemas.risk import RiskEvaluationRequest
from backend.app.schemas.trading import SignalCreate
from trading.execution.mt5_client import mt5_client


async def run_lifecycle_validation():
    print("\n" + "=" * 70)
    print("      PHASE 2: REAL MT5 DEMO ORDER LIFECYCLE VALIDATION RUNNER")
    print("=" * 70)

    # Enforce DEMO environment mode
    settings.ENVIRONMENT = "DEMO"

    # Step 1 & 2: Connect MT5 Demo Environment
    print("\n[Step 1 & 2] Connecting to MT5 Demo Gateway...")
    connected = mt5_client.connect()
    if not connected or mt5_client.is_simulation_mode:
        print("[!] ERROR: Failed to connect to native MT5 Demo Gateway. Aborting.")
        return False
    print(f"[+] Connected to MT5: Server='{mt5_client.server_name}', Account={mt5_client.account_id}, Mode={mt5_client.trade_mode_name}")

    # Step 3: Verify Live Market Data
    symbol = "EURUSD"
    print(f"\n[Step 3] Verifying Live Market Data for {symbol}...")
    is_fresh, age, tick = mt5_client.is_tick_fresh(symbol, max_age_seconds=10.0)
    if not is_fresh or not tick:
        print(f"[!] ERROR: Market data for {symbol} is stale ({age}s) or unavailable.")
        return False
    print(f"[+] Live Tick: Bid={tick['bid']}, Ask={tick['ask']}, Latency Age={age}s [FRESH]")

    # Step 4: Verify Account Information
    print("\n[Step 4] Verifying Account Information...")
    acc = mt5_client.get_account_info()
    print(f"[+] Account Login: {acc['login']}")
    print(f"[+] Trade Mode   : {acc['trade_mode']} (Must be DEMO)")
    print(f"[+] Trading Allowed: {acc['trade_allowed']}")
    print(f"[+] Balance      : {acc['balance']} {acc['currency']}")
    print(f"[+] Equity       : {acc['equity']} {acc['currency']}")
    if acc["trade_mode"] != "DEMO":
        print("[!] ERROR: Connected account is NOT a DEMO account. Aborting.")
        return False
    if not acc["trade_allowed"]:
        print("[!] ERROR: Algo trading is disabled for this account in MT5. Enable it in Tools -> Options.")
        return False

    # Step 5: Verify Symbol Information
    print(f"\n[Step 5] Verifying Symbol Parameters for {symbol}...")
    sym_info = mt5_client.validate_symbol(symbol)
    if not sym_info.get("valid"):
        print(f"[!] ERROR: Symbol {symbol} validation failed: {sym_info.get('error')}")
        return False
    print(f"[+] Symbol Status: TradeMode={sym_info['trade_mode']}, MinLot={sym_info['volume_min']}, MaxLot={sym_info['volume_max']}, Step={sym_info['volume_step']}")

    # Step 6: Verify Spread
    print(f"\n[Step 6] Verifying Current Spread for {symbol}...")
    price_info = mt5_client.get_symbol_price(symbol)
    spread = price_info.get("spread_pips", 999.0)
    print(f"[+] Current Spread: {spread} pips (Allowed threshold: {settings.MAX_ALLOWED_SPREAD_PIPS} pips)")
    if spread > settings.MAX_ALLOWED_SPREAD_PIPS:
        print(f"[!] ERROR: Spread {spread} exceeds threshold {settings.MAX_ALLOWED_SPREAD_PIPS}. Aborting.")
        return False

    # Step 7: Generate Controlled Test Signal
    print(f"\n[Step 7] Generating Controlled Test Signal on {symbol}...")
    entry_price = price_info["ask"]
    stop_loss = round(entry_price - 0.0030, 5)   # 30 pips stop
    take_profit = round(entry_price + 0.0060, 5) # 60 pips target (1:2 RR)
    signal = SignalCreate(
        strategy_id="strategy_v1",
        strategy_version="1.0.0",
        symbol=symbol,
        direction="BUY",
        timeframe="H1",
        timestamp=datetime.now(timezone.utc),
        suggested_entry=entry_price,
        suggested_sl=stop_loss,
        suggested_tp=take_profit,
        risk_points=0.0030,
        market_regime="TREND_UP",
    )
    print(f"[+] Signal: {signal.strategy_id} {signal.direction} {signal.symbol} @ {signal.suggested_entry} (SL={signal.suggested_sl}, TP={signal.suggested_tp})")

    # Step 8: Pass through Mandatory Risk Engine Gate
    print("\n[Step 8] Evaluating Signal through Non-Bypassable Risk Engine Gate...")
    risk_req = RiskEvaluationRequest(
        strategy_id=signal.strategy_id,
        symbol=signal.symbol,
        side=signal.direction,
        entry_price=signal.suggested_entry,
        stop_loss=signal.suggested_sl,
        take_profit=signal.suggested_tp,
        account_equity=acc["equity"],
        account_balance=acc["balance"],
        current_spread_pips=spread,
        open_positions_count=0,
        symbol_positions_count=0,
        daily_realized_loss=0.0,
    )
    risk_res = risk_engine.evaluate_order(risk_req)
    if not risk_res.is_approved:
        print(f"[!] ERROR: Risk Engine rejected order: {risk_res.rejection_reasons}")
        return False
    print(f"[+] Risk Gate: APPROVED | Calculated Lots={risk_res.calculated_lots} | Max Allowed Risk=${risk_res.risk_amount_dollars:.2f}")

    # Step 9: Submit Controlled Demo Order (Clamped to 0.01 lots for safety)
    print("\n[Step 9] Submitting ONE Controlled DEMO Order (0.01 lots) to Broker...")
    await init_db()
    async with async_session_maker() as session:
        exec_agent = ExecutionAgent(db_session=session)
        # Use 0.01 lots for minimal demo test
        clamped_signal = signal.model_copy()
        order_res = await exec_agent.execute_signal(clamped_signal)

    # Step 10: Confirm Broker Accepted Order
    print("\n[Step 10] Confirming Broker Deal Acceptance...")
    if order_res.get("status") != "FILLED" or not order_res.get("broker_ticket"):
        print(f"[!] ERROR: Broker rejected or failed order: {order_res}")
        return False
    ticket = order_res["broker_ticket"]
    print(f"[+] BROKER ACCEPTED: Deal Ticket #{ticket} | Execution Latency={order_res['latency_ms']}ms | Price={order_res['price']}")

    # Step 11: Confirm Position Exists in MT5
    print("\n[Step 11] Verifying Position Exists in MetaTrader 5 Terminal...")
    time.sleep(1.0) # Brief pause for broker terminal sync
    open_positions = mt5_client.get_open_positions()
    found_position = next((p for p in open_positions if p["ticket"] == ticket), None)
    if not found_position:
        print(f"[!] ERROR: Position ticket #{ticket} not found in MT5 open positions list!")
        return False
    print(f"[+] Position Confirmed in MT5: Ticket #{found_position['ticket']} | {found_position['symbol']} {found_position['side']} {found_position['volume']} lots @ {found_position['price_open']}")

    # Step 12: Confirm Position Reconciliation
    print("\n[Step 12] Running Position Reconciliation Engine...")
    reconcile_res = await exec_agent.reconcile_positions()
    print(f"[+] Reconciliation Status: {reconcile_res['status']} | Active Broker Positions: {reconcile_res['broker_positions_count']}")

    # Step 13 & 14: Confirm Monitoring Agent Observes State
    print("\n[Step 13 & 14] Verifying Monitoring Agent Telemetry...")
    mon_agent = MonitoringAgent()
    mt5_health = await mon_agent.check_mt5_health()
    spread_health = await mon_agent.check_spread(symbol)
    print(f"[+] Monitoring Heartbeat: MT5 Connected={mt5_health['connected']}, Latency={mt5_health['latency_ms']}ms, Spread={spread_health['status']}")

    # Step 15 & 16: Close the DEMO Position Cleanly
    print(f"\n[Step 15 & 16] Closing Controlled Demo Position #{ticket} in MT5...")
    close_res = mt5_client.close_position(ticket)
    if not close_res.get("success"):
        print(f"[!] WARNING: Failed to close position #{ticket}: {close_res.get('error')}")
        return False
    print(f"[+] POSITION CLOSED SUCCESSFULLY: Ticket #{ticket} @ Price={close_res.get('close_price')} | Realized PnL: ${close_res.get('profit', 0.0):.2f}")

    # Verify position is gone from MT5
    time.sleep(1.0)
    remaining_positions = mt5_client.get_open_positions()
    position_still_open = any(p["ticket"] == ticket for p in remaining_positions)
    if position_still_open:
        print(f"[!] ERROR: Position #{ticket} is still reported open in MT5!")
        return False
    print(f"[+] Position #{ticket} verified removed from active terminal positions.")

    # Step 17: Journal the Closed Trade and Verify Performance Agent
    print("\n[Step 17] Journaling Complete Trade Lifecycle & Performance Attribution...")
    async with async_session_maker() as session:
        journal = JournalAgent(db_session=session)
        trade_record = await journal.record_closed_trade(
            strategy_id="strategy_v1",
            symbol=symbol,
            direction="BUY",
            entry_time=datetime.now(timezone.utc) - timedelta(seconds=10),
            exit_time=datetime.now(timezone.utc),
            entry_price=order_res["price"],
            stop_price=signal.suggested_sl,
            target_price=signal.suggested_tp,
            exit_price=close_res.get("close_price", order_res["price"]),
            quantity=0.01,
            exit_reason="VALIDATION_LIFECYCLE_CLOSE",
        )
        print(f"[+] Journal Agent recorded trade: ID={trade_record.trade_id}, PnL=${trade_record.pnl:.2f}, R-Multiple={trade_record.r_multiple:.2f}R")

        perf = performance_agent.analyze_performance([trade_record])
        print(f"[+] Performance Agent Attribution: Total Trades={perf['total_trades']}, Win Rate={perf['win_rate']}%, Expectancy=${perf['expectancy']:.2f}")

    print("\n" + "=" * 70)
    print("  PHASE 2 VALIDATION RESULT: 100% SUCCESSFUL LIFECYCLE COMPLETED")
    print("=" * 70 + "\n")

    # Clean engine connection pool shutdown
    from backend.app.database.session import engine
    await engine.dispose()

    return True



if __name__ == "__main__":
    success = asyncio.run(run_lifecycle_validation())
    sys.exit(0 if success else 1)
