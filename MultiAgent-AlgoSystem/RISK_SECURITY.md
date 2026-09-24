# Risk Management & Security Architecture

## 1. Core Principle: Zero Direct Execution

The LLM/AI has **ZERO direct access** to MetaTrader 5 execution functions (`mt5.order_send`).

The AI can only call:
```python
request_order(
    symbol="EURUSD",
    side="BUY",
    quantity=0.1,
    stop_loss=1.0750,
    take_profit=1.0950,
    strategy_id="strategy_v1",
    reason="Pullback to 20 EMA in London session with spread 1.2 pips",
)
```

### Order Request Pipeline
```
AI Agent
   ↓
request_order(...)
   ↓
Kill Switch Check (Persistent)
   ↓
MT5 Terminal Connectivity Gate
   ↓
Deterministic Risk Engine (evaluate_order)
   ├── Drawdown Gate (< 10%)
   ├── Daily Loss Gate (< 3%)
   ├── Max Positions Gate (<= 5)
   ├── Max Symbol Exposure Gate (<= 2)
   ├── Spread Gate (<= 5.0 pips)
   └── Mandatory Stop Loss Gate (positive & directional)
   ↓
Risk Approved?
   ├── NO  ──> Log Rejection to Supabase DB & EventBus ──> Return rejection reason to AI
   └── YES ──> Execution Engine ──> MT5 Gateway (DEMO Only) ──> Supabase DB
```

If rejected, the AI receives:
```json
{
    "approved": false,
    "reason": "Spread too wide for EURUSD (5.4 > 5.0 pips)",
    "risk_check": {
        "is_approved": false,
        "rejection_reasons": ["Spread too wide for EURUSD (5.4 > 5.0 pips)"]
    }
}
```
The AI **cannot override or retry around** the rejection.

---

## 2. Deterministic Risk Engine Constraints

The Risk Engine operates entirely in pure Python logic independent of LLM parameters:
- **Maximum Risk Per Trade**: Fixed at 1.0% of current equity.
- **Maximum Daily Loss**: Fixed at 3.0% of equity (realized + unrealized).
- **Maximum Account Drawdown**: Hard stop at 10.0%. Tripping this engages the emergency kill switch.
- **Maximum Open Positions**: 5 simultaneous trades system-wide.
- **Maximum Symbol Exposure**: 2 simultaneous trades per currency pair.
- **Spread Restriction**: Market orders blocked if spread > 5.0 pips.
- **Mandatory Stop Loss**: Orders without a positive stop loss or with an inverted stop loss (e.g. BUY SL >= entry) are immediately rejected.
- **Position Sizing**: Mathematically quantized to broker lot step:
  $$\text{Lots} = \frac{\text{Account Equity} \times 0.01}{|\text{Entry} - \text{Stop Loss}| \times \text{Contract Size}}$$

---

## 3. Persistent Dual-State Kill Switch

The Kill Switch ensures absolute emergency stop across power failures, process crashes, and container restarts:
1. **Local Disk Persistence**: Serialized atomic write to `.kill_switch_state.json`.
2. **Database Persistence**: Synchronized with `kill_switch_state` table in Supabase/PostgreSQL.
3. **Fail-Closed Startup**: On backend startup, `risk_engine.sync_with_db()` checks both sources. If *either* source has `is_active=True`, the kill switch remains engaged.
4. **Emergency Disengage Protocol**: Only human operators via dashboard or authorized API can disengage the kill switch with a mandatory operator name and audit trail.

---

## 4. Trade Origin Classification & Discretionary Isolation

Broker accounts frequently experience manual trades or trades placed by third-party EAs. The system prevents contaminated performance attribution:
- `SYSTEM_GENERATED`: Orders initiated through `request_order` and matched against system `orders` records.
- `MANUAL`: Trades initiated directly by a human on the MT5 terminal.
- `EXTERNAL`: Trades initiated by an external EA or unknown magic number.
- `UNKNOWN`: Unclassified trade deals.

**Attribution Rule**: `PerformanceAgent` and `analyze_trade_history` filter strictly for `origin == 'SYSTEM_GENERATED'` when calculating strategy expectancy, win rates, and degradation signals. Manual and external trades are audited in the journal but completely isolated from AI strategy evaluations.

---

## 5. Security & Credential Isolation

- **Zero Client Exposure**: Frontend communicates exclusively with the FastAPI backend.
- **Secret Redaction**: `OPENAI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and `MT5_PASSWORD` are loaded through server-side environment variables and masked in all logs and telemetry (`sk-***`, `sbp_***`).
- **Input Guardrails**: `backend/app/ai_agent/guardrails.py` intercepts prompts containing dangerous shell patterns (`sh`, `bash`, `exec`, `eval`, `import os`).
- **DEMO Trading Lock**: `TRADING_MODE` defaults to `DEMO`. Live execution is hard-locked (`LIVE_TRADING_ACKNOWLEDGED = False`).
