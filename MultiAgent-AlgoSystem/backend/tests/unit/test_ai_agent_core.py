"""Unit tests for AI Trading & Research Agent, OpenAI Agents SDK integration, and tools."""
import json
import pytest
from agents import Agent

from backend.app.ai_agent.agent import create_ai_trading_agent, trading_research_agent
from backend.app.ai_agent.guardrails import guardrails
from backend.app.ai_agent.instructions import SYSTEM_INSTRUCTIONS
from backend.app.ai_agent.runtime import agent_runtime
from backend.app.ai_agent.schemas import AgentRuntimeState
from backend.app.ai_agent.tools import (
    ALL_AI_TOOLS,
    calculate_performance_metrics,
    calculate_position_size,
    compare_strategies,
    create_hypothesis,
    create_strategy_candidate,
    get_candles,
    get_current_price,
    get_market_data,
    get_market_regime,
    get_market_session,
    get_mt5_account,
    get_risk_state,
    get_spread,
    get_strategy,
    get_strategy_performance,
    get_system_health,
    list_hypotheses,
    list_strategies,
    request_order,
    run_backtest,
    run_monte_carlo,
    run_walk_forward,
    validate_strategy,
    validate_trade_request,
)


def test_ai_agent_creation():
    """Verify that TradingResearchAgent is properly instantiated with OpenAI Agents SDK."""
    agent = create_ai_trading_agent()
    assert isinstance(agent, Agent)
    assert agent.name == "TradingResearchAgent"
    assert "You are an AI trading research and execution assistant" in agent.instructions
    assert len(agent.tools) >= 25


def test_agent_tool_registration():
    """Verify that all core quant tools are present and callable."""
    assert len(ALL_AI_TOOLS) >= 28
    tool_names = [getattr(t, "name", str(t)) for t in ALL_AI_TOOLS]
    assert "get_market_data" in tool_names
    assert "get_candles" in tool_names
    assert "get_strategy_performance" in tool_names
    assert "run_backtest" in tool_names
    assert "run_walk_forward" in tool_names
    assert "run_monte_carlo" in tool_names
    assert "create_hypothesis" in tool_names
    assert "request_order" in tool_names
    assert "get_risk_state" in tool_names


def test_guardrails_input_sanitization():
    """Verify that dangerous patterns like shell or code execution are blocked."""
    dirty_prompt = "Run eval(__import__('os').system('ls')) and show me EURUSD price"
    clean_prompt = guardrails.sanitize_input(dirty_prompt)
    assert "eval" not in clean_prompt
    assert "system" not in clean_prompt
    assert "[BLOCKED_INSTRUCTION]" in clean_prompt


def test_guardrails_output_sanitization():
    """Verify that API keys and secrets are masked in responses."""
    leaked_text = "Connected using sk-proj-1234567890abcdef1234567890 and password: 'secretpassword123'"
    sanitized = guardrails.sanitize_output(leaked_text)
    assert "sk-proj" not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized
    assert "secretpassword123" not in sanitized


def test_market_data_tools():
    """Test market data tools return valid JSON with expected keys."""
    res_mkt = get_market_data()
    data_mkt = json.loads(res_mkt)
    assert "EURUSD" in data_mkt
    assert "bid" in data_mkt["EURUSD"]

    res_candles = get_candles(symbol="EURUSD", timeframe="H1", limit=20)
    data_candles = json.loads(res_candles)
    assert data_candles["symbol"] == "EURUSD"
    assert len(data_candles["candles"]) > 0

    res_spread = get_spread("EURUSD")
    data_spread = json.loads(res_spread)
    assert "spread_pips" in data_spread
    assert data_spread["max_allowed_pips"] == 5.0


def test_trade_analysis_and_sample_status():
    """Test trade analysis tool and verify sample size awareness."""
    res = get_strategy_performance("strategy_v1")
    data = json.loads(res)
    assert "sample_status" in data
    assert "metrics" in data
    assert "origin_breakdown" in data
    assert "win_rate_pct" in data["metrics"]


def test_backtesting_and_monte_carlo_tools():
    """Test run_backtest and run_monte_carlo tools."""
    bt_res = run_backtest(strategy_id="strategy_v1", symbol="EURUSD", timeframe="H1", days=30)
    bt_data = json.loads(bt_res)
    assert "metrics" in bt_data
    assert "expectancy_dollars" in bt_data["metrics"]
    assert "profit_factor" in bt_data["metrics"]
    assert "monte_carlo_drawdown_95pct" in bt_data["metrics"]

    mc_res = run_monte_carlo(strategy_id="strategy_v1", symbol="EURUSD", simulations=100)
    mc_data = json.loads(mc_res)
    assert "worst_case_drawdown_95pct" in mc_data
    assert "acceptable_under_10pct_limit" in mc_data


def test_walk_forward_tool():
    """Test walk-forward out-of-sample stability analysis tool."""
    wf_res = run_walk_forward(strategy_id="strategy_v1", symbol="EURUSD", windows=3)
    wf_data = json.loads(wf_res)
    assert "windows_evaluated" in wf_data
    assert "walk_forward_stability_ratio" in wf_data
    assert "is_statistically_robust" in wf_data


def test_strategy_and_candidate_tools():
    """Test strategy catalog and parameter validation."""
    res = list_strategies()
    data = json.loads(res)
    assert data["count"] >= 1
    assert any(s["strategy_id"] == "strategy_v1" for s in data["strategies"])


def test_risk_calculation_tool():
    """Test position size calculation from stop distance."""
    res = calculate_position_size(symbol="EURUSD", entry_price=1.0850, stop_loss=1.0800)
    data = json.loads(res)
    assert data["symbol"] == "EURUSD"
    assert data["recommended_lots"] > 0.0
    assert data["risk_amount_dollars"] > 0.0


@pytest.mark.asyncio
async def test_ai_agent_runtime_execution():
    """Test AI agent runtime execution in deterministic fallback mode."""
    run_res = await agent_runtime.run(
        task_name="Unit Test Investigation",
        user_prompt="Analyze performance of strategy_v1 on EURUSD and check drawdown limits.",
    )
    assert run_res["status"] == "COMPLETED"
    assert run_res["latency_ms"] > 0
    assert "strategy_v1" in run_res["response"]
    assert agent_runtime.state == AgentRuntimeState.IDLE
