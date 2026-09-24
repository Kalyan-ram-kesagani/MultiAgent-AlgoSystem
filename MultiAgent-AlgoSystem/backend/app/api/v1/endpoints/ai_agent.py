"""Unified AI Agent, Research, Controlled Order Request, and Risk Endpoints."""
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai_agent.runtime import agent_runtime
from backend.app.ai_agent.tools.risk import request_order
from backend.app.agents.risk.risk_engine import risk_engine
from backend.app.agents.strategy.strategy_agent import StrategyAgent
from backend.app.database.session import get_db
from backend.app.models.ai_audit import AIAgentRun, AIToolCall, KillSwitchStateModel, OrderRequestModel
from backend.app.models.research import Experiment, Hypothesis
from backend.app.models.strategy import Strategy, StrategyVersion
from backend.app.models.trading import Trade

router = APIRouter(tags=["AI Trading & Research Agent"])
strategy_agent = StrategyAgent()


# Request / Response Schemas
class AIRunRequest(BaseModel):
    prompt: str = Field(..., description="Prompt or query for the AI Agent")
    task_name: str = Field(default="Ad-hoc Analysis", description="Name of the task")


class AIAnalyzeRequest(BaseModel):
    strategy_id: str = Field(default="strategy_v1")
    symbol: str = Field(default="EURUSD")


class AIResearchRequest(BaseModel):
    topic: str = Field(default="Market Regimes and Spread Degradation")
    strategy_id: str = Field(default="strategy_v1")


class AIBacktestRequest(BaseModel):
    strategy_id: str = Field(default="strategy_v1")
    symbol: str = Field(default="EURUSD")
    timeframe: str = Field(default="H1")
    days: int = Field(default=90, ge=10, le=365)
    parameters: Optional[Dict[str, Any]] = None


class OrderRequestPayload(BaseModel):
    symbol: str
    side: str
    quantity: float
    stop_loss: float
    take_profit: float
    strategy_id: str = "strategy_v1"
    reason: str
    execute: Optional[bool] = True


class KillSwitchPayload(BaseModel):
    activate: bool
    reason: str = "Operator manual intervention"
    requested_by: str = "Dashboard Operator"


# Endpoints
@router.post("/ai/run")
async def run_ai_agent(req: AIRunRequest):
    """Execute arbitrary prompt or quantitative investigation through the AI Agent."""
    res = await agent_runtime.run(task_name=req.task_name, user_prompt=req.prompt)
    return res


@router.post("/ai/analyze")
async def run_ai_analysis(req: AIAnalyzeRequest):
    """Trigger AI statistical performance and regime attribution analysis."""
    prompt = (
        f"Perform complete statistical performance and regime attribution analysis for '{req.strategy_id}' on {req.symbol}. "
        "Separate systematic trades from manual/external trades. Evaluate expectancy, profit factor, drawdown, and determine if sample size is sufficient."
    )
    res = await agent_runtime.run(task_name=f"Performance Analysis ({req.strategy_id})", user_prompt=prompt)
    return res


@router.post("/ai/research")
async def run_ai_research(req: AIResearchRequest):
    """Trigger AI hypothesis generation and quantitative backtesting workflow."""
    prompt = (
        f"Formulate a falsifiable quantitative research hypothesis regarding '{req.topic}' for strategy '{req.strategy_id}'. "
        "Run an event-driven backtest, perform walk-forward validation across rolling temporal windows, and run 95th percentile Monte Carlo permutations. "
        "Report expectancy, profit factor, stability ratio, and conclude whether the candidate is rejected or recommended for human review."
    )
    res = await agent_runtime.run(task_name=f"Autonomous Research: {req.topic[:30]}", user_prompt=prompt)
    return res


@router.post("/ai/backtest")
async def run_ai_backtest(req: AIBacktestRequest):
    """Trigger AI backtest with Monte Carlo analysis."""
    param_str = json.dumps(req.parameters) if req.parameters else "{}"
    prompt = (
        f"Run a detailed historical backtest for '{req.strategy_id}' on {req.symbol} ({req.timeframe}) over {req.days} days. "
        f"Parameters: {param_str}. Evaluate expectancy, drawdown, and Monte Carlo 95th percentile worst-case risk."
    )
    res = await agent_runtime.run(task_name=f"Backtest ({req.strategy_id} {req.symbol})", user_prompt=prompt)
    return res


@router.get("/ai/status")
def get_ai_status():
    """Retrieve actual live runtime state and telemetry for AI Trading & Research Agent."""
    return agent_runtime.get_status()


@router.get("/ai/runs")
async def get_ai_runs(limit: int = Query(default=20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    """Retrieve persistent audit log of recent AI Agent executions."""
    stmt = select(AIAgentRun).order_by(AIAgentRun.start_time.desc()).limit(limit)
    res = await db.execute(stmt)
    runs = list(res.scalars().all())
    if not runs:
        return agent_runtime.recent_runs[:limit]
    return [
        {
            "run_id": r.run_id,
            "task": r.task,
            "status": r.status,
            "model": r.model,
            "latency_ms": r.latency_ms,
            "start_time": r.start_time.isoformat() if r.start_time else None,
            "response": r.final_response,
            "error": r.error,
        }
        for r in runs
    ]


@router.get("/ai/tool-calls")
async def get_ai_tool_calls(
    run_id: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve audit records of tools executed by the AI Agent."""
    stmt = select(AIToolCall).order_by(AIToolCall.timestamp.desc()).limit(limit)
    if run_id:
        stmt = stmt.where(AIToolCall.run_id == run_id)
    res = await db.execute(stmt)
    records = list(res.scalars().all())
    if not records:
        return agent_runtime.recent_tool_calls[:limit]
    return [
        {
            "tool_call_id": tc.tool_call_id,
            "run_id": tc.run_id,
            "tool_name": tc.tool_name,
            "latency_ms": tc.latency_ms,
            "success": tc.success,
            "output_preview": tc.output_result_json[:200] if tc.output_result_json else "",
            "timestamp": tc.timestamp.isoformat() if tc.timestamp else None,
        }
        for tc in records
    ]


@router.get("/research/experiments")
async def get_research_experiments(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Retrieve recorded research experiments."""
    stmt = select(Experiment).order_by(Experiment.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/research/hypotheses")
async def get_research_hypotheses(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Retrieve recorded research hypotheses."""
    stmt = select(Hypothesis).order_by(Hypothesis.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/strategies")
def get_strategies():
    """List registered strategies with metadata and default parameters."""
    return strategy_agent.list_strategies()


@router.get("/strategies/{strategy_id}/versions")
async def get_strategy_versions(strategy_id: str, db: AsyncSession = Depends(get_db)):
    """List immutable versions for a strategy."""
    stmt = select(StrategyVersion).where(StrategyVersion.strategy_id == strategy_id).order_by(StrategyVersion.created_at.desc())
    res = await db.execute(stmt)
    versions = list(res.scalars().all())
    return [
        {
            "version": v.version,
            "status": v.status,
            "author": v.author,
            "changelog": v.changelog,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "parameters": json.loads(v.parameters_json),
        }
        for v in versions
    ]


@router.post("/orders/request")
def submit_order_request(payload: OrderRequestPayload):
    """
    Controlled Order Request Submission.
    AI or operator submits proposal -> Strictly evaluated by Deterministic Risk Engine.
    If approved and execute=True, routes strictly to MT5 DEMO.
    """
    raw_res = request_order(
        symbol=payload.symbol,
        side=payload.side,
        quantity=payload.quantity,
        stop_loss=payload.stop_loss,
        take_profit=payload.take_profit,
        strategy_id=payload.strategy_id,
        reason=payload.reason,
        execute=payload.execute if payload.execute is not None else True,
    )
    return json.loads(raw_res)


@router.get("/orders/{order_request_id}")
async def get_order_request(order_request_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve an order request status and risk journal audit record by ID."""
    stmt = select(OrderRequestModel).where(OrderRequestModel.request_id == order_request_id)
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail=f"Order request '{order_request_id}' not found.")

    return {
        "order_request_id": record.request_id,
        "execution_id": getattr(record, "execution_id", None),
        "symbol": record.symbol,
        "side": record.side,
        "quantity": record.quantity,
        "approved_lots": record.approved_lots,
        "stop_loss": record.stop_loss,
        "take_profit": record.take_profit,
        "strategy_id": record.strategy_id,
        "is_approved": record.is_approved,
        "execution_status": record.execution_status,
        "rejection_reasons": json.loads(record.rejection_reasons_json) if record.rejection_reasons_json else [],
        "risk_evaluation": json.loads(record.risk_evaluation_json) if record.risk_evaluation_json else {},
        "reason": record.reason,
        "broker_ticket": record.broker_ticket,
        "broker_deal_id": getattr(record, "broker_deal_id", None),
        "execution_error": record.execution_error,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


@router.get("/risk/limits")
def get_risk_limits():
    """Retrieve hard immutable deterministic risk limits."""
    from backend.app.core.config import settings
    return {
        "max_risk_per_trade_pct": settings.RISK_PER_TRADE_PCT * 100,
        "max_portfolio_drawdown_pct": settings.MAX_ACCOUNT_DRAWDOWN_PCT * 100,
        "max_daily_loss_pct": settings.MAX_DAILY_LOSS_PCT * 100,
        "max_open_positions": settings.MAX_OPEN_POSITIONS,
        "max_symbol_exposure": settings.MAX_SYMBOL_EXPOSURE,
        "max_allowed_spread_pips": settings.MAX_ALLOWED_SPREAD_PIPS,
        "stop_loss_required": True,
        "trading_mode": settings.TRADING_MODE,
        "ai_modification_permitted": False,
    }


@router.get("/risk/status")
def get_risk_status():
    """Retrieve Risk Engine parameters and limits."""
    from backend.app.ai_agent.tools.risk import get_risk_state
    return json.loads(get_risk_state())


@router.get("/kill-switch")
def get_kill_switch_state():
    """Retrieve current Kill Switch state."""
    return {
        "kill_switch_active": risk_engine.kill_switch_active,
        "reason": risk_engine.kill_switch_reason,
        "operator": risk_engine.kill_switch_operator,
    }


@router.post("/kill-switch")
def set_kill_switch_state(payload: KillSwitchPayload):
    """Emergency toggle for the system kill switch."""
    if payload.activate:
        risk_engine.engage_kill_switch(payload.reason, operator=payload.requested_by)
    else:
        risk_engine.disengage_kill_switch(operator=payload.requested_by)
    return {
        "kill_switch_active": risk_engine.kill_switch_active,
        "reason": risk_engine.kill_switch_reason,
        "operator": risk_engine.kill_switch_operator,
    }
