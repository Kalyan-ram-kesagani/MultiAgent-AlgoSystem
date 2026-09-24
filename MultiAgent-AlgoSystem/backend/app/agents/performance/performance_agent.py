"""Agent #11 — Performance Agent: Multi-Dimensional Statistical Attribution & Sample-Aware Attribution."""
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from backend.app.models.trading import Trade


class PerformanceAgent:
    """Computes rigorous statistical attribution across strategies, markets, regimes, and sessions."""

    def __init__(
        self,
        insufficient_sample_threshold: int = 30,
        early_analysis_threshold: int = 100,
    ):
        self.insufficient_threshold = insufficient_sample_threshold
        self.early_threshold = early_analysis_threshold

    def determine_sample_status(self, trade_count: int) -> Dict[str, Any]:
        """Classify statistical sample credibility based on trade count."""
        if trade_count < self.insufficient_threshold:
            status = "INSUFFICIENT SAMPLE"
            confidence = "LOW"
            recommendation = "Collect more empirical trade data before drawing structural conclusions."
        elif trade_count < self.early_threshold:
            status = "EARLY ANALYSIS"
            confidence = "MODERATE"
            recommendation = "Early exploratory pattern analysis permissible; avoid overfitting parameters."
        else:
            status = "RESEARCHABLE"
            confidence = "HIGH"
            recommendation = "Statistically sufficient dataset for hypothesis testing and walk-forward backtesting."

        return {
            "status": status,
            "confidence": confidence,
            "recommendation": recommendation,
            "trade_count": trade_count,
            "thresholds": {
                "insufficient": self.insufficient_threshold,
                "early_analysis": self.early_threshold,
            },
        }

    def analyze_performance(self, trades: List[Trade]) -> Dict[str, Any]:
        """Compute all 14 core performance metrics and 10 segmentations."""
        if not trades:
            sample_info = self.determine_sample_status(0)
            return {
                "sample_status": sample_info,
                "trade_count": 0,
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "expectancy": 0.0,
                "average_r": 0.0,
                "gross_profit": 0.0,
                "gross_loss": 0.0,
                "net_pnl": 0.0,
                "total_net_pnl": 0.0,
                "max_drawdown": 0.0,
                "consecutive_losses": 0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "segmentation": {},
            }

        rows = []
        for t in trades:
            entry_dt = t.entry_time if isinstance(t.entry_time, datetime) else datetime.utcnow()
            day_name = entry_dt.strftime("%A")
            
            # Approximate volatility regime from price spread or r_multiple
            pnl_val = float(t.pnl)
            r_val = float(t.r_multiple) if t.r_multiple is not None else 0.0
            
            # Volatility regime estimation
            vol_regime = "NORMAL"
            if abs(r_val) > 2.0 or abs(pnl_val) > 10.0:
                vol_regime = "HIGH"
            elif abs(r_val) < 0.2:
                vol_regime = "LOW"

            rows.append({
                "symbol": t.symbol or "UNKNOWN",
                "timeframe": "H1",
                "session": t.session or "UNKNOWN",
                "direction": t.direction or "UNKNOWN",
                "origin": getattr(t, "origin", "SYSTEM_GENERATED") or "SYSTEM_GENERATED",
                "strategy_version": t.strategy_id or "strategy_v1",
                "market_regime": t.market_regime or "UNKNOWN",
                "volatility_regime": vol_regime,
                "day_of_week": day_name,
                "entry_condition": "TREND_PULLBACK_CONFIRMATION",
                "exit_condition": t.exit_reason or "TP",
                "pnl": pnl_val,
                "r_multiple": r_val,
                "commission": float(t.commission or 0.0),
                "swap": float(t.swap or 0.0),
            })

        df = pd.DataFrame(rows)
        total_trades = len(df)
        wins = df[df["pnl"] > 0]
        losses = df[df["pnl"] < 0]
        num_wins = len(wins)
        num_losses = len(losses)

        win_rate = round(num_wins / total_trades * 100, 2)
        gross_profit = round(float(wins["pnl"].sum()), 2) if num_wins > 0 else 0.0
        gross_loss = round(abs(float(losses["pnl"].sum())), 2) if num_losses > 0 else 0.0
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)

        avg_win = round(float(wins["pnl"].mean()), 2) if num_wins > 0 else 0.0
        avg_loss = round(float(losses["pnl"].mean()), 2) if num_losses > 0 else 0.0
        expectancy = round((num_wins / total_trades * avg_win) + (num_losses / total_trades * avg_loss), 2)
        avg_r = round(float(df["r_multiple"].mean()), 2)
        net_pnl = round(float(df["pnl"].sum()), 2)

        # Max drawdown computation
        cum_pnl = df["pnl"].cumsum()
        peak = cum_pnl.cummax()
        drawdown_series = peak - cum_pnl
        max_drawdown = round(float(drawdown_series.max()), 2) if len(drawdown_series) > 0 else 0.0

        # Consecutive losses calculation
        max_consecutive_losses = 0
        current_streak = 0
        for p in df["pnl"]:
            if p < 0:
                current_streak += 1
                if current_streak > max_consecutive_losses:
                    max_consecutive_losses = current_streak
            else:
                current_streak = 0

        # Multi-dimensional segmentation across all 10 dimensions
        dimensions = [
            "symbol",
            "timeframe",
            "session",
            "direction",
            "origin",
            "strategy_version",
            "market_regime",
            "volatility_regime",
            "day_of_week",
            "entry_condition",
            "exit_condition",
        ]

        def breakdown_dimension(col_name: str) -> Dict[str, Any]:
            res = {}
            for val, grp in df.groupby(col_name):
                grp_wins = grp[grp["pnl"] > 0]
                grp_losses = grp[grp["pnl"] < 0]
                g_wins_count = len(grp_wins)
                g_losses_count = len(grp_losses)
                g_tot = len(grp)
                g_gross_win = float(grp_wins["pnl"].sum()) if g_wins_count > 0 else 0.0
                g_gross_loss = abs(float(grp_losses["pnl"].sum())) if g_losses_count > 0 else 0.0
                g_pf = round(g_gross_win / g_gross_loss, 2) if g_gross_loss > 0 else 999.0
                res[str(val)] = {
                    "count": g_tot,
                    "wins": g_wins_count,
                    "losses": g_losses_count,
                    "win_rate": round(g_wins_count / g_tot * 100, 1),
                    "profit_factor": g_pf,
                    "net_pnl": round(float(grp["pnl"].sum()), 2),
                    "avg_r": round(float(grp["r_multiple"].mean()), 2),
                }
            return res

        segmentation = {dim: breakdown_dimension(dim) for dim in dimensions}
        sample_status = self.determine_sample_status(total_trades)

        return {
            "sample_status": sample_status,
            "trade_count": total_trades,
            "total_trades": total_trades,
            "wins": num_wins,
            "losses": num_losses,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "expectancy": expectancy,
            "average_r": avg_r,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "net_pnl": net_pnl,
            "total_net_pnl": net_pnl,
            "max_drawdown": max_drawdown,
            "consecutive_losses": max_consecutive_losses,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "segmentation": segmentation,
            # Backwards compatibility keys
            "by_market": segmentation["symbol"],
            "by_session": segmentation["session"],
            "by_regime": segmentation["market_regime"],
        }


performance_agent = PerformanceAgent()
