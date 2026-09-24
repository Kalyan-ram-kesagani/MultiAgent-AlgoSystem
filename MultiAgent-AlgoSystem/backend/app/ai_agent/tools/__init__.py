"""AI Trading & Research Agent Tools Package."""
from backend.app.ai_agent.tools.market_data import (
    get_candles,
    get_current_price,
    get_market_data,
    get_market_regime,
    get_market_session,
    get_spread,
)
from backend.app.ai_agent.tools.mt5_tools import (
    get_mt5_account,
    get_mt5_orders,
    get_mt5_positions,
    get_mt5_symbol_info,
    get_mt5_trade_history,
)
from backend.app.ai_agent.tools.trade_analysis import (
    analyze_drawdown,
    analyze_regimes,
    analyze_trade_history,
    analyze_trade_sources,
    calculate_performance_metrics,
    get_strategy_performance,
)
from backend.app.ai_agent.tools.research import (
    create_experiment,
    create_hypothesis,
    get_experiment,
    get_hypothesis,
    list_hypotheses,
    record_research_result,
)
from backend.app.ai_agent.tools.backtesting import (
    compare_strategies,
    get_backtest_results,
    run_backtest,
    run_monte_carlo,
    run_walk_forward,
)
from backend.app.ai_agent.tools.strategy import (
    create_strategy_candidate,
    get_strategy,
    get_strategy_versions,
    list_strategies,
    validate_strategy,
)
from backend.app.ai_agent.tools.risk import (
    calculate_position_size,
    get_risk_state,
    request_order,
    validate_trade_request,
)
from backend.app.ai_agent.tools.system import (
    get_agent_status,
    get_kill_switch_status,
    get_recent_events,
    get_system_health,
)

from agents import function_tool

ALL_AI_TOOLS = [
    # Market Data
    function_tool(get_market_data),
    function_tool(get_candles),
    function_tool(get_current_price),
    function_tool(get_spread),
    function_tool(get_market_session),
    function_tool(get_market_regime),
    # MT5
    function_tool(get_mt5_account),
    function_tool(get_mt5_positions),
    function_tool(get_mt5_orders),
    function_tool(get_mt5_trade_history),
    function_tool(get_mt5_symbol_info),
    # Performance & Trade Analysis
    function_tool(analyze_trade_sources),
    function_tool(get_strategy_performance),
    function_tool(analyze_trade_history),
    function_tool(analyze_drawdown),
    function_tool(analyze_regimes),
    function_tool(calculate_performance_metrics),
    # Research & Hypotheses
    function_tool(create_hypothesis),
    function_tool(list_hypotheses),
    function_tool(get_hypothesis),
    function_tool(create_experiment),
    function_tool(get_experiment),
    function_tool(record_research_result),
    # Backtesting & Robustness
    function_tool(run_backtest),
    function_tool(run_walk_forward),
    function_tool(run_monte_carlo),
    function_tool(compare_strategies),
    function_tool(get_backtest_results),
    # Strategy
    function_tool(get_strategy),
    function_tool(list_strategies),
    function_tool(create_strategy_candidate),
    function_tool(validate_strategy),
    function_tool(get_strategy_versions),
    # Risk Gate
    function_tool(get_risk_state),
    function_tool(calculate_position_size),
    function_tool(validate_trade_request),
    function_tool(request_order),
    # System & Health
    function_tool(get_system_health),
    function_tool(get_agent_status),
    function_tool(get_kill_switch_status),
    function_tool(get_recent_events),
]

__all__ = [
    "ALL_AI_TOOLS",
    "get_market_data",
    "get_candles",
    "get_current_price",
    "get_spread",
    "get_market_session",
    "get_market_regime",
    "get_mt5_account",
    "get_mt5_positions",
    "get_mt5_orders",
    "get_mt5_trade_history",
    "get_mt5_symbol_info",
    "get_strategy_performance",
    "analyze_trade_history",
    "analyze_drawdown",
    "analyze_regimes",
    "calculate_performance_metrics",
    "create_hypothesis",
    "list_hypotheses",
    "get_hypothesis",
    "record_research_result",
    "run_backtest",
    "run_walk_forward",
    "run_monte_carlo",
    "compare_strategies",
    "get_backtest_results",
    "get_strategy",
    "list_strategies",
    "create_strategy_candidate",
    "validate_strategy",
    "get_strategy_versions",
    "get_risk_state",
    "calculate_position_size",
    "validate_trade_request",
    "request_order",
    "get_system_health",
    "get_agent_status",
    "get_kill_switch_status",
    "get_recent_events",
]
