# Quantitative Research & Overfitting Protection

## 1. Research Lifecycle & Continuous Feedback Loop

The system operates a continuous learning loop where live performance feeds directly into scientific hypothesis testing:

```
MT5 Broker (DEMO)
       ↓
Reconciled Trade History
       ↓
Supabase Database (Trades with Origin Tagging)
       ↓
Performance Analytics (Degradation Monitor)
       ↓
TradingResearchAgent (Detects Anomaly or Opportunity)
       ↓
Hypothesis Formulation (EXP-XXXX)
       ↓
Rigorous Testing:
├── Historical Event-Driven Backtest (Spread & Slippage included)
├── Walk-Forward Out-of-Sample Efficiency (>= 70%)
└── Monte Carlo Trade Resampling (95th percentile DD <= 10%)
       ↓
Decision:
├── REJECTED (Underperforming, overfitted, or high DD)
├── RESEARCH_REQUIRED (Sample size too low or inconclusive)
└── CANDIDATE_FOR_DEMO (Passed all criteria)
       ↓
Mandatory Human Approval Gate (Dashboard / API)
       ↓
Staged DEMO Deployment (Never directly to LIVE)
```

---

## 2. Statistical Sample Size Discipline

The AI Agent enforces strict sample size tiers to prevent hasty conclusions based on variance:

| Trade Sample Count | Classification | Allowed Agent Action |
|:---|:---|:---|
| `< 10` trades | **INSUFFICIENT DATA** | Flag as unverified; no parameter changes permitted. |
| `10 - 49` trades | **EARLY DATA** | Log preliminary observations; research only. |
| `50 - 99` trades | **PRELIMINARY** | Strategy testing and initial hypothesis formulation. |
| `100+` trades | **RESEARCHABLE** | Statistical tests, walk-forward splits, candidate promotion. |

---

## 3. Overfitting Safeguards

### Train / Test & Walk-Forward Validation
- Historical data is partitioned into rolling temporal windows.
- In-Sample (IS) optimization must demonstrate high Out-of-Sample (OOS) efficiency:
  $$\text{Walk-Forward Efficiency Ratio} = \frac{\text{Avg OOS Profit Factor}}{\text{Avg IS Profit Factor}} \ge 0.70$$
- If OOS performance degrades significantly compared to IS, the candidate is flagged as **OVERFITTED** and rejected.

### Monte Carlo Resampling
- Simulates 250 to 1,000 randomized permutations of trade returns without replacement.
- Determines the 95th percentile worst-case portfolio drawdown.
- If worst-case simulated drawdown exceeds **10.0%**, the strategy candidate is rejected.

### Economic Realism
- Backtest engine incorporates fixed broker commissions ($7/lot standard), live bid-ask spreads (1.5 pips base), and execution slippage points (5 points).
- Zero future-data leakage: indicators and signals are evaluated strictly on historical bar slices.

---

## 4. Immutable Experiment Records

All hypotheses, candidate versions, and backtest results are stored immutably in Supabase/PostgreSQL:
- `research_hypotheses`: Stores initial rationale, regime context, and formal statement.
- `strategy_versions`: Immutable parameter configurations (`strategy_v1.0.1`, `strategy_v1.1.0`) linked to baseline lineage.
- `experiments`: Auditable experiment ID (`EXP-XXXX`), baseline vs candidate metrics, and validation verdicts.
- **No Automatic Deployment**: Strategy candidates remain in `CANDIDATE_FOR_DEMO` status until explicit human confirmation.
