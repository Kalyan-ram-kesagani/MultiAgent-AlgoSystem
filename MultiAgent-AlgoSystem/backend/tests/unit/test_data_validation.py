"""Unit tests for Data Agent validation rules and anomaly detection."""
from datetime import datetime, timedelta, timezone
from backend.app.agents.data.data_agent import DataAgent
from backend.app.schemas.market_data import BarData


def test_data_agent_detects_inverted_high_low():
    agent = DataAgent()
    now = datetime.now(timezone.utc)
    bad_bar = BarData(
        symbol="EURUSD",
        timeframe="H1",
        timestamp=now,
        open=1.0850,
        high=1.0800,  # High less than Low!
        low=1.0870,
        close=1.0820,
        volume=100.0,
        spread=1.0,
    )
    report = agent.validate_bars("EURUSD", "H1", [bad_bar])
    assert report.quality_status == "REJECTED"
    assert any(i.issue_type == "INVERTED_HIGH_LOW" for i in report.issues)


def test_data_agent_detects_duplicate_timestamps():
    agent = DataAgent()
    now = datetime.now(timezone.utc)
    bar1 = BarData(symbol="EURUSD", timeframe="H1", timestamp=now, open=1.08, high=1.09, low=1.07, close=1.08)
    bar2 = BarData(symbol="EURUSD", timeframe="H1", timestamp=now, open=1.08, high=1.09, low=1.07, close=1.08)

    report = agent.validate_bars("EURUSD", "H1", [bar1, bar2])
    assert any(i.issue_type == "DUPLICATE_TIMESTAMP" for i in report.issues)


def test_data_agent_clean_synthetic_data():
    agent = DataAgent()
    bars = DataAgent.generate_synthetic_data("EURUSD", "H1", num_bars=100)
    report = agent.validate_bars("EURUSD", "H1", bars)
    assert report.quality_status == "VALIDATED"
    assert report.valid_bars == 100
