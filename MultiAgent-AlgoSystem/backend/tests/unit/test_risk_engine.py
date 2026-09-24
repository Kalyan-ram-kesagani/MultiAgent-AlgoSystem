"""Unit tests for Agent #7 Risk Engine safety mechanisms and sizing."""
import pytest
from backend.app.agents.risk.risk_engine import RiskEngine
from backend.app.schemas.risk import RiskEvaluationRequest


@pytest.fixture
def risk_engine(tmp_path):
    state_file = tmp_path / ".kill_switch_test.json"
    engine = RiskEngine(state_file=state_file)
    yield engine
    if state_file.exists():
        state_file.unlink(missing_ok=True)


def test_risk_engine_valid_order_approval(risk_engine):
    """Test standard valid EURUSD order approval and sizing."""
    req = RiskEvaluationRequest(
        strategy_id="strategy_v1",
        symbol="EURUSD",
        side="BUY",
        entry_price=1.08500,
        stop_loss=1.08200,  # 30 pips stop
        take_profit=1.09100,  # 60 pips TP (2R)
        account_equity=10000.0,
        account_balance=10000.0,
        current_spread_pips=1.2,
        open_positions_count=1,
        symbol_positions_count=0,
    )
    result = risk_engine.evaluate_order(req)
    assert result.is_approved is True
    assert result.calculated_lots > 0
    assert result.risk_amount_dollars == 100.0  # 1% of 10k
    assert len(result.rejection_reasons) == 0


def test_risk_engine_blocks_when_kill_switch_active(risk_engine):
    """Verify that manual or automatic kill switch strictly blocks all new orders."""
    risk_engine.engage_kill_switch("Manual emergency stop triggered", operator="OPERATOR")
    req = RiskEvaluationRequest(
        strategy_id="strategy_v1",
        symbol="EURUSD",
        side="BUY",
        entry_price=1.0850,
        stop_loss=1.0820,
        take_profit=1.0910,
        account_equity=10000.0,
        account_balance=10000.0,
        current_spread_pips=1.2,
        open_positions_count=0,
        symbol_positions_count=0,
    )
    result = risk_engine.evaluate_order(req)
    assert result.is_approved is False
    assert any("kill switch is ACTIVE" in r for r in result.rejection_reasons)
    assert result.calculated_lots == 0.0


def test_risk_engine_blocks_abnormal_spread(risk_engine):
    """Verify orders are rejected when spread exceeds safety limits."""
    req = RiskEvaluationRequest(
        strategy_id="strategy_v1",
        symbol="EURUSD",
        side="BUY",
        entry_price=1.0850,
        stop_loss=1.0820,
        take_profit=1.0910,
        account_equity=10000.0,
        account_balance=10000.0,
        current_spread_pips=8.5,  # Exceeds max 5.0 pips
        open_positions_count=0,
        symbol_positions_count=0,
    )
    result = risk_engine.evaluate_order(req)
    assert result.is_approved is False
    assert any("Spread too wide" in r for r in result.rejection_reasons)


def test_risk_engine_consecutive_losses_triggers_kill_switch(risk_engine):
    """Verify consecutive losses automatically trigger the circuit breaker."""
    risk_engine.record_trade_outcome(-50.0)
    risk_engine.record_trade_outcome(-40.0)
    assert risk_engine.kill_switch_active is False
    risk_engine.record_trade_outcome(-60.0)  # 3rd consecutive loss
    assert risk_engine.kill_switch_active is True
    assert "Consecutive loss limit" in risk_engine.kill_switch_reason
