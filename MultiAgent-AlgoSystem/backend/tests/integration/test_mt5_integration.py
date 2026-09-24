"""Tests for MT5 Gateway multi-environment modes, safety locks, and execution guardrails."""
import pytest
from datetime import datetime, timezone
from backend.app.core.config import Settings, settings
from backend.app.agents.execution.execution_agent import ExecutionAgent
from backend.app.schemas.trading import SignalCreate
from trading.execution.mt5_client import MT5Client, MT5SafetyException, mt5_client


def test_settings_secret_masking():
    """Verify secrets and passwords are never exposed in safe dict dumps."""
    s = Settings(
        ENVIRONMENT="DEMO",
        MT5_PASSWORD="super_secret_broker_password",
        SECRET_KEY="internal_jwt_secret_token",
    )
    safe = s.get_safe_dict()
    assert safe["MT5_PASSWORD"] == "********"
    assert safe["SECRET_KEY"] == "********"


def test_environment_mode_properties():
    """Verify is_sandbox, is_demo, and is_live properties."""
    s_sandbox = Settings(ENVIRONMENT="SANDBOX")
    assert s_sandbox.is_sandbox is True
    assert s_sandbox.is_demo is False
    assert s_sandbox.is_live is False

    s_dev = Settings(ENVIRONMENT="DEVELOPMENT")
    assert s_dev.is_sandbox is True

    s_demo = Settings(ENVIRONMENT="DEMO")
    assert s_demo.is_demo is True
    assert s_demo.is_sandbox is False

    s_live = Settings(ENVIRONMENT="LIVE")
    assert s_live.is_live is True


def test_sandbox_client_simulation(monkeypatch):
    """Verify MT5Client in sandbox mode operates safely in-memory without real MT5."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "SANDBOX")
    client = MT5Client()
    connected = client.connect()
    assert connected is True
    assert client.is_simulation_mode is True

    prices = client.get_symbol_price("EURUSD")
    assert prices["bid"] > 0
    assert prices["ask"] >= prices["bid"]

    res = client.place_order(
        symbol="EURUSD",
        side="BUY",
        volume=0.10,
        price=1.0850,
        sl=1.0820,
        tp=1.0910,
    )
    assert res["success"] is True
    assert res["ticket"] > 0
    assert "Simulation" in res["message"]


@pytest.mark.asyncio
async def test_execution_agent_duplicate_order_protection(monkeypatch):
    """Verify duplicate signals within the idempotency window are rejected."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "SANDBOX")
    mt5_client.connect()

    agent = ExecutionAgent()
    sig = SignalCreate(
        strategy_id="test_strat",
        strategy_version="1.0.0",
        symbol="EURUSD",
        direction="BUY",
        timeframe="H1",
        timestamp=datetime.now(timezone.utc),
        suggested_entry=1.0850,
        suggested_sl=1.0820,
        suggested_tp=1.0910,
        risk_points=0.0030,
    )

    # First execution should succeed
    res1 = await agent.execute_signal(sig)
    assert res1["status"] == "FILLED"

    # Immediate second execution with identical signature must be rejected by idempotency gate
    res2 = await agent.execute_signal(sig)
    assert res2["status"] == "REJECTED"
    assert any("Duplicate order protection" in r for r in res2["rejection_reasons"])
