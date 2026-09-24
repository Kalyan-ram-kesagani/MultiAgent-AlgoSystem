"""Base strategy abstract class enforcing explicit parameters, versioning, and deterministic signal emission."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd
from pydantic import BaseModel
from backend.app.schemas.trading import SignalCreate


class StrategyMetadata(BaseModel):
    strategy_id: str
    version: str
    name: str
    description: str
    author: str
    timeframe: str
    supported_symbols: List[str]


class BaseStrategy(ABC):
    """Abstract Base Class for all trading strategies."""

    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        self.params = self.get_default_parameters()
        if parameters:
            self.params.update(parameters)
        self.metadata = self.get_metadata()

    @abstractmethod
    def get_metadata(self) -> StrategyMetadata:
        """Return strategy metadata including ID, version, and supported symbols."""
        pass

    @abstractmethod
    def get_default_parameters(self) -> Dict[str, Any]:
        """Return default dictionary of strategy parameters."""
        pass

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> List[SignalCreate]:
        """
        Evaluate market data bars and generate deterministic trading signals.
        MUST NOT rely on non-deterministic randomness or ambiguous concepts.
        """
        pass
