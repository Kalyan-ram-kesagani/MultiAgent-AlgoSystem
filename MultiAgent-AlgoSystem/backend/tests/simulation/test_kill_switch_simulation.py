"""Simulation tests for Circuit Breaker, Kill Switch, and Multi-Scale Position Sizing."""
import pytest
from backend.app.agents.risk.risk_engine import RiskEngine
from backend.app.schemas.risk import RiskEvaluationRequest


def test_micro_account_sizing():
    """Verify position sizing calculates correctly for a $200 account (blueprint example)."""
    engine = RiskEngine()
    req = RiskEvaluationRequest(
        strategy_id="strategy_v1",
        symbol="EURUSD",
        side="BUY",
        entry_price=1.0850,
        stop_loss=1.0830,  # 20 pips = 0.0020
        take_profit=1.0890,
        account_equity=200.0,
        account_balance=200.0,
        current_spread_pips=1.0,
        open_positions_count=0,
        symbol_positions_count=0,
    )
    result = engine.evaluate_order(req)
    assert result.is_approved is True
    # Risk 1% of $200 = $2.00
    assert result.risk_amount_dollars == 2.0
    # Stop distance = 20 pips ($200 per standard lot) -> 2 / 200 = 0.01 lots
    assert result.calculated_lots == 0.01


def test_kill_switch_blocks_simulated_burst():
    """Verify that engaging kill switch halts 100 consecutive incoming signals."""
    engine = RiskEngine()
    try:
        engine.engage_kill_switch("Automated simulation emergency test", operator="SIMULATOR")

        for i in range(100):
            req = RiskEvaluationRequest(
                strategy_id="strategy_v1",
                symbol="EURUSD",
                side="BUY" if i % 2 == 0 else "SELL",
                entry_price=1.0850,
                stop_loss=1.0800 if i % 2 == 0 else 1.0900,
                take_profit=1.0950 if i % 2 == 0 else 1.0750,
                account_equity=10000.0,
                account_balance=10000.0,
                current_spread_pips=1.2,
                open_positions_count=0,
                symbol_positions_count=0,
            )
            res = engine.evaluate_order(req)
            assert res.is_approved is False
            assert res.calculated_lots == 0.0
    finally:
        engine.disengage_kill_switch(operator="SIMULATOR_CLEANUP")

