"""Autonomous Research, Strategy Optimization & Experiment Pipeline API endpoints."""
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agents.orchestrator.orchestrator_agent import OrchestratorAgent
from backend.app.agents.performance.performance_agent import performance_agent
from backend.app.database.session import get_db
from backend.app.models.research import Experiment, Hypothesis
from backend.app.models.strategy import StrategyVersion
from backend.app.models.trading import Trade
from backend.app.core.config import settings
from backend.app.services.performance_monitor import performance_monitor

router = APIRouter(tags=["Autonomous Research & Strategy Improvement"])


class InvestigationRequest(BaseModel):
    symbol: str = "EURUSD"
    strategy_id: str = "strategy_v1"
    issue: Optional[str] = None
    force_run: bool = False


class ExperimentReviewRequest(BaseModel):
    decision: str  # APPROVED_FOR_DEMO, REJECTED
    operator_comment: Optional[str] = None


@router.get("/performance/degradation")
async def get_performance_degradation_telemetry(db: AsyncSession = Depends(get_db)):
    """
    Evaluate actual recorded trades from Supabase and detect degradation patterns.
    Provides sample-size awareness (INSUFFICIENT SAMPLE, EARLY ANALYSIS, RESEARCHABLE).
    """
    stmt = select(Trade).order_by(Trade.exit_time.desc()).limit(500)
    res = await db.execute(stmt)
    trades = list(res.scalars().all())

    metrics = performance_agent.analyze_performance(trades)
    alerts = performance_monitor.detect_degradations(metrics)

    return {
        "sample_status": metrics.get("sample_status"),
        "trade_count": metrics.get("trade_count", len(trades)),
        "metrics": {
            "win_rate": metrics.get("win_rate"),
            "profit_factor": metrics.get("profit_factor"),
            "expectancy": metrics.get("expectancy"),
            "total_net_pnl": metrics.get("total_net_pnl"),
            "max_drawdown": metrics.get("max_drawdown"),
            "consecutive_losses": metrics.get("consecutive_losses"),
            "gross_profit": metrics.get("gross_profit"),
            "gross_loss": metrics.get("gross_loss"),
            "avg_win": metrics.get("avg_win"),
            "avg_loss": metrics.get("avg_loss"),
        },
        "degradation_alerts": alerts,
        "investigation_recommended": len(alerts) > 0,
    }


@router.post("/orchestrator/investigate")
async def trigger_autonomous_investigation(
    req: InvestigationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger the multi-agent strategy improvement pipeline:
    Performance Monitor -> Research Agent (Hypothesis) -> AI/ML Agent -> Backtest Agent -> Supabase Registry.
    """
    # 1. Fetch current trades to provide empirical context
    stmt = select(Trade).order_by(Trade.exit_time.desc()).limit(500)
    res = await db.execute(stmt)
    trades = list(res.scalars().all())
    metrics = performance_agent.analyze_performance(trades)
    alerts = performance_monitor.detect_degradations(metrics)

    top_issue = alerts[0] if alerts else {
        "strategy_id": req.strategy_id,
        "symbol": req.symbol,
        "issue": req.issue or "exploratory_optimization",
        "sample_size": len(trades),
        "severity": "LOW_SAMPLE" if len(trades) < 30 else "MODERATE",
        "recommended_action": "formulate_exploratory_hypothesis",
    }

    # 2. Orchestrate multi-agent investigation
    orchestrator = OrchestratorAgent(db_session=db)
    result = await orchestrator.execute_task("investigate_performance", top_issue)
    return result


@router.get("/research/hypotheses")
async def list_hypotheses(db: AsyncSession = Depends(get_db)):
    """Retrieve all falsifiable research hypotheses stored in Supabase."""
    stmt = select(Hypothesis).order_by(Hypothesis.created_at.desc()).limit(50)
    res = await db.execute(stmt)
    hypotheses = list(res.scalars().all())
    return hypotheses


@router.get("/research/experiments")
async def list_experiments(db: AsyncSession = Depends(get_db)):
    """Retrieve all strategy improvement experiments and comparative metrics from Supabase."""
    stmt = select(Experiment).order_by(Experiment.created_at.desc()).limit(50)
    res = await db.execute(stmt)
    experiments = list(res.scalars().all())

    # Parse JSON fields for frontend display
    parsed = []
    for exp in experiments:
        data = {
            "id": exp.id,
            "experiment_id": exp.experiment_id,
            "hypothesis_id": exp.hypothesis_id,
            "baseline_strategy": exp.baseline_strategy,
            "candidate_strategy": exp.candidate_strategy,
            "strategy_id": exp.strategy_id,
            "strategy_version": exp.strategy_version,
            "dataset": exp.dataset,
            "dataset_period": exp.dataset_period,
            "training_period": exp.training_period,
            "validation_period": exp.validation_period,
            "out_of_sample_period": exp.out_of_sample_period,
            "status": exp.status,
            "action": exp.action,
            "human_approved": exp.human_approved,
            "created_at": exp.created_at.isoformat() if exp.created_at else None,
            "conclusion": exp.conclusion,
            "parameters": json.loads(exp.parameters_json) if exp.parameters_json else {},
            "metrics": json.loads(exp.metrics_json) if exp.metrics_json else [],
            "robustness": json.loads(exp.robustness_metrics_json) if exp.robustness_metrics_json else {},
        }
        parsed.append(data)
    return parsed


@router.post("/research/experiments/{experiment_id}/review")
async def review_experiment(
    experiment_id: str,
    req: ExperimentReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """Human Operator Gate: Review and approve candidate strategy for Demo testing or reject."""
    stmt = select(Experiment).where(Experiment.experiment_id == experiment_id)
    res = await db.execute(stmt)
    exp = res.scalar_one_or_none()
    if not exp:
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_id}' not found.")

    decision = req.decision.upper()
    if "LIVE" in decision:
        raise HTTPException(status_code=403, detail="LIVE trading deployment is strictly disabled. MT5 DEMO ONLY.")

    valid_decisions = ("APPROVED_FOR_DEMO", "DEMO_VALIDATION", "ACTIVE", "REJECTED")
    if decision not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"Decision '{decision}' invalid. Must be one of: {valid_decisions}",
        )

    # State mapping: CANDIDATE -> HUMAN REVIEW -> DEMO_VALIDATION -> HUMAN APPROVAL -> ACTIVE
    if decision in ("APPROVED_FOR_DEMO", "DEMO_VALIDATION"):
        target_status = "DEMO_VALIDATION"
        is_approved = True
    elif decision == "ACTIVE":
        target_status = "ACTIVE"
        is_approved = True
    else:
        target_status = "REJECTED"
        is_approved = False

    exp.status = target_status
    exp.action = f"Human decision: {target_status}. Comment: {req.operator_comment or 'N/A'}"
    exp.human_approved = is_approved

    # Update candidate strategy version record
    v_stmt = select(StrategyVersion).where(
        StrategyVersion.strategy_id == exp.strategy_id,
        StrategyVersion.version == exp.strategy_version,
    )
    v_res = await db.execute(v_stmt)
    v_record = v_res.scalar_one_or_none()
    if v_record:
        v_record.status = target_status

    await db.commit()
    return {
        "status": "DECISION_RECORDED",
        "experiment_id": experiment_id,
        "decision": decision,
        "promotion_status": target_status,
        "human_approved": exp.human_approved,
        "trading_mode": settings.TRADING_MODE,
    }


@router.get("/strategies/versions")
async def list_strategy_versions(
    strategy_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve immutable strategy version history from Supabase."""
    stmt = select(StrategyVersion).order_by(StrategyVersion.created_at.desc())
    if strategy_id:
        stmt = stmt.where(StrategyVersion.strategy_id == strategy_id)
    res = await db.execute(stmt)
    versions = list(res.scalars().all())
    return [
        {
            "strategy_id": v.strategy_id,
            "version": v.version,
            "code_version": v.code_version,
            "author": v.author,
            "status": v.status,
            "changelog": v.changelog,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "parameters": json.loads(v.parameters_json) if v.parameters_json else {},
        }
        for v in versions
    ]
