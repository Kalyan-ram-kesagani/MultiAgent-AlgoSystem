"""Research & Hypothesis Tools for AI Agent."""
import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select

from backend.app.database.session import async_session_maker
from backend.app.models.research import Experiment, ExperimentResult, Hypothesis


def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return loop.run_until_complete(coro)


def create_hypothesis(
    strategy_id: str = "strategy_v1",
    title: str = "",
    hypothesis: str = "",
    reason: str = "",
    evidence: Any = None,
    hypothesis_statement: str = "",
    reasoning: str = "",
    test_plan: str = "",
    success_metric: str = "",
    failure_condition: str = "",
) -> str:
    """
    Formulate and persist an empirical research hypothesis in the database.
    Distinguishes OBSERVATION, HYPOTHESIS, TEST RESULT, and CONCLUSION.
    Does NOT present unverified hypotheses as established facts.
    """
    stmt_text = hypothesis or hypothesis_statement or title
    reason_text = reason or reasoning or "Empirical trade observation"
    ev_list = evidence if isinstance(evidence, list) else ([evidence] if evidence else [])

    async def _async_create():
        hyp_id = f"HYP-{uuid.uuid4().hex[:8].upper()}"
        new_hyp = Hypothesis(
            hypothesis_id=hyp_id,
            strategy_id=strategy_id.strip() if strategy_id else "strategy_v1",
            title=title.strip() if title else stmt_text[:60],
            hypothesis_statement=stmt_text.strip(),
            reasoning=reason_text.strip(),
            evidence_json=json.dumps(ev_list),
            test_plan=test_plan.strip() if test_plan else "Walk-forward temporal validation and Monte Carlo resampling",
            success_metric=success_metric.strip() if success_metric else "Profit Factor >= 1.25, Expectancy > 0, Max DD <= 10%",
            failure_condition=failure_condition.strip() if failure_condition else "OOS Profit Factor < 1.0 or Max DD > 10%",
            status="PROPOSED",
        )
        async with async_session_maker() as session:
            session.add(new_hyp)
            await session.commit()
            return {
                "hypothesis_id": hyp_id,
                "strategy_id": new_hyp.strategy_id,
                "title": new_hyp.title,
                "hypothesis": new_hyp.hypothesis_statement,
                "reason": new_hyp.reasoning,
                "evidence": ev_list,
                "status": new_hyp.status,
                "classification": "HYPOTHESIS",
                "disclaimer": "This statement is a falsifiable hypothesis undergoing investigation, not an established fact.",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "success": True,
            }

    res = _run_async(_async_create())
    return json.dumps(res, indent=2)


def list_hypotheses(status: Optional[str] = None, strategy_id: Optional[str] = None) -> str:
    """List recorded research hypotheses with their current status and empirical evidence."""
    async def _async_list():
        async with async_session_maker() as session:
            stmt = select(Hypothesis).order_by(Hypothesis.created_at.desc())
            if strategy_id:
                stmt = stmt.where(Hypothesis.strategy_id == strategy_id)
            if status:
                stmt = stmt.where(Hypothesis.status == status.upper())
            res = await session.execute(stmt)
            hyps = list(res.scalars().all())
            return [
                {
                    "hypothesis_id": h.hypothesis_id,
                    "strategy_id": h.strategy_id,
                    "title": h.title,
                    "hypothesis": h.hypothesis_statement,
                    "reasoning": h.reasoning,
                    "evidence": json.loads(h.evidence_json) if h.evidence_json else [],
                    "status": h.status,
                    "created_at": h.created_at.isoformat() if h.created_at else None,
                }
                for h in hyps
            ]

    data = _run_async(_async_list())
    return json.dumps({"count": len(data), "hypotheses": data}, indent=2)


def get_hypothesis(hypothesis_id: str) -> str:
    """Retrieve full detail, rationale, test plan, and status for a specific hypothesis ID."""
    async def _async_get():
        async with async_session_maker() as session:
            stmt = select(Hypothesis).where(Hypothesis.hypothesis_id == hypothesis_id)
            res = await session.execute(stmt)
            hyp = res.scalar_one_or_none()
            if not hyp:
                return {"error": f"Hypothesis {hypothesis_id} not found"}
            return {
                "hypothesis_id": hyp.hypothesis_id,
                "strategy_id": hyp.strategy_id,
                "title": hyp.title,
                "hypothesis": hyp.hypothesis_statement,
                "reasoning": hyp.reasoning,
                "evidence": json.loads(hyp.evidence_json) if hyp.evidence_json else [],
                "test_plan": hyp.test_plan,
                "success_metric": hyp.success_metric,
                "failure_condition": hyp.failure_condition,
                "status": hyp.status,
                "created_at": hyp.created_at.isoformat() if hyp.created_at else None,
            }

    data = _run_async(_async_get())
    return json.dumps(data, indent=2)


def create_experiment(
    experiment_name: str,
    strategy_id: str = "strategy_v1",
    baseline_strategy_version: str = "v1.0.0",
    candidate_strategy_version: str = "v1.1.0",
    hypothesis_id: Optional[str] = None,
    dataset_description: str = "EURUSD_H1",
    training_period: Optional[str] = "Bars 0-350 (70% In-Sample)",
    testing_period: Optional[str] = "Bars 350-500 (30% Out-of-Sample)",
    sample_size: int = 0,
    parameters_json: str = "{}",
) -> str:
    """
    Create an immutable experiment registry record.
    Initializes experiment status to CREATED.
    """
    async def _async_create():
        exp_id = f"EXP-{uuid.uuid4().hex[:8].upper()}"
        new_exp = Experiment(
            experiment_id=exp_id,
            experiment_name=experiment_name.strip(),
            strategy_id=strategy_id.strip(),
            baseline_strategy_version=baseline_strategy_version.strip(),
            candidate_strategy_version=candidate_strategy_version.strip(),
            hypothesis_id=hypothesis_id.strip() if hypothesis_id else None,
            status="CREATED",
            dataset_description=dataset_description.strip(),
            training_period=training_period,
            testing_period=testing_period,
            sample_size=sample_size,
            created_by="TradingResearchAgent",
            parameters_json=parameters_json if parameters_json else "{}",
        )
        async with async_session_maker() as session:
            session.add(new_exp)
            await session.commit()
            return {
                "experiment_id": exp_id,
                "experiment_name": new_exp.experiment_name,
                "strategy_id": new_exp.strategy_id,
                "baseline_version": new_exp.baseline_strategy_version,
                "candidate_version": new_exp.candidate_strategy_version,
                "hypothesis_id": new_exp.hypothesis_id,
                "status": new_exp.status,
                "dataset": new_exp.dataset_description,
                "sample_size": new_exp.sample_size,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

    data = _run_async(_async_create())
    return json.dumps(data, indent=2)


def get_experiment(experiment_id: str) -> str:
    """Retrieve full experiment details and recorded results."""
    async def _async_get():
        async with async_session_maker() as session:
            stmt = select(Experiment).where(
                (Experiment.experiment_id == experiment_id) | (Experiment.experiment_name == experiment_id)
            )
            res = await session.execute(stmt)
            exp = res.scalar_one_or_none()
            if not exp:
                return {"error": f"Experiment {experiment_id} not found."}

            # Fetch any recorded results
            stmt_res = select(ExperimentResult).where(ExperimentResult.experiment_id == exp.experiment_id)
            res_results = await session.execute(stmt_res)
            results = list(res_results.scalars().all())

            results_data = []
            for r in results:
                results_data.append({
                    "strategy_version": r.strategy_version,
                    "sample_size": r.sample_size,
                    "win_rate": r.win_rate,
                    "profit_factor": r.profit_factor,
                    "expectancy": r.expectancy,
                    "net_profit": r.net_profit,
                    "max_drawdown": r.max_drawdown,
                    "sharpe": r.sharpe,
                    "sortino": r.sortino,
                    "trade_count": r.trade_count,
                    "average_trade": r.average_trade,
                    "largest_loss": r.largest_loss,
                    "largest_win": r.largest_win,
                    "walk_forward": json.loads(r.walk_forward_result_json) if r.walk_forward_result_json else None,
                    "monte_carlo": json.loads(r.monte_carlo_result_json) if r.monte_carlo_result_json else None,
                })

            return {
                "experiment_id": exp.experiment_id,
                "experiment_name": exp.experiment_name,
                "strategy_id": exp.strategy_id,
                "baseline_version": exp.baseline_strategy_version,
                "candidate_version": exp.candidate_strategy_version,
                "hypothesis_id": exp.hypothesis_id,
                "status": exp.status,
                "dataset_description": exp.dataset_description,
                "training_period": exp.training_period,
                "testing_period": exp.testing_period,
                "sample_size": exp.sample_size,
                "created_by": exp.created_by,
                "created_at": exp.created_at.isoformat() if exp.created_at else None,
                "completed_at": exp.completed_at.isoformat() if exp.completed_at else None,
                "results": results_data,
            }

    data = _run_async(_async_get())
    return json.dumps(data, indent=2)


def record_research_result(
    experiment_id: str,
    conclusion: str,
    is_validated: bool,
    status: Optional[str] = None,
) -> str:
    """
    Record conclusion on an experiment.
    Marks status as CANDIDATE (awaiting human review) or REJECTED.
    Does NOT deploy automatically to live trading.
    """
    final_status = status.upper() if status else ("CANDIDATE" if is_validated else "REJECTED")

    async def _async_record():
        async with async_session_maker() as session:
            stmt = select(Experiment).where(
                (Experiment.experiment_id == experiment_id) | (Experiment.experiment_name == experiment_id)
            )
            res = await session.execute(stmt)
            exp = res.scalar_one_or_none()
            if not exp:
                return {"error": f"Experiment {experiment_id} not found"}

            exp.conclusion = conclusion
            exp.status = final_status
            exp.completed_at = datetime.now(timezone.utc)
            await session.commit()
            return {
                "experiment_id": exp.experiment_id,
                "status": exp.status,
                "conclusion": exp.conclusion,
                "human_approval_required": True,
                "message": "Experiment completed. Candidate strategies remain inactive until explicit human approval.",
            }

    data = _run_async(_async_record())
    return json.dumps(data, indent=2)
