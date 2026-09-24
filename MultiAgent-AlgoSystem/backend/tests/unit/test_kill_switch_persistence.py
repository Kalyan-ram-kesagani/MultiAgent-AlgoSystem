"""Test kill switch persistence across application restarts."""
import pytest
from pathlib import Path
from backend.app.agents.risk.risk_engine import RiskEngine
from backend.app.schemas.risk import RiskEvaluationRequest


def test_kill_switch_persistence_lifecycle(tmp_path: Path):
    """
    Test cycle:
    1. Start engine with clean state
    2. Engage kill switch
    3. Simulate app restart by instantiating new RiskEngine with same state file
    4. Assert kill switch is still ACTIVE
    5. Attempt order -> assert REJECTED
    6. Disengage kill switch -> assert deactivation persisted
    7. Simulate restart again -> assert deactivated
    """
    state_file = tmp_path / ".kill_switch_state.json"

    # Step 1: Clean startup
    engine1 = RiskEngine(state_file=state_file)
    assert engine1.kill_switch_active is False

    # Step 2: Engage kill switch
    engine1.engage_kill_switch("Circuit breaker test", operator="TEST_OPERATOR")
    assert engine1.kill_switch_active is True
    assert state_file.exists()

    # Step 3: Simulate restart (new instance loading persisted state)
    engine2 = RiskEngine(state_file=state_file)
    assert engine2.kill_switch_active is True
    assert "Circuit breaker test" in engine2.kill_switch_reason

    # Step 5: Attempt order evaluation
    req = RiskEvaluationRequest(
        strategy_id="test_strat",
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
    res = engine2.evaluate_order(req)
    assert res.is_approved is False
    assert any("Emergency kill switch is ACTIVE" in r for r in res.rejection_reasons)

    # Step 6: Authorized explicit reset
    engine2.disengage_kill_switch(operator="AUTHORIZED_ADMIN")
    assert engine2.kill_switch_active is False

    # Step 7: Simulate another restart
    engine3 = RiskEngine(state_file=state_file)
    assert engine3.kill_switch_active is False
