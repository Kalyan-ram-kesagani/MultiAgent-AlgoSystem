"""System launcher and command-line runner."""
import argparse
import asyncio
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.agents.orchestrator.orchestrator_agent import orchestrator
from backend.app.agents.risk.risk_engine import risk_engine
from backend.app.core.config import settings
from backend.app.database.session import init_db
from trading.execution.mt5_client import mt5_client


def run_server():
    """Start FastAPI server with uvicorn."""
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG)


async def main():
    parser = argparse.ArgumentParser(description="Autonomous AI Trading Platform CLI")
    parser.add_argument("--server", action="store_true", help="Launch the FastAPI server")
    parser.add_argument("--init-db", action="store_true", help="Initialize database tables")
    parser.add_argument("--test-mt5", action="store_true", help="Test MT5 connectivity")
    parser.add_argument("--backtest", action="store_true", help="Run sample strategy backtest")
    parser.add_argument("--kill-switch", choices=["on", "off"], help="Engage or disengage kill switch")
    parser.add_argument("--startup-report", action="store_true", help="Print comprehensive MT5 Gateway health and status report")
    parser.add_argument("--reconcile", action="store_true", help="Reconcile broker open positions with database")
    parser.add_argument("--mode", choices=["sandbox", "demo", "live"], help="Override environment mode for this run")
    args = parser.parse_args()

    if args.mode:
        settings.ENVIRONMENT = args.mode.upper()

    if args.init_db:
        print("[*] Initializing database tables...")
        await init_db()
        print("[+] Database tables initialized.")

    if args.startup_report or args.test_mt5:
        print("[*] Initializing MT5 Gateway...")
        mt5_client.connect()
        mt5_client.print_startup_report()

    if args.reconcile:
        from backend.app.agents.execution.execution_agent import execution_agent
        mt5_client.connect()
        print("[*] Reconciling broker open positions with database...")
        res = await execution_agent.reconcile_positions()
        print(f"[+] Status: {res['status']}")
        print(f"[+] Broker Open Positions: {res['broker_positions_count']}")
        print(f"[+] Untracked in DB: {res['untracked_in_db']}")
        if res['broker_positions']:
            for p in res['broker_positions']:
                print(f"    - Ticket #{p['ticket']}: {p['symbol']} {p['side']} {p['volume']} lots @ {p['price_open']} (PnL: ${p['profit']:.2f})")

    if args.kill_switch:
        if args.kill_switch == "on":
            risk_engine.engage_kill_switch("CLI command", operator="CLI")
            print("[!] EMERGENCY KILL SWITCH ENGAGED.")
        else:
            risk_engine.disengage_kill_switch(operator="CLI")
            print("[+] Kill switch disengaged.")

    if args.backtest:
        print("[*] Running sample backtest on EURUSD...")
        res = await orchestrator.execute_task("investigate_performance", {"symbol": "EURUSD", "strategy_id": "strategy_v1"})
        print(f"[+] Backtest Completed: {res.get('backtest_summary')}")

    if args.server:
        run_server()



if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Default run server
        run_server()
    else:
        asyncio.run(main())
