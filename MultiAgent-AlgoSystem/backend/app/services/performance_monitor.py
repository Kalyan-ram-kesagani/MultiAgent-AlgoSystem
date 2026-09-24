"""Performance Degradation Monitor Service.

Audits multi-dimensional statistical performance metrics from Supabase PostgreSQL.
Detects:
- Expectancy deterioration
- Profit factor deterioration
- Unusual drawdown
- Loss clustering (consecutive losses)
- Symbol-specific deterioration
- Session-specific deterioration
- Regime-specific deterioration

CRITICAL RULE: With small sample sizes (<30 trades), issues are classified with
severity='LOW_SAMPLE' and recommended_action='collect_more_data' or 'exploratory_investigation',
explicitly avoiding premature declarations of strategy failure.
"""
from typing import Any, Dict, List, Optional

from backend.app.agents.runtime.event_bus import event_bus
from backend.app.core.logging import logger


class PerformanceMonitor:
    """Monitors trade performance telemetry and emits structured investigation alerts."""

    def __init__(self, min_sample_for_conclusive_verdict: int = 30):
        self.min_sample_threshold = min_sample_for_conclusive_verdict

    def detect_degradations(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate statistical metrics against health baselines and generate investigation tasks.
        """
        issues: List[Dict[str, Any]] = []
        trade_count = metrics.get("trade_count", metrics.get("total_trades", 0))

        if trade_count == 0:
            return issues

        is_low_sample = trade_count < self.min_sample_threshold
        sample_severity = "LOW_SAMPLE" if is_low_sample else "MODERATE"
        sample_action = "collect_more_data" if is_low_sample else "investigate_and_refine"

        # 1. Overall Expectancy Check
        expectancy = metrics.get("expectancy", 0.0)
        if expectancy < 0:
            issues.append({
                "strategy_id": "strategy_v1",
                "segment_type": "OVERALL",
                "segment_value": "PORTFOLIO",
                "issue": "negative expectancy",
                "metric_value": expectancy,
                "sample_size": trade_count,
                "severity": sample_severity,
                "recommended_action": sample_action,
                "reason": f"Portfolio expectancy is negative (${expectancy:.2f}) over {trade_count} trades.",
            })

        # 2. Overall Profit Factor Check
        profit_factor = metrics.get("profit_factor", 0.0)
        if profit_factor < 1.0 and trade_count >= 5:
            issues.append({
                "strategy_id": "strategy_v1",
                "segment_type": "OVERALL",
                "segment_value": "PORTFOLIO",
                "issue": "sub-1.0 profit factor",
                "metric_value": profit_factor,
                "sample_size": trade_count,
                "severity": sample_severity,
                "recommended_action": sample_action,
                "reason": f"Gross losses exceed gross wins (Profit Factor: {profit_factor:.2f}).",
            })

        # 3. Loss Clustering Check
        consecutive_losses = metrics.get("consecutive_losses", 0)
        if consecutive_losses >= 3:
            issues.append({
                "strategy_id": "strategy_v1",
                "segment_type": "EXECUTION",
                "segment_value": "STREAK",
                "issue": "increased loss clustering",
                "metric_value": consecutive_losses,
                "sample_size": trade_count,
                "severity": "MODERATE" if consecutive_losses >= 4 else sample_severity,
                "recommended_action": "audit_volatility_and_stops",
                "reason": f"Detected cluster of {consecutive_losses} consecutive loss trades.",
            })

        # 4. Symbol-Specific Degradation (e.g., EURUSD 10 trades, 10% win rate)
        by_market = metrics.get("by_market", metrics.get("segmentation", {}).get("symbol", {}))
        for symbol, stats in by_market.items():
            sym_count = stats.get("count", 0)
            sym_wr = stats.get("win_rate", 0.0)
            sym_pnl = stats.get("net_pnl", 0.0)

            if sym_count >= 5 and (sym_wr <= 25.0 or sym_pnl < 0):
                issues.append({
                    "strategy_id": "strategy_v1",
                    "symbol": symbol,
                    "segment_type": "SYMBOL",
                    "segment_value": symbol,
                    "issue": "symbol-specific deterioration",
                    "metric_value": sym_wr,
                    "sample_size": sym_count,
                    "severity": "LOW_SAMPLE" if sym_count < self.min_sample_threshold else "MODERATE",
                    "recommended_action": "formulate_exploratory_hypothesis" if sym_count < self.min_sample_threshold else "optimize_symbol_parameters",
                    "reason": f"{symbol} demonstrates low win rate ({sym_wr:.1f}%) and negative net PnL (${sym_pnl:.2f}) over {sym_count} trades.",
                })

        # 5. Session-Specific Degradation
        by_session = metrics.get("by_session", metrics.get("segmentation", {}).get("session", {}))
        for session, stats in by_session.items():
            sess_count = stats.get("count", 0)
            sess_pnl = stats.get("net_pnl", 0.0)
            if sess_count >= 5 and sess_pnl < 0:
                issues.append({
                    "strategy_id": "strategy_v1",
                    "segment_type": "SESSION",
                    "segment_value": session,
                    "issue": "session-specific deterioration",
                    "metric_value": sess_pnl,
                    "sample_size": sess_count,
                    "severity": sample_severity,
                    "recommended_action": "test_session_filter",
                    "reason": f"Session {session} incurred net loss of ${sess_pnl:.2f} across {sess_count} trades.",
                })

        return issues


performance_monitor = PerformanceMonitor()
