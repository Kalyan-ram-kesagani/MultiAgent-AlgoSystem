# AI Trading & Research Agent Architecture

## Overview
The **TradingResearchAgent** is an autonomous, quantitative reasoning and research assistant powered by the official **OpenAI Agents SDK** (`openai-agents`). It operates inside a strictly controlled algorithmic trading architecture designed to prevent unhedged or unverified trades from ever reaching the broker.

```
              ┌────────────────────────────────────┐
              │     REAL AI TRADING AGENT           │
              │     OpenAI Agents SDK               │
              │                                    │
              │  Reasoning + Tool Calling           │
              │  Research + Analysis                │
              │  Strategy Investigation             │
              │  Performance Analysis               │
              │  Hypothesis Generation              │
              └───────────────┬────────────────────┘
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
       MARKET DATA       RESEARCH TOOLS    ANALYTICS
       MT5 DATA          BACKTEST           PERFORMANCE
       CANDLES           WALK-FORWARD       REGIMES
       SPREAD            MONTE CARLO        DRAWDOWN
       POSITIONS         STRATEGY TEST      TRADE ANALYSIS
```

---

## 1. System Prompt & Research Objective

The AI Agent operates under strict quant research rules:

```
You are an AI trading research and execution assistant operating inside a controlled algorithmic trading system.

Your primary objective is NOT to maximize win rate.
Your objective is to analyze market and strategy data, identify testable hypotheses, evaluate strategies using statistically and economically meaningful evidence, and make controlled trade requests when permitted.

You must:
- use tools instead of inventing data
- never fabricate market data or backtest results
- never claim certainty; distinguish facts from hypotheses
- identify insufficient sample sizes (<10: INSUFFICIENT DATA, 10-49: EARLY DATA, 50-99: PRELIMINARY, 100+: RESEARCHABLE)
- avoid overfitting; mandate train/test splits and walk-forward efficiency (>70%)
- consider transaction costs, spread (max 5.0 pips), and execution slippage
- respect risk limits; never bypass the Risk Engine
- never directly place broker orders (mt5.order_send is completely forbidden)
- never disable the Kill Switch or modify risk limits
- never expose secrets (API keys, passwords, database credentials)
- never deploy a strategy automatically to LIVE
- clearly explain failed experiments and preserve immutable history
- treat manual/external trades separately from system trades
```

---

## 2. OpenAI Agents SDK Implementation

### Agent Runtime (`backend/app/ai_agent/agent.py`)
```python
from agents import Agent
from backend.app.ai_agent.instructions import TRADING_RESEARCH_AGENT_INSTRUCTIONS
from backend.app.ai_agent.tools import ALL_AI_TOOLS
from backend.app.core.config import settings

trading_agent = Agent(
    name="TradingResearchAgent",
    model=settings.OPENAI_MODEL,  # e.g., "gpt-4o"
    instructions=TRADING_RESEARCH_AGENT_INSTRUCTIONS,
    tools=ALL_AI_TOOLS,
)
```

### Execution Flow (`backend/app/ai_agent/runtime.py`)
1. **Input Guardrail**: Scans prompt for forbidden shell commands or credential patterns.
2. **SDK Runner**: Uses `Runner.run(trading_agent, input=sanitized_prompt)`.
3. **Audit Logging**: Persists `AIAgentRun` record with tokens, latency, status, and associated tool calls (`AIToolCall`) in Supabase/PostgreSQL.
4. **Offline Fallback**: When `OPENAI_API_KEY` is absent or in offline testing, gracefully executes an automated quantitative research pipeline across real backtesting and regime tools rather than failing silently.

---

## 3. Tool Catalog (31 Real Tools)

Every tool has typed inputs, typed JSON outputs, rigorous error handling, and parameter boundaries:

### Market Data Tools (`backend/app/ai_agent/tools/market_data.py`)
- `get_market_data()`: Snapshot of major symbols (EURUSD, GBPUSD, XAUUSD) with live bids, asks, and spreads.
- `get_candles(symbol, timeframe, limit)`: OHLCV bars from MT5 or synthetic generator.
- `get_current_price(symbol)`: Real-time bid/ask and spread calculation.
- `get_spread(symbol)`: Validates spread against institutional threshold (<5.0 pips).
- `get_market_session()`: Asian, London, New York, or London/NY overlap.
- `get_market_regime(symbol)`: Classifies trend (BULL/BEAR), ranging, or high volatility.

### MetaTrader 5 Tools (`backend/app/ai_agent/tools/mt5_tools.py`)
- `get_mt5_account()`: Balance, equity, free margin, and leverage.
- `get_mt5_positions()`: Live open positions, PnL, stops, and tickets.
- `get_mt5_orders()`: Pending broker orders.
- `get_mt5_trade_history(days)`: Reconciled deals with origin filtering.
- `get_mt5_symbol_info(symbol)`: Digits, points, lot step, volume min/max.

### Performance Analytics Tools (`backend/app/ai_agent/tools/trade_analysis.py`)
- `get_strategy_performance(strategy_id)`: Expectancy, profit factor, win rate, Max DD.
- `analyze_trade_history(strategy_id)`: Segmented breakdown of wins, losses, and R-multiples.
- `analyze_drawdown(strategy_id)`: Peak-to-trough drawdown and recovery periods.
- `analyze_regimes(strategy_id)`: Performance segmented by market regime.
- `calculate_performance_metrics(strategy_id)`: Sharpe, Sortino, average win/loss.

### Research & Hypothesis Tools (`backend/app/ai_agent/tools/research.py`)
- `create_hypothesis(strategy_id, title, description, market_regime, rationale)`: Registers an immutable hypothesis.
- `list_hypotheses(status, strategy_id)`: Returns active and completed hypotheses.
- `get_hypothesis(hypothesis_id)`: Retrieves testable statements and status.
- `record_research_result(hypothesis_id, conclusion, evidence_json)`: Stores quantitative findings.

### Backtesting & Robustness Tools (`backend/app/ai_agent/tools/backtesting.py`)
- `run_backtest(strategy_id, symbol, timeframe, days, parameters_json)`: Full event-driven simulation.
- `run_walk_forward(strategy_id, symbol, windows)`: Out-of-sample temporal cross-validation.
- `run_monte_carlo(strategy_id, symbol, simulations)`: 95th percentile worst-case drawdown.
- `compare_strategies(baseline_id, candidate_id)`: Quant side-by-side comparison.
- `get_backtest_results(run_id)`: Retrieves stored backtest metrics.

### Strategy Lifecycle Tools (`backend/app/ai_agent/tools/strategy.py`)
- `get_strategy(strategy_id)`: Strategy parameter schema and rules.
- `list_strategies()`: Active registry strategies.
- `create_strategy_candidate(baseline_id, new_parameters_json, rationale)`: Creates unpromoted candidate version.
- `validate_strategy(strategy_id)`: Validates strategy code against backtest requirements.
- `get_strategy_versions(strategy_id)`: Version history and lineage.

### Risk & Order Proposal Tools (`backend/app/ai_agent/tools/risk.py`)
- `get_risk_state()`: Kill switch state, daily loss, drawdown, open exposure.
- `calculate_position_size(symbol, entry_price, stop_loss)`: Calculates 1% equity risk volume.
- `validate_trade_request(symbol, side, quantity, stop_loss, take_profit)`: Pre-flight risk check.
- `request_order(symbol, side, quantity, stop_loss, take_profit, strategy_id, reason)`: **The ONLY path to trade.** Emits proposal to Deterministic Risk Engine.

### System Health Tools (`backend/app/ai_agent/tools/system.py`)
- `get_system_health()`: Service statuses (MT5, Supabase, Risk Engine, EventBus).
- `get_agent_status()`: Runtime state, last task, current tool, heartbeat.
- `get_kill_switch_status()`: Engagement status, reason, operator, timestamp.
- `get_recent_events(limit)`: Real-time event log.

---

## 4. Runtime State Model
The frontend and supervisor track true runtime states:
- `IDLE`: Standing by for requests or scheduled research triggers.
- `THINKING`: Performing LLM reasoning and strategy analysis.
- `TOOL_CALL`: Executing a registered tool function.
- `RESEARCHING`: Formulating hypotheses and reviewing historical trades.
- `BACKTESTING`: Running event-driven simulation or walk-forward validation.
- `RISK_CHECK`: Evaluating an order proposal through the Deterministic Risk Engine.
- `EXECUTING`: Routing risk-approved order to MT5 DEMO.
- `WAITING_APPROVAL`: Strategy candidate ready for mandatory human review.
- `ERROR`: An unhandled exception occurred; system fails closed.
- `STOPPED`: Background supervisor halted or kill switch engaged.
