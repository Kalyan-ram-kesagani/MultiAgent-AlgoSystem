"""Trade Analysis & Performance Tools for AI Agent."""
import asyncio
import json
from typing import Any, Dict, List, Optional
from sqlalchemy import select

from backend.app.agents.performance.performance_agent import performance_agent
from backend.app.database.session import async_session_maker
from backend.app.models.trading import Trade


def _run_async(coro):
    """Run an async coroutine synchronously inside tool calls."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # Inside existing event loop, create task in thread pool or use runner
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return loop.run_until_complete(coro)


async def _fetch_trades(strategy_id: Optional[str] = None, origin_filter: Optional[str] = None) -> List[Trade]:
    async with async_session_maker() as session:
        stmt = select(Trade).order_by(Trade.exit_time.desc())
        if strategy_id and strategy_id != "all":
            stmt = stmt.where(Trade.strategy_id == strategy_id)
        if origin_filter:
            stmt = stmt.where(Trade.origin == origin_filter)
        res = await session.execute(stmt)
        return list(res.scalars().all())


def get_strategy_performance(strategy_id: str = "strategy_v1") -> str:
    """
    Get comprehensive statistical performance metrics for a strategy.
    Separates SYSTEM_GENERATED algorithmic trades from MANUAL / EXTERNAL discretionary trades.
    Adheres strictly to sample size discipline.
    """
    trades = _run_async(_fetch_trades(strategy_id))
    system_trades = [t for t in trades if getattr(t, "origin", "SYSTEM_GENERATED") == "SYSTEM_GENERATED"]
    manual_trades = [t for t in trades if getattr(t, "origin", "") == "MANUAL"]
    external_trades = [t for t in trades if getattr(t, "origin", "") == "EXTERNAL"]

    sys_perf = performance_agent.analyze_performance(system_trades)
    
    # Classify sample status based on systematic trades
    count = len(system_trades)
    if count < 10:
        sample_status = "INSUFFICIENT DATA (<10 trades) - Prohibit rule modification"
    elif count < 50:
        sample_status = "EARLY DATA (10-49 trades) - Preliminary observation only"
    elif count < 100:
        sample_status = "PRELIMINARY (50-99 trades) - Requires out-of-sample confirmation"
    else:
        sample_status = "RESEARCHABLE (100+ trades) - Statistically viable for optimization"

    result = {
        "strategy_id": strategy_id,
        "sample_size": count,
        "sample_status": sample_status,
        "metrics": {
            "win_rate_pct": sys_perf.get("win_rate", 0.0),
            "profit_factor": sys_perf.get("profit_factor", 0.0),
            "expectancy_dollars": sys_perf.get("expectancy", 0.0),
            "net_pnl": sys_perf.get("net_pnl", 0.0),
            "max_drawdown": sys_perf.get("max_drawdown", 0.0),
            "average_r": sys_perf.get("average_r", 0.0),
            "wins": sys_perf.get("wins", 0),
            "losses": sys_perf.get("losses", 0),
            "consecutive_losses": sys_perf.get("consecutive_losses", 0),
        },
        "origin_breakdown": {
            "system_generated_count": len(system_trades),
            "manual_discretionary_count": len(manual_trades),
            "external_ea_count": len(external_trades),
        },
    }
    return json.dumps(result, indent=2)


def analyze_trade_history(strategy_id: str = "strategy_v1") -> str:
    """Analyze recent winning vs losing trades, duration, and profit distributions."""
    trades = _run_async(_fetch_trades(strategy_id, origin_filter="SYSTEM_GENERATED"))
    if not trades:
        return json.dumps({"status": "INSUFFICIENT DATA", "message": f"No system trades found for {strategy_id}"}, indent=2)

    pnls = [float(t.pnl) for t in trades]
    durations = [t.duration_seconds for t in trades]
    r_mults = [float(t.r_multiple) for t in trades if t.r_multiple is not None]

    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]

    return json.dumps({
        "strategy_id": strategy_id,
        "total_trades": len(trades),
        "avg_win_dollar": round(sum(wins) / len(wins), 2) if wins else 0.0,
        "avg_loss_dollar": round(sum(losses) / len(losses), 2) if losses else 0.0,
        "largest_win": max(pnls) if pnls else 0.0,
        "largest_loss": min(pnls) if pnls else 0.0,
        "avg_duration_minutes": round((sum(durations) / len(durations)) / 60.0, 1) if durations else 0.0,
        "avg_r_multiple": round(sum(r_mults) / len(r_mults), 2) if r_mults else 0.0,
    }, indent=2)


def analyze_drawdown(strategy_id: str = "strategy_v1") -> str:
    """Analyze historical drawdown depth, recovery periods, and underwater durations."""
    trades = _run_async(_fetch_trades(strategy_id, origin_filter="SYSTEM_GENERATED"))
    if len(trades) < 5:
        return json.dumps({"status": "INSUFFICIENT DATA", "trade_count": len(trades)}, indent=2)

    trades_sorted = sorted(trades, key=lambda t: t.exit_time)
    pnls = [float(t.pnl) for t in trades_sorted]
    
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    underwater_trades = 0
    max_underwater_streak = 0

    for p in pnls:
        cum += p
        if cum > peak:
            peak = cum
            underwater_trades = 0
        else:
            dd = peak - cum
            if dd > max_dd:
                max_dd = dd
            underwater_trades += 1
            if underwater_trades > max_underwater_streak:
                max_underwater_streak = underwater_trades

    return json.dumps({
        "strategy_id": strategy_id,
        "peak_equity_gain": round(peak, 2),
        "max_drawdown_dollars": round(max_dd, 2),
        "max_underwater_trades": max_underwater_streak,
        "total_analyzed_trades": len(pnls),
    }, indent=2)


def analyze_regimes(strategy_id: str = "strategy_v1") -> str:
    """Analyze strategy performance broken down by market regime and trading session."""
    trades = _run_async(_fetch_trades(strategy_id, origin_filter="SYSTEM_GENERATED"))
    perf = performance_agent.analyze_performance(trades)
    return json.dumps({
        "strategy_id": strategy_id,
        "by_session": perf.get("by_session", {}),
        "by_market": perf.get("by_market", {}),
        "by_regime": perf.get("by_regime", {}),
    }, indent=2)


def calculate_performance_metrics(strategy_id: str = "strategy_v1") -> str:
    """Calculate Sharpe, Sortino, Calmar, Expectancy, and Profit Factor for strategy."""
    trades = _run_async(_fetch_trades(strategy_id, origin_filter="SYSTEM_GENERATED"))
    perf = performance_agent.analyze_performance(trades)
    
    # Calculate Sharpe approximation from trade returns
    pnls = [float(t.pnl) for t in trades]
    if len(pnls) >= 10:
        import numpy as np
        mean = np.mean(pnls)
        std = np.std(pnls) + 1e-9
        sharpe = round(float(mean / std * np.sqrt(252)), 2)
        downside = [p for p in pnls if p < 0]
        downside_std = np.std(downside) + 1e-9 if downside else 1.0
        sortino = round(float(mean / downside_std * np.sqrt(252)), 2)
    else:
        sharpe = 0.0
        sortino = 0.0

    return json.dumps({
        "strategy_id": strategy_id,
        "trade_count": len(pnls),
        "expectancy": perf.get("expectancy", 0.0),
        "profit_factor": perf.get("profit_factor", 0.0),
        "win_rate": perf.get("win_rate", 0.0),
        "max_drawdown": perf.get("max_drawdown", 0.0),
        "sharpe_ratio_annualized": sharpe,
        "sortino_ratio_annualized": sortino,
    }, indent=2)


def analyze_trade_sources() -> str:
    """
    Categorize all database trades by strategy, trade origin (SYSTEM_GENERATED, MANUAL, EXTERNAL, UNKNOWN),
    execution source, status, and symbol.
    Strictly isolates manual discretionary and external trades to prevent contaminated strategy attribution.
    """
    async def _async_analyze():
        async with async_session_maker() as session:
            stmt = select(Trade)
            res = await session.execute(stmt)
            trades = list(res.scalars().all())

            system_count = 0
            manual_count = 0
            external_count = 0
            unknown_count = 0

            # Group map key: (strategy_id, trade_source, execution_source, status, symbol)
            group_map = {}

            for t in trades:
                origin = (t.origin or "SYSTEM_GENERATED").upper()
                if origin == "SYSTEM_GENERATED":
                    system_count += 1
                    trade_source = "SYSTEM_GENERATED"
                    exec_source = "SYSTEM_ORDER_GATEWAY" if t.order_id else "SYSTEM_AUTOMATED"
                    strat_id = t.strategy_id or "strategy_v1"
                elif origin == "MANUAL":
                    manual_count += 1
                    trade_source = "MANUAL"
                    exec_source = "MT5_TERMINAL_MANUAL"
                    strat_id = "MANUAL_DISCRETIONARY"
                elif origin == "EXTERNAL":
                    external_count += 1
                    trade_source = "EXTERNAL"
                    exec_source = "MT5_EXTERNAL_EA"
                    strat_id = "EXTERNAL_BROKER_DEAL"
                else:
                    unknown_count += 1
                    trade_source = "UNKNOWN"
                    exec_source = "UNATTRIBUTED"
                    strat_id = "UNKNOWN_SOURCE"

                status = "CLOSED"
                sym = (t.symbol or "UNKNOWN").upper()

                key = (strat_id, trade_source, exec_source, status, sym)
                if key not in group_map:
                    group_map[key] = {
                        "strategy_id": strat_id,
                        "trade_source": trade_source,
                        "execution_source": exec_source,
                        "status": status,
                        "symbol": sym,
                        "trade_count": 0,
                        "total_pnl": 0.0,
                    }
                group_map[key]["trade_count"] += 1
                group_map[key]["total_pnl"] = round(group_map[key]["total_pnl"] + float(t.pnl or 0.0), 2)

            return {
                "groups": list(group_map.values()),
                "total_trades": len(trades),
                "system_trades": system_count,
                "manual_trades": manual_count,
                "external_trades": external_count,
                "unknown_trades": unknown_count,
                "attribution_rule": "MANUAL and EXTERNAL trades are strictly isolated to prevent attributing discretionary activity to strategy_v1.",
            }

    data = _run_async(_async_analyze())
    return json.dumps(data, indent=2)

