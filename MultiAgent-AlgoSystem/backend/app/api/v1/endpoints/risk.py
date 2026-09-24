"""Risk Engine and Kill Switch API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from backend.app.agents.risk.risk_engine import risk_engine
from backend.app.core.config import settings
from backend.app.schemas.risk import (
    CircuitBreakerStatusResponse,
    KillSwitchRequest,
    RiskEvaluationRequest,
    RiskEvaluationResult,
)

router = APIRouter(prefix="/risk", tags=["Risk & Safety"])


@router.post("/evaluate", response_model=RiskEvaluationResult)
def evaluate_order(req: RiskEvaluationRequest):
    """Evaluate an order proposal through the non-bypassable Risk Engine."""
    return risk_engine.evaluate_order(req)


@router.get("/circuit-breaker", response_model=CircuitBreakerStatusResponse)
def get_circuit_breaker_status():
    """Retrieve current circuit breaker and kill switch status."""
    return CircuitBreakerStatusResponse(
        kill_switch_active=risk_engine.kill_switch_active,
        trading_paused=risk_engine.kill_switch_active,
        pause_reason=risk_engine.kill_switch_reason,
        consecutive_losses=risk_engine.consecutive_losses,
        current_day_loss=0.0,
        current_week_loss=0.0,
        peak_equity=risk_engine.peak_equity,
        current_drawdown_pct=0.0,
        max_drawdown_threshold_pct=settings.MAX_ACCOUNT_DRAWDOWN_PCT * 100,
        max_daily_loss_threshold_pct=settings.MAX_DAILY_LOSS_PCT * 100,
    )


@router.post("/kill-switch")
def toggle_kill_switch(req: KillSwitchRequest):
    """Engage or disengage emergency kill switch manually."""
    if req.activate:
        risk_engine.engage_kill_switch(reason=req.reason, operator=req.requested_by)
    else:
        risk_engine.disengage_kill_switch(operator=req.requested_by)

    return {
        "kill_switch_active": risk_engine.kill_switch_active,
        "reason": risk_engine.kill_switch_reason,
    }


@router.get("/limits")
def get_risk_limits():
    """Retrieve hard immutable deterministic risk limits."""
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


@router.get("/status")
def get_risk_status():
    """Retrieve full risk state and circuit breaker telemetry."""
    import json
    from backend.app.ai_agent.tools.risk import get_risk_state
    return json.loads(get_risk_state())

