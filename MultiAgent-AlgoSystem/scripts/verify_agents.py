"""Verification script to test and assert the health of all 11 decoupled agents."""
import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
import pandas as pd

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


async def verify_all_agents():
    results = {}
    print("\nStarting comprehensive verification of all 11 Agents...")

    # Connect MT5 Gateway (or fallback to Simulation Gateway)
    from trading.execution.mt5_client import mt5_client
    mt5_client.connect()

    # 1. Orchestrator Agent
    from backend.app.agents.orchestrator.orchestrator_agent import orchestrator
    res_orch = await orchestrator.execute_task("investigate_performance", {"symbol": "EURUSD", "strategy_id": "strategy_v1"})
    results["Agent #1 (Orchestrator)"] = "OPERATIONAL" if "backtest_summary" in res_orch else f"FAILED: {res_orch}"

    # 2. Research Agent
    from backend.app.agents.research.research_agent import research_agent
    from backend.app.schemas.research import HypothesisCreate
    hyp = await research_agent.create_hypothesis(HypothesisCreate(
        title="Trend pullbacks on H1 EURUSD yield positive expectancy",
        hypothesis_statement="Buying pullbacks in EMA trend yields Sharpe > 1.2",
        reasoning="Trend continuation probability exceeds mean reversion on H1",
        test_plan="Walk-forward out of sample test over 2 years",
        success_metric="Sharpe > 1.2, Profit Factor > 1.5",
        failure_condition="Drawdown > 10%"
    ))
    results["Agent #2 (Research)"] = "OPERATIONAL" if hyp.hypothesis_id.startswith("HYP-") else "FAILED"

    # 3. Data Agent
    from backend.app.agents.data.data_agent import DataAgent
    data_agent = DataAgent()
    bars = data_agent.generate_synthetic_data(symbol="EURUSD", num_bars=150)
    report = data_agent.validate_bars(symbol="EURUSD", timeframe="H1", bars=bars)
    results["Agent #3 (Data)"] = "OPERATIONAL" if str(report.quality_status) in ["VALIDATED", "DataQualityStatus.VALIDATED"] and len(bars) == 150 else "FAILED"

    # 4. Strategy Agent
    from backend.app.agents.strategy.strategy_agent import StrategyAgent
    strat_agent = StrategyAgent()
    strats = strat_agent.list_strategies()
    df_bars = pd.DataFrame([b.model_dump() for b in bars])
    signals = strat_agent.evaluate_signals("strategy_v1", df_bars)
    results["Agent #4 (Strategy)"] = "OPERATIONAL" if len(strats) >= 1 and isinstance(signals, list) else "FAILED"

    # 5. AI/ML Agent
    from backend.app.agents.ml.ml_agent import ml_agent
    ml_train = ml_agent.train_regime_classifier(df_bars)
    regime = ml_agent.predict_regime(df_bars)
    results["Agent #5 (AI / ML)"] = "OPERATIONAL" if ("average_cv_accuracy" in ml_train or "model_type" in ml_train) and regime else "FAILED"

    # 6. Backtest Agent
    from backend.app.agents.backtest.backtest_engine import BacktestEngine
    from backend.app.schemas.backtest import BacktestRequest
    bt_engine = BacktestEngine()
    strategy = strat_agent.get_strategy("strategy_v1")
    bt_res = bt_engine.run_backtest(strategy, df_bars, BacktestRequest(
        strategy_id="strategy_v1", symbol="EURUSD", timeframe="H1", initial_capital=10000.0, run_monte_carlo=True
    ))
    results["Agent #6 (Backtest)"] = "OPERATIONAL" if bt_res.profit_factor >= 0 else "FAILED"

    # 7. Risk Agent
    from backend.app.agents.risk.risk_engine import risk_engine
    risk_engine.disengage_kill_switch(operator="VERIFY_SCRIPT")
    from backend.app.schemas.risk import RiskEvaluationRequest
    risk_req = RiskEvaluationRequest(
        strategy_id="strategy_v1", symbol="EURUSD", side="BUY",
        entry_price=1.0850, stop_loss=1.0820, take_profit=1.0910,
        account_equity=10000.0, account_balance=10000.0, current_spread_pips=1.2,
        open_positions_count=0, symbol_positions_count=0, daily_realized_loss=0.0
    )
    risk_eval = risk_engine.evaluate_order(risk_req)
    results["Agent #7 (Risk Gate)"] = "OPERATIONAL" if risk_eval.is_approved and risk_eval.calculated_lots > 0 else "FAILED"

    # 8. Execution Agent
    from backend.app.agents.execution.execution_agent import ExecutionAgent
    from backend.app.schemas.trading import SignalCreate
    exec_agent = ExecutionAgent()
    curr_px = mt5_client.get_symbol_price("EURUSD")
    entry_p = curr_px.get("ask", 1.0850) or 1.0850
    sl_p = round(entry_p - 0.0030, 5)
    tp_p = round(entry_p + 0.0060, 5)
    sig = SignalCreate(
        strategy_id="verify_test", strategy_version="1.0.0", symbol="EURUSD", direction="BUY",
        timeframe="H1", timestamp=datetime.now(timezone.utc),
        suggested_entry=entry_p, suggested_sl=sl_p, suggested_tp=tp_p, risk_points=0.0030
    )
    exec_res = await exec_agent.execute_signal(sig)
    results["Agent #8 (Execution)"] = "OPERATIONAL" if exec_res.get("status") == "FILLED" and exec_res.get("quantity") > 0 else f"FAILED: {exec_res}"
    if exec_res.get("broker_ticket"):
        mt5_client.close_position(exec_res["broker_ticket"])

    # 9. Monitoring Agent
    from backend.app.agents.monitoring.monitoring_agent import monitoring_agent
    mt5_stat = await monitoring_agent.check_mt5_health()
    spread_stat = await monitoring_agent.check_spread("EURUSD")
    results["Agent #9 (Monitoring)"] = "OPERATIONAL" if (mt5_stat.get("connected") or mt5_stat.get("is_simulation")) and spread_stat.get("status") == "NORMAL" else "FAILED"

    # 10. Journal Agent
    from backend.app.agents.journal.journal_agent import JournalAgent
    journal_agent = JournalAgent()
    trade = await journal_agent.record_closed_trade(
        strategy_id="strategy_v1", symbol="EURUSD", direction="BUY",
        entry_time=datetime.now(timezone.utc) - timedelta(hours=2),
        exit_time=datetime.now(timezone.utc),
        entry_price=1.0850, stop_price=1.0820, target_price=1.0910, exit_price=1.0910,
        quantity=0.33, exit_reason="TP"
    )
    results["Agent #10 (Journal)"] = "OPERATIONAL" if trade.trade_id.startswith("TRD-") and trade.pnl > 0 else "FAILED"

    # 11. Performance Agent
    from backend.app.agents.performance.performance_agent import performance_agent
    perf = performance_agent.analyze_performance([trade])
    results["Agent #11 (Performance)"] = "OPERATIONAL" if perf.get("total_trades") == 1 and perf.get("win_rate") == 100.0 else "FAILED"

    print("\n==================== 11 AGENTS STATUS REPORT ====================")
    for agent_name, status in results.items():
        print(f"  {agent_name:28} : {status}")
    all_ok = all(v == "OPERATIONAL" for v in results.values())
    print("=================================================================")
    print(f"  OVERALL SYSTEM STATUS : {'ALL 11 AGENTS FULLY OPERATIONAL' if all_ok else 'SOME AGENTS FAILED'}\n")
    return all_ok

if __name__ == "__main__":
    asyncio.run(verify_all_agents())
