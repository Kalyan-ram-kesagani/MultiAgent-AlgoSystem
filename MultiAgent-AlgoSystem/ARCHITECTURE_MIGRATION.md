# Architecture Migration Document

## Autonomous AI Trading & Research System
**Migration from 11-Agent Prototype Architecture to Unified Real AI Agent + Deterministic Infrastructure**

---

## 1. Current Architecture

The existing system was built as an 11-agent prototype, with each specialized area represented as an individual "agent" in an Agent Registry:
1. `#1 Orchestrator Agent`: High-level coordination & task routing.
2. `#2 Research Agent`: Hypothesis creation & experiment logging.
3. `#3 Data Agent`: Synthetic data generation & OHLCV bar auditing.
4. `#4 Strategy Agent`: Strategy registry & signal generation rules.
5. `#5 AI/ML Agent`: TimeSeriesSplit feature importance & regime classification.
6. `#6 Backtest Agent`: Event-driven simulation, slippage, spread, Monte Carlo permutations.
7. `#7 Risk Agent`: Position sizing, drawdown enforcement, circuit breaker kill switch.
8. `#8 Execution Agent`: MT5 order placement, idempotency caching, broker reconciliation.
9. `#9 Monitoring Agent`: Telemetry collector, MT5 watchdog, spread anomaly detection.
10. `#10 Journal Agent`: Automated trade journaling, R-multiples, MFE/MAE.
11. `#11 Performance Agent`: Statistical attribution, win rate, expectancy, degradation checks.

### Current Limitations
- While modular, several "agents" were deterministic software modules rather than reasoning entities, causing confusion in the UI with artificial "ACTIVE/WAITING" states.
- No direct integration with the modern OpenAI Agents SDK for autonomous, multi-turn reasoning and tool-calling.
- Kill switch state was stored primarily in a local JSON file (`.kill_switch_state.json`), leaving potential synchronization gaps with database state across cluster or container restarts.
- MT5 deals imported from the broker lacked clear origin classification (`SYSTEM_GENERATED` vs `MANUAL` vs `EXTERNAL`), risking attribution of manual user discretionary trades to algorithmic strategy performance.

---

## 2. Target Architecture

```
                    ┌─────────────────────────┐
                    │     REACT DASHBOARD      │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │       FASTAPI API        │
                    └────────────┬────────────┘
                                 │
                                 ▼
              ┌────────────────────────────────────┐
              │     REAL AI TRADING AGENT           │
              │     OpenAI Agents SDK               │
              │                                    │
              │  Reasoning + Tool Calling           │
              │  Research + Analysis                │
              │  Strategy Investigation             │
              │  Performance Analysis                │
              │  Hypothesis Generation               │
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
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                    ┌──────────────────────┐
                    │   DETERMINISTIC      │
                    │     RISK ENGINE      │
                    │                      │
                    │ Position sizing      │
                    │ Max risk             │
                    │ Drawdown limits      │
                    │ Exposure             │
                    │ Daily loss           │
                    │ Kill switch          │
                    └──────────┬───────────┘
                               │
                         APPROVED?
                         /       \
                       NO         YES
                       │           │
                       ▼           ▼
                    JOURNAL    EXECUTION ENGINE
                                   │
                                   ▼
                                  MT5
                                   │
                                   ▼
                              SUPABASE DB
```

---

## 3. Reusable Components

The existing deterministic codebase contains high-quality implementations that are preserved and mapped directly into services and tool providers:
- **MT5 Gateway Client** (`trading/execution/mt5_client.py`): Robust MetaTrader 5 Python integration, tick latency monitoring, position reconciliation, deal fetching, and fallback simulation mode.
- **Risk Engine Core** (`backend/app/agents/risk/risk_engine.py`): Exact position sizing from stop distance, daily loss, drawdown limits, and consecutive loss thresholds.
- **Backtest Engine** (`backend/app/agents/backtest/backtest_engine.py`): Event-driven simulation, spread/slippage modeling, and Monte Carlo 95% worst-case drawdown permutations.
- **Strategy Registry & Indicators** (`strategies/` and `backend/app/agents/strategy/strategy_agent.py`): Deterministic indicators (EMA, ATR, RSI, Donchian) and immutable strategy definitions.
- **Journal & Trade Reconciler** (`backend/app/agents/journal/journal_agent.py` & `backend/app/services/mt5_reconciler.py`): Automated trade logging, R-multiple auditing, MFE/MAE recording.
- **Telemetry Collector** (`backend/app/services/mt5_collector.py`): Background polling of MT5 ticks and telemetry.
- **Database Schema & Base Models** (`backend/app/models/`): SQLAlchemy models for trades, positions, experiments, hypotheses, strategies, and system events.

---

## 4. Components to Modify

1. **Risk Engine & Kill Switch** (`backend/app/agents/risk/risk_engine.py`):
   - Dual-persistence: Synchronize kill switch state between `.kill_switch_state.json` and Supabase/PostgreSQL (`circuit_breaker_states` table).
   - Ensure fail-closed behavior: If state is inaccessible or either store indicates active kill switch, all order requests are immediately rejected.
2. **MT5 Reconciler** (`backend/app/services/mt5_reconciler.py`):
   - Tag all broker deals with an explicit `origin` attribute:
     - `SYSTEM_GENERATED`: Deals matching an approved system `Order`.
     - `MANUAL`: Discretionary trades placed directly by user in MT5 client.
     - `EXTERNAL`: Trades generated by third-party EAs.
3. **Performance Analytics** (`backend/app/agents/performance/performance_agent.py`):
   - Filter metrics to strictly evaluate `SYSTEM_GENERATED` trades for AI strategy attribution, while separately tracking `MANUAL` / `EXTERNAL` trading metrics.
4. **App Lifespan & Supervisor** (`backend/app/main.py`):
   - Replace the legacy 11-agent startup loop with the `AIBackgroundSupervisor` coordinating the single AI agent runtime, MT5 telemetry, and trade reconciliation.
5. **Frontend Agent Control Center** (`frontend/src/pages/AgentControlCenterPage.tsx`):
   - Replace the 11 fake agent cards with:
     - Unified **AI Trading & Research Agent** status card with actual state (`IDLE`, `THINKING`, `RESEARCHING`, `BACKTESTING`, etc.).
     - **Deterministic System Services** health grid (MT5 Gateway, Supabase, Risk Engine, Execution Engine, Kill Switch, Backtest Engine, Monitoring).
     - **AI Activity & Experiment History** feed.

---

## 5. New Components

1. **`backend/app/ai_agent/`**:
   - `agent.py`: OpenAI Agents SDK `Agent` definition ("TradingResearchAgent").
   - `instructions.py`: Quant research system instructions enforcing expectancy over raw win rate, out-of-sample discipline, and strict risk gating.
   - `runtime.py`: Agent execution runner, status manager, run logger, and event dispatcher.
   - `schemas.py`: Pydantic input/output schemas for all AI tools.
   - `guardrails.py`: Input/output sanitization preventing arbitrary code execution.
   - `background_supervisor.py`: Background monitor detecting performance degradation and orchestrating autonomous research.
2. **`backend/app/ai_agent/tools/`**:
   - `market_data.py`: `get_market_data`, `get_candles`, `get_current_price`, `get_spread`, `get_market_session`, `get_market_regime`
   - `mt5_tools.py`: `get_mt5_account`, `get_mt5_positions`, `get_mt5_orders`, `get_mt5_trade_history`, `get_mt5_symbol_info`
   - `trade_analysis.py`: `get_strategy_performance`, `analyze_trade_history`, `analyze_drawdown`, `analyze_regimes`, `calculate_performance_metrics`
   - `research.py`: `create_hypothesis`, `list_hypotheses`, `get_hypothesis`, `record_research_result`
   - `backtesting.py`: `run_backtest`, `run_walk_forward`, `run_monte_carlo`, `compare_strategies`, `get_backtest_results`
   - `strategy.py`: `get_strategy`, `list_strategies`, `create_strategy_candidate`, `validate_strategy`, `get_strategy_versions`
   - `risk.py`: `get_risk_state`, `calculate_position_size`, `validate_trade_request`, `request_order`
   - `system.py`: `get_system_health`, `get_agent_status`, `get_kill_switch_status`, `get_recent_events`
3. **`backend/app/models/ai_audit.py`**:
   - `AIAgentRun`: Tracks AI runs, task, model, status, latency.
   - `AIToolCall`: Logs every tool execution, input parameters, and returned output.
   - `OrderRequest`: Records all trade proposals submitted by the AI to the Risk Engine.

---

## 6. Data Flow

```
[ Market Ticks / MT5 Deals ]
          │
          ▼
   (MT5 Reconciler)
          │
          ▼ (Classify: SYSTEM / MANUAL / EXTERNAL)
   [ Supabase DB: trades ]
          │
          ▼
  (Performance Service)
          │
          ▼ (Statistical Degradation / Opportunity Alert)
  [ AI Trading & Research Agent ]
          │
          ├──> [ Research Tools: Hypotheses, Walk-Forward, Monte Carlo ]
          │          │
          │          ▼
          │    [ Immutable Experiments: PENDING_HUMAN_REVIEW ]
          │
          └──> [ Order Request: request_order(...) ]
                     │
                     ▼
             (Deterministic Risk Engine)
                     │
            ┌────────┴────────┐
         APPROVED          REJECTED
            │                 │
            ▼                 ▼
   (Execution Engine)   [ Journal / EventBus: Order Rejected ]
            │
            ▼
      [ MT5 Broker ]
```

---

## 7. Security & Risk Flow

1. **Non-Bypassable Risk Boundary**: The AI Agent possesses zero access to MT5 order sending functions (`mt5.order_send`). It can only emit an `OrderRequest` schema via `request_order`.
2. **Order Gate Pipeline**:
   - `Kill Switch Check`: If kill switch is active (persisted on disk or DB), order immediately returns `{ "approved": false, "reason": "Kill switch engaged" }`.
   - `Trading Mode Lock`: Must be `DEMO` or `SANDBOX`. `LIVE` is strictly disabled.
   - `Spread Validation`: Spread must be `< 5.0 pips`.
   - `Position & Exposure Limits`: Max 5 open positions, max 2 open per symbol.
   - `Drawdown & Daily Loss Check`: Max daily loss 3%, max drawdown 10%.
   - `Stop-Loss Requirement`: All requests must include an explicit stop-loss price. Sizing is computed strictly from stop distance.
3. **Credentials Isolation**: OpenAI API keys, Supabase credentials, and MT5 logins are kept strictly on the backend and never exposed to the frontend or LLM tool payloads.
4. **Sandboxed Code Execution**: No `eval()`, `exec()`, or shell command execution tools are provided to the AI.

---

## 8. Migration Plan

- **Step 1**: Install `openai-agents>=0.22.0` and configure settings in `backend/app/core/config.py`.
- **Step 2**: Create `backend/app/models/ai_audit.py` and enhance `Trade` model with `origin`.
- **Step 3**: Implement `backend/app/ai_agent/` core, instructions, schemas, guardrails, and tools.
- **Step 4**: Enhance Risk Engine with DB kill switch persistence and implement `request_order` flow.
- **Step 5**: Update MT5 reconciler for manual/external deal classification.
- **Step 6**: Wire API endpoints (`/api/ai/*`, `/api/orders/request`) and connect `AIBackgroundSupervisor`.
- **Step 7**: Update frontend `AgentControlCenterPage.tsx` with AI Cockpit and System Services.
- **Step 8**: Execute comprehensive unit, integration, and simulation test suite.
