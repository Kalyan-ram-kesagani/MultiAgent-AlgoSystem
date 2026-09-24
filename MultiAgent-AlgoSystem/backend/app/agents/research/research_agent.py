"""Agent #2 — Research Agent: Hypothesis Formulation, Literature/Empirical Synthesis, and Experiment Design."""
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.research import Experiment, Hypothesis
from backend.app.schemas.research import ExperimentCreate, HypothesisCreate


class ResearchAgent:
    """Formulates testable, falsifiable hypotheses and structures rigorous test plans."""

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db = db_session

    async def create_hypothesis(self, req: HypothesisCreate) -> Hypothesis:
        """Formulate and persist a testable trading hypothesis."""
        hypothesis_id = f"HYP-{uuid.uuid4().hex[:6].upper()}"
        record = Hypothesis(
            hypothesis_id=hypothesis_id,
            title=req.title,
            hypothesis_statement=req.hypothesis_statement,
            reasoning=req.reasoning,
            test_plan=req.test_plan,
            success_metric=req.success_metric,
            failure_condition=req.failure_condition,
            status="PROPOSED",
        )
        if self.db:
            self.db.add(record)
            await self.db.commit()
            await self.db.refresh(record)
        return record

    async def formulate_hypotheses_from_investigation(
        self,
        investigation: Dict[str, Any],
    ) -> List[Hypothesis]:
        """
        Synthesize empirical degradation telemetry into testable, falsifiable hypotheses.
        """
        symbol = investigation.get("symbol", "EURUSD")
        issue = investigation.get("issue", "negative expectancy")
        sample_size = investigation.get("sample_size", 10)
        segment_type = investigation.get("segment_type", "OVERALL")

        hypotheses_to_create = []

        if "volatility" in issue.lower() or segment_type in ("OVERALL", "SYMBOL"):
            # Hypothesis 1: Volatility filter hypothesis
            hypotheses_to_create.append(HypothesisCreate(
                title=f"Volatility Regime Filter Hypothesis for {symbol}",
                hypothesis_statement=f"Strategy performance on {symbol} may deteriorate during elevated volatility regimes due to spread expansion and premature stop hits.",
                reasoning=f"Empirical trade review reveals negative expectancy (${investigation.get('metric_value', -1.21):.2f}) over {sample_size} deals, often exiting via stop loss during high-volatility sessions.",
                test_plan="Apply ATR volatility threshold (skip trades when ATR14 > 1.5x of 50-period average) and backtest across historical bars using walk-forward cross-validation.",
                success_metric="Expectancy improves from negative to >$0.50 with Profit Factor > 1.25 on out-of-sample data.",
                failure_condition="Out-of-sample Profit Factor remains < 1.0 or trade frequency is reduced by more than 50%.",
            ))

        if "session" in issue.lower() or segment_type in ("OVERALL", "SESSION", "SYMBOL"):
            # Hypothesis 2: Session timing filter hypothesis
            hypotheses_to_create.append(HypothesisCreate(
                title=f"Trading Session Liquidity Hypothesis for {symbol}",
                hypothesis_statement=f"Strategy win rate on {symbol} may improve if entries are restricted to London/New York overlap where institutional liquidity is highest.",
                reasoning=f"Trade telemetry indicates low win rate during thin or late US sessions with erratic slippage.",
                test_plan="Simulate restricting entry signals strictly between 12:00 UTC and 16:00 UTC with slippage and spread friction.",
                success_metric="Reduction in average adverse excursion (MAE) by >= 20% and positive net PnL.",
                failure_condition="Trade count falls below 20 trades or win rate does not exceed 45%.",
            ))

        persisted = []
        for h_req in hypotheses_to_create:
            hypo = await self.create_hypothesis(h_req)
            persisted.append(hypo)

        return persisted

    async def get_all_hypotheses(self) -> List[Hypothesis]:
        """Retrieve all hypotheses from Supabase."""
        if not self.db:
            return []
        stmt = select(Hypothesis).order_by(Hypothesis.created_at.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_experiment(self, req: ExperimentCreate) -> Experiment:
        """Register an experiment tied to a hypothesis and strategy version."""
        import json
        exp_id = f"EXP-{uuid.uuid4().hex[:6].upper()}"
        record = Experiment(
            experiment_id=exp_id,
            hypothesis_id=req.hypothesis_id,
            baseline_strategy="strategy_v1",
            candidate_strategy="strategy_v1.1",
            strategy_id=req.strategy_id,
            strategy_version=req.strategy_version,
            dataset=req.dataset_period,
            dataset_period=req.dataset_period,
            parameters_json=json.dumps(req.parameters),
            status="PROPOSED",
            action="PENDING_HUMAN_REVIEW",
            human_approved=False,
        )
        if self.db:
            self.db.add(record)
            await self.db.commit()
            await self.db.refresh(record)
        return record

    async def get_all_experiments(self) -> List[Experiment]:
        """Retrieve all registered experiments from Supabase."""
        if not self.db:
            return []
        stmt = select(Experiment).order_by(Experiment.created_at.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())


research_agent = ResearchAgent()
