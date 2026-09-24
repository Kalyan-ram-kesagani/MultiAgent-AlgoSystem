"""Agent #4 — Strategy Agent: Strategy Registry, Version Management, and Signal Evaluation."""
from datetime import datetime
from typing import Dict, List, Optional, Type
import pandas as pd
from backend.app.core.constants import StrategyStatus
from backend.app.core.logging import logger
from backend.app.schemas.trading import SignalCreate
from strategies.shared.base_strategy import BaseStrategy
from strategies.strategy_v1.trend_pullback import StrategyV1


class StrategyAgent:
    """Manages strategy instances, version transitions, and deterministic signal evaluation."""

    def __init__(self):
        self._registry: Dict[str, Type[BaseStrategy]] = {}
        self._active_instances: Dict[str, BaseStrategy] = {}
        # Register core strategy implementations
        self.register_strategy_class("strategy_v1", StrategyV1)

    def register_strategy_class(self, strategy_id: str, strategy_cls: Type[BaseStrategy]) -> None:
        """Register a strategy class into the runtime catalog."""
        self._registry[strategy_id] = strategy_cls
        self._active_instances[strategy_id] = strategy_cls()
        logger.info(f"Registered strategy {strategy_id}", extra={"strategy_id": strategy_id})

    def get_strategy(self, strategy_id: str) -> Optional[BaseStrategy]:
        return self._active_instances.get(strategy_id)

    def list_strategies(self) -> List[Dict]:
        result = []
        for sid, instance in self._active_instances.items():
            meta = instance.get_metadata()
            result.append({
                "strategy_id": meta.strategy_id,
                "version": meta.version,
                "name": meta.name,
                "description": meta.description,
                "timeframe": meta.timeframe,
                "supported_symbols": meta.supported_symbols,
                "default_parameters": instance.get_default_parameters(),
            })
        return result

    def evaluate_signals(
        self,
        strategy_id: str,
        market_df: pd.DataFrame,
        override_params: Optional[Dict] = None,
    ) -> List[SignalCreate]:
        """Run deterministic signal evaluation on provided market data."""
        if strategy_id not in self._registry:
            raise ValueError(f"Strategy {strategy_id} is not registered.")

        strategy_cls = self._registry[strategy_id]
        strategy = strategy_cls(parameters=override_params)
        return strategy.generate_signals(market_df)
