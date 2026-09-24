# Autonomous AI Trading System — Master Implementation

A modular, risk-controlled, AI-assisted automated trading and research platform capable of market data ingestion and auditing, deterministic strategy execution, walk-forward out-of-sample backtesting, MetaTrader 5 order execution, pre-trade risk sizing, automated journaling, and real-time dashboard observability.

---

## Core Safety Architecture

> [!IMPORTANT]
> **Non-Bypassable Risk Control**: No strategy or AI component may bypass the Risk Engine. All orders pass `Signal -> Risk Validation Gate -> Execution Engine -> MT5`. The Orchestrator and AI models are strictly forbidden from placing live trades directly.

```
       [ STRATEGY / AI AGENT ]
                  │
                  ▼
         [ RISK ENGINE GATE ]  ◄──── [ HARD KILL SWITCH (Manual + Auto) ]
                  │
      (Approved Orders Only)
                  │
                  ▼
         [ EXECUTION AGENT ]
                  │
                  ▼
      [ METATRADER 5 GATEWAY ]
                  │
                  ▼
             [ BROKER ]
```

---

## 11 Decoupled Agents

1. **#1 Orchestrator Agent**: High-level workflow coordinator, task decomposition, and live deployment gatekeeper. Cannot place trades directly.
2. **#2 Research Agent**: Formulates testable hypotheses and experiment designs (`EXP-XXXXX`).
3. **#3 Data Agent**: Collects, validates (gap detection, bad ticks, spread spikes), and stores OHLCV bars without overwriting historical data.
4. **#4 Strategy Agent**: Maintains immutable strategy versions and executes deterministic mathematical rules.
5. **#5 AI/ML Agent**: Regime classification (Trend Up/Down, Range, High Vol) and walk-forward signal filtering.
6. **#6 Backtest Agent**: Event-driven simulation with realistic spread, slippage, commission, and Monte Carlo 95% drawdown permutations.
7. **#7 Risk Agent**: Independent risk engine calculating lot sizing from actual stop distance and enforcing drawdown, daily loss, and consecutive loss limits.
8. **#8 Execution Agent**: Idempotent order placement, broker response capture, and position reconciliation.
9. **#9 Monitoring Agent**: Real-time heartbeat, MT5 link watchdog, execution latency, and abnormal spread alerts.
10. **#10 Journal Agent**: Automated trade logging, R-multiple auditing, MFE/MAE recording.
11. **#11 Performance Agent**: Multi-dimensional statistical attribution across market, session, and regime.

---

## Technology Stack

- **Backend**: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy (asyncio), SQLite (development fallback) & PostgreSQL (Docker), Uvicorn.
- **Trading**: MetaTrader 5 (MQL5 EA + Python integration).
- **ML / Analytics**: NumPy, Pandas, scikit-learn, SciPy.
- **Frontend**: React 18, Vite, TypeScript, Vanilla CSS design system.
- **Infrastructure**: Docker Compose, structured JSON logging.

---

## Quickstart

### 1. Backend Setup & Tests
```bash
# Activate virtual environment
.\.venv\Scripts\activate

# Run test suite
pytest backend/tests/ -v

# Start FastAPI server
python scripts/run_system.py --server
```
API Documentation will be live at `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup
```bash
cd frontend
npm run dev
```
Dashboard cockpit will be live at `http://localhost:5173`.

### 3. CLI Management Commands
```bash
# Check MT5 connection
python scripts/run_system.py --test-mt5

# Run sample backtest on EURUSD
python scripts/run_system.py --backtest

# Manually trigger Emergency Kill Switch
python scripts/run_system.py --kill-switch on
```

---

## License
Proprietary & Confidential. Built for Autonomous Algorithmic Trading Research.
