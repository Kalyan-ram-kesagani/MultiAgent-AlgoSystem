"""Strategy and Strategy Versioning API endpoints."""
from typing import Any, Dict, List
from fastapi import APIRouter
from backend.app.agents.strategy.strategy_agent import StrategyAgent

router = APIRouter(prefix="/strategies", tags=["Strategies"])
strategy_agent = StrategyAgent()


@router.get("/")
def list_strategies() -> List[Dict[str, Any]]:
    """List all registered deterministic strategies and metadata."""
    return strategy_agent.list_strategies()


@router.get("/{strategy_id}")
def get_strategy_details(strategy_id: str):
    strategy = strategy_agent.get_strategy(strategy_id)
    if not strategy:
        return {"error": f"Strategy '{strategy_id}' not found"}
    meta = strategy.get_metadata()
    return {
        "metadata": meta.model_dump(),
        "parameters": strategy.params,
    }
