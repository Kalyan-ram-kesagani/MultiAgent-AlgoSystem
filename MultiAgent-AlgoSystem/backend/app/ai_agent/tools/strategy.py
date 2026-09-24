"""Strategy Management & Immutable Versioning Tools for AI Agent."""
import asyncio
import json
from typing import Any, Dict, List, Optional
from sqlalchemy import select

from backend.app.agents.strategy.strategy_agent import StrategyAgent
from backend.app.database.session import async_session_maker
from backend.app.models.strategy import Strategy, StrategyVersion

strategy_agent = StrategyAgent()


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


def get_strategy(strategy_id: str) -> str:
    """Fetch complete metadata, supported markets, timeframe, and active parameters for a strategy."""
    strat = strategy_agent.get_strategy(strategy_id)
    if not strat:
        return json.dumps({"error": f"Strategy '{strategy_id}' not found."}, indent=2)

    meta = strat.get_metadata()
    return json.dumps({
        "strategy_id": meta.strategy_id,
        "name": meta.name,
        "version": meta.version,
        "description": meta.description,
        "timeframe": meta.timeframe,
        "supported_symbols": meta.supported_symbols,
        "parameters": strat.get_default_parameters(),
    }, indent=2)


def list_strategies() -> str:
    """List all registered strategies in the system catalog."""
    strats = strategy_agent.list_strategies()
    return json.dumps({"count": len(strats), "strategies": strats}, indent=2)


def create_strategy_candidate(
    strategy_id: str = "strategy_v1",
    version: str = "v1.1.0",
    parameters: Any = None,
    rules: Optional[str] = None,
    created_from: Optional[str] = "v1.0.0",
    experiment_id: Optional[str] = None,
    changelog: Optional[str] = None,
    base_strategy_id: Optional[str] = None,
    new_version: Optional[str] = None,
    parameters_json: Optional[str] = None,
    hypothesis_id: Optional[str] = None,
) -> str:
    """
    Register an immutable new version candidate for a strategy in the database.
    Does NOT deploy automatically to live trading; created in CANDIDATE status awaiting validation.
    """
    target_strat_id = (base_strategy_id or strategy_id).strip()
    target_ver = (new_version or version).strip()
    log_text = changelog or "Candidate parameter optimization"

    # Normalize parameters
    if parameters is not None:
        params_dict = parameters if isinstance(parameters, dict) else json.loads(parameters)
    elif parameters_json is not None:
        params_dict = json.loads(parameters_json)
    else:
        params_dict = {}

    async def _async_create():
        async with async_session_maker() as session:
            # Check existing version for immutability
            stmt = select(StrategyVersion).where(
                StrategyVersion.strategy_id == target_strat_id,
                StrategyVersion.version == target_ver,
            )
            res = await session.execute(stmt)
            if res.scalar_one_or_none():
                return {"error": f"Version '{target_ver}' already exists for {target_strat_id}. Strategy versions are immutable."}

            new_sv = StrategyVersion(
                strategy_id=target_strat_id,
                version=target_ver,
                code_version="python_v1",
                rules=rules,
                parameters_json=json.dumps(params_dict),
                created_from=created_from,
                experiment_id=experiment_id,
                author="TradingResearchAgent",
                status="CANDIDATE",
                changelog=log_text,
            )
            session.add(new_sv)
            await session.commit()
            return {
                "strategy_id": target_strat_id,
                "version": target_ver,
                "status": "CANDIDATE",
                "rules": rules,
                "created_from": created_from,
                "experiment_id": experiment_id,
                "parameters": params_dict,
                "changelog": log_text,
                "message": "Strategy candidate created as an immutable version. Requires human approval before DEMO or live activation.",
            }

    data = _run_async(_async_create())
    return json.dumps(data, indent=2)



def validate_strategy(strategy_id: str, version: str) -> str:
    """
    Verify parameter boundaries and indicator logic consistency for a strategy version candidate.
    """
    async def _async_val():
        async with async_session_maker() as session:
            stmt = select(StrategyVersion).where(
                StrategyVersion.strategy_id == strategy_id,
                StrategyVersion.version == version,
            )
            res = await session.execute(stmt)
            sv = res.scalar_one_or_none()
            if not sv:
                return {"error": f"Strategy version {strategy_id} {version} not found."}

            params = json.loads(sv.parameters_json)
            issues = []
            if params.get("ema_fast", 20) >= params.get("ema_slow", 50):
                issues.append("ema_fast must be strictly less than ema_slow.")
            if params.get("reward_risk_ratio", 2.0) < 1.0:
                issues.append("reward_risk_ratio must be at least 1.0.")
            if params.get("atr_stop_multiplier", 1.5) <= 0.5:
                issues.append("atr_stop_multiplier is too tight (must be > 0.5).")

            is_valid = len(issues) == 0
            return {
                "strategy_id": strategy_id,
                "version": version,
                "is_valid": is_valid,
                "issues": issues,
                "status": "VALIDATED" if is_valid else "INVALID",
            }

    data = _run_async(_async_val())
    return json.dumps(data, indent=2)


def get_strategy_versions(strategy_id: str) -> str:
    """List all immutable historical versions and parameter snapshots for a strategy."""
    async def _async_list():
        async with async_session_maker() as session:
            stmt = select(StrategyVersion).where(
                StrategyVersion.strategy_id == strategy_id
            ).order_by(StrategyVersion.created_at.desc())
            res = await session.execute(stmt)
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

    data = _run_async(_async_list())
    return json.dumps({"strategy_id": strategy_id, "versions": data}, indent=2)
