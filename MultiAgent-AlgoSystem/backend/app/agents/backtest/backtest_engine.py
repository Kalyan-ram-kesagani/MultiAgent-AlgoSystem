"""Agent #6 — Backtest Agent: Realistic backtesting, transaction costs, walk-forward, and Monte Carlo."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from backend.app.schemas.backtest import (
    BacktestRequest,
    BacktestResponse,
    BacktestTradeSummary,
)
from backend.app.schemas.trading import SignalCreate
from strategies.shared.base_strategy import BaseStrategy


class BacktestEngine:
    """Event-driven simulation backtest engine with realistic market execution frictions."""

    def __init__(self):
        pass

    def run_backtest(
        self,
        strategy: BaseStrategy,
        df: pd.DataFrame,
        request: BacktestRequest,
    ) -> BacktestResponse:
        """Run realistic simulation on market bars."""
        if len(df) < 50:
            raise ValueError("Insufficient market data for backtesting (minimum 50 bars required).")

        # Generate deterministic signals from strategy
        signals = strategy.generate_signals(df)

        # Execution parameters
        initial_capital = request.initial_capital
        equity = initial_capital
        spread_cost_per_trade = request.spread_pips * 10.0  # Approx FX standard lot pip value
        commission_per_lot = request.commission_per_lot
        slippage_price_delta = request.slippage_points * 0.00001  # In price units

        trades: List[BacktestTradeSummary] = []
        equity_curve = [{"time": df["timestamp"].iloc[0].isoformat(), "equity": equity}]

        # Create bar map for quick price checks
        bar_times = {bar["timestamp"]: idx for idx, bar in df.iterrows()}

        for signal in signals:
            if signal.timestamp not in bar_times:
                continue

            entry_idx = bar_times[signal.timestamp]
            if entry_idx >= len(df) - 1:
                continue

            # Simulate entry at the next bar's open price with slippage
            next_bar = df.iloc[entry_idx + 1]
            if signal.direction == "BUY":
                entry_price = next_bar["open"] + slippage_price_delta
                sl_price = signal.suggested_sl
                tp_price = signal.suggested_tp
                risk_distance = entry_price - sl_price
            else:
                entry_price = next_bar["open"] - slippage_price_delta
                sl_price = signal.suggested_sl
                tp_price = signal.suggested_tp
                risk_distance = sl_price - entry_price

            if risk_distance <= 0:
                continue

            # 1% Risk sizing
            risk_amount = equity * 0.01
            lot_size = max(0.01, round(risk_amount / (risk_distance * 100000), 2))

            # Simulate through subsequent bars until exit
            exit_price = None
            exit_reason = None
            exit_time = None

            for j in range(entry_idx + 1, len(df)):
                bar = df.iloc[j]

                if signal.direction == "BUY":
                    # Check SL first (conservative)
                    if bar["low"] <= sl_price:
                        exit_price = sl_price - slippage_price_delta
                        exit_reason = "SL"
                        exit_time = bar["timestamp"]
                        break
                    elif bar["high"] >= tp_price:
                        exit_price = tp_price - slippage_price_delta
                        exit_reason = "TP"
                        exit_time = bar["timestamp"]
                        break
                else:
                    if bar["high"] >= sl_price:
                        exit_price = sl_price + slippage_price_delta
                        exit_reason = "SL"
                        exit_time = bar["timestamp"]
                        break
                    elif bar["low"] <= tp_price:
                        exit_price = tp_price + slippage_price_delta
                        exit_reason = "TP"
                        exit_time = bar["timestamp"]
                        break

            # If trade still open at end of data, close at final bar close
            if exit_price is None:
                final_bar = df.iloc[-1]
                exit_price = final_bar["close"]
                exit_reason = "DATA_END"
                exit_time = final_bar["timestamp"]

            # Calculate PnL in currency
            if signal.direction == "BUY":
                gross_pnl = (exit_price - entry_price) * 100000 * lot_size
            else:
                gross_pnl = (entry_price - exit_price) * 100000 * lot_size

            # Deduct transaction costs
            total_comm = commission_per_lot * lot_size
            net_pnl = gross_pnl - total_comm - (spread_cost_per_trade * lot_size)
            r_mult = net_pnl / (risk_amount + 1e-9)

            equity += net_pnl
            equity_curve.append({"time": exit_time.isoformat(), "equity": round(equity, 2)})

            trades.append(
                BacktestTradeSummary(
                    symbol=signal.symbol,
                    direction=signal.direction,
                    entry_time=next_bar["timestamp"],
                    exit_time=exit_time,
                    entry_price=round(entry_price, 5),
                    exit_price=round(exit_price, 5),
                    sl=round(sl_price, 5),
                    tp=round(tp_price, 5),
                    quantity=lot_size,
                    pnl=round(net_pnl, 2),
                    r_multiple=round(r_mult, 2),
                    exit_reason=exit_reason,
                )
            )

        # Compute comprehensive performance metrics
        metrics = self._calculate_metrics(trades, initial_capital, equity_curve)

        # Monte Carlo Simulation if requested
        monte_carlo_dd = None
        if request.run_monte_carlo and trades:
            monte_carlo_dd = self.run_monte_carlo(trades, iterations=request.monte_carlo_iterations)

        import uuid

        return BacktestResponse(
            backtest_id=f"BT-{uuid.uuid4().hex[:8].upper()}",
            strategy_id=request.strategy_id,
            strategy_version=request.strategy_version,
            symbol=request.symbol,
            timeframe=request.timeframe,
            total_trades=metrics["total_trades"],
            winning_trades=metrics["winning_trades"],
            losing_trades=metrics["losing_trades"],
            win_rate=metrics["win_rate"],
            net_profit=metrics["net_profit"],
            profit_factor=metrics["profit_factor"],
            expectancy=metrics["expectancy"],
            average_win=metrics["average_win"],
            average_loss=metrics["average_loss"],
            max_drawdown_pct=metrics["max_drawdown_pct"],
            max_drawdown_dollars=metrics["max_drawdown_dollars"],
            sharpe_ratio=metrics["sharpe_ratio"],
            sortino_ratio=metrics["sortino_ratio"],
            average_r=metrics["average_r"],
            monte_carlo_drawdown_95=monte_carlo_dd,
            equity_curve=equity_curve,
            trades=trades,
        )

    def _calculate_metrics(
        self,
        trades: List[BacktestTradeSummary],
        initial_capital: float,
        equity_curve: List[Dict[str, Any]],
    ) -> Dict[str, float]:
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "net_profit": 0.0,
                "profit_factor": 0.0,
                "expectancy": 0.0,
                "average_win": 0.0,
                "average_loss": 0.0,
                "max_drawdown_pct": 0.0,
                "max_drawdown_dollars": 0.0,
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "average_r": 0.0,
            }

        pnls = np.array([t.pnl for t in trades])
        r_mults = np.array([t.r_multiple for t in trades])

        wins = pnls[pnls > 0]
        losses = pnls[pnls < 0]

        total_trades = len(trades)
        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate = round((winning_trades / total_trades) * 100, 2)
        net_profit = round(float(np.sum(pnls)), 2)

        gross_win = float(np.sum(wins)) if len(wins) > 0 else 0.0
        gross_loss = abs(float(np.sum(losses))) if len(losses) > 0 else 0.0
        profit_factor = round(gross_win / gross_loss, 2) if gross_loss > 0 else 999.0

        avg_win = round(float(np.mean(wins)), 2) if len(wins) > 0 else 0.0
        avg_loss = round(float(np.mean(losses)), 2) if len(losses) > 0 else 0.0

        win_prob = winning_trades / total_trades
        loss_prob = losing_trades / total_trades
        expectancy = round((win_prob * avg_win) + (loss_prob * avg_loss), 2)

        # Max Drawdown (both % and $)
        equities = [pt["equity"] for pt in equity_curve]
        peak = equities[0]
        max_dd_pct = 0.0
        max_dd_dollars = 0.0
        for eq in equities:
            if eq > peak:
                peak = eq
            dd_dollars = peak - eq
            if dd_dollars > max_dd_dollars:
                max_dd_dollars = dd_dollars
            dd = dd_dollars / (peak + 1e-9) * 100
            if dd > max_dd_pct:
                max_dd_pct = dd

        # Sharpe & Sortino
        if len(pnls) > 1 and np.std(pnls) > 0:
            sharpe = round(float(np.mean(pnls) / np.std(pnls) * np.sqrt(252)), 2)
            neg_pnls = pnls[pnls < 0]
            downside_std = np.std(neg_pnls) if len(neg_pnls) > 1 else np.std(pnls)
            sortino = round(float(np.mean(pnls) / (downside_std + 1e-9) * np.sqrt(252)), 2)
        else:
            sharpe = 0.0
            sortino = 0.0

        avg_r = round(float(np.mean(r_mults)), 2)

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "net_profit": net_profit,
            "profit_factor": profit_factor,
            "expectancy": expectancy,
            "average_win": avg_win,
            "average_loss": avg_loss,
            "max_drawdown_pct": round(max_dd_pct, 2),
            "max_drawdown_dollars": round(max_dd_dollars, 2),
            "sharpe_ratio": sharpe,
            "sortino_ratio": sortino,
            "average_r": avg_r,
        }

    def run_monte_carlo(
        self,
        trades: List[BacktestTradeSummary],
        iterations: int = 500,
        random_seed: int = 42,
    ) -> float:
        """Permute trade ordering across N runs to calculate 95th percentile max drawdown."""
        if len(trades) < 5:
            return 0.0

        rng = np.random.default_rng(random_seed)
        simulated_drawdowns = []

        for _ in range(iterations):
            shuffled = rng.permutation(trades)
            equity = 10000.0
            peak = equity
            max_dd = 0.0
            for t in shuffled:
                r = getattr(t, "r_multiple", 0.0)
                if r == 0.0:
                    r = t.pnl / 100.0
                trade_pnl = (equity * 0.01) * r
                equity += trade_pnl
                if equity > peak:
                    peak = equity
                dd = (peak - equity) / peak * 100.0
                if dd > max_dd:
                    max_dd = dd
            simulated_drawdowns.append(max_dd)

        # 95th percentile of drawdown distribution
        dd_95 = float(np.percentile(simulated_drawdowns, 95))
        return round(dd_95, 2)

    def compare_candidate_to_baseline(
        self,
        baseline_strategy: BaseStrategy,
        candidate_strategy: BaseStrategy,
        df: pd.DataFrame,
        request: BacktestRequest,
    ) -> Dict[str, Any]:
        """
        Execute comprehensive Baseline vs Candidate evaluation pipeline:
        1. Full backtest on both strategies
        2. Walk-forward split (70% in-sample, 30% out-of-sample)
        3. 95% Monte Carlo drawdown permutations
        4. Statistical comparison table with anti-curve-fitting stability checks.
        """
        # 1. Full Dataset Execution
        base_res = self.run_backtest(baseline_strategy, df, request)
        cand_res = self.run_backtest(candidate_strategy, df, request)

        # 2. Walk-Forward Partitioning (70% IS / 30% OOS)
        split_idx = int(len(df) * 0.70)
        df_is = df.iloc[:split_idx].copy().reset_index(drop=True)
        df_oos = df.iloc[split_idx:].copy().reset_index(drop=True)

        cand_is_res = self.run_backtest(candidate_strategy, df_is, request)
        cand_oos_res = self.run_backtest(candidate_strategy, df_oos, request)

        # 3. Monte Carlo 95% Max Drawdown
        base_mc_dd = self.run_monte_carlo(base_res.trades, iterations=500, random_seed=42)
        cand_mc_dd = self.run_monte_carlo(cand_res.trades, iterations=500, random_seed=42)

        # 4. Out-of-sample return & Stability Score
        is_pf = getattr(cand_is_res, "profit_factor", 1.0)
        oos_pf = getattr(cand_oos_res, "profit_factor", 1.0)
        stability_score = round(max(0.0, 1.0 - abs(is_pf - oos_pf) / (is_pf + 1e-9)), 2)

        is_ret = (cand_is_res.net_profit / request.initial_capital) * 100
        oos_ret = (cand_oos_res.net_profit / request.initial_capital) * 100

        # Build comparison summary
        comparison_table = [
            {
                "metric": "Profit Factor",
                "baseline": getattr(base_res, "profit_factor", 0.0),
                "candidate": getattr(cand_res, "profit_factor", 0.0),
                "delta": round(getattr(cand_res, "profit_factor", 0.0) - getattr(base_res, "profit_factor", 0.0), 2),
            },
            {
                "metric": "Expectancy ($)",
                "baseline": getattr(base_res, "expectancy", 0.0),
                "candidate": getattr(cand_res, "expectancy", 0.0),
                "delta": round(getattr(cand_res, "expectancy", 0.0) - getattr(base_res, "expectancy", 0.0), 2),
            },
            {
                "metric": "Max Drawdown (%)",
                "baseline": getattr(base_res, "max_drawdown_pct", 0.0),
                "candidate": getattr(cand_res, "max_drawdown_pct", 0.0),
                "delta": round(getattr(cand_res, "max_drawdown_pct", 0.0) - getattr(base_res, "max_drawdown_pct", 0.0), 2),
            },
            {
                "metric": "Trade Count",
                "baseline": getattr(base_res, "total_trades", 0),
                "candidate": getattr(cand_res, "total_trades", 0),
                "delta": getattr(cand_res, "total_trades", 0) - getattr(base_res, "total_trades", 0),
            },
            {
                "metric": "Win Rate (%)",
                "baseline": getattr(base_res, "win_rate", 0.0),
                "candidate": getattr(cand_res, "win_rate", 0.0),
                "delta": round(getattr(cand_res, "win_rate", 0.0) - getattr(base_res, "win_rate", 0.0), 2),
            },
            {
                "metric": "Monte Carlo 95% DD (%)",
                "baseline": base_mc_dd,
                "candidate": cand_mc_dd,
                "delta": round(cand_mc_dd - base_mc_dd, 2),
            },
            {
                "metric": "OOS Return (%)",
                "baseline": "N/A",
                "candidate": round(oos_ret, 2),
                "delta": round(oos_ret, 2),
            },
            {
                "metric": "Stability Score (0-1)",
                "baseline": "1.00",
                "candidate": stability_score,
                "delta": round(stability_score - 1.0, 2),
            },
        ]

        # Candidate assessment
        candidate_improves = (
            getattr(cand_res, "profit_factor", 0.0) >= getattr(base_res, "profit_factor", 0.0)
            and getattr(cand_res, "expectancy", 0.0) >= getattr(base_res, "expectancy", 0.0)
            and getattr(cand_res, "max_drawdown_pct", 99.0) <= getattr(base_res, "max_drawdown_pct", 99.0) + 2.0
            and getattr(cand_res, "total_trades", 0) >= 5
        )

        base_id = baseline_strategy.metadata.strategy_id if hasattr(baseline_strategy, "metadata") else getattr(baseline_strategy, "strategy_id", "strategy_v1")
        cand_id = candidate_strategy.metadata.strategy_id if hasattr(candidate_strategy, "metadata") else getattr(candidate_strategy, "strategy_id", "strategy_v1.1")

        return {
            "baseline_strategy": base_id,
            "candidate_strategy": cand_id,
            "candidate_improves_baseline": candidate_improves,
            "comparison_table": comparison_table,
            "in_sample_return_pct": round(is_ret, 2),
            "out_of_sample_return_pct": round(oos_ret, 2),
            "stability_score": stability_score,
            "monte_carlo_95_drawdown_pct": cand_mc_dd,
            "baseline_metrics": base_res.model_dump(),
            "candidate_metrics": cand_res.model_dump(),
            "status": "PENDING_HUMAN_REVIEW",
            "action": "Awaiting human operator review before paper/demo staging.",
        }
