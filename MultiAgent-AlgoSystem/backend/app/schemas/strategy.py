"""Pydantic schemas for strategies and strategy versions."""
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class StrategyCreate(BaseModel):
    strategy_id: str
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = {}
    code_version: str = "1.0.0"
    author: str = "system"


class StrategyVersionCreate(BaseModel):
    strategy_id: str
    version: str
    code_version: str
    parameters: Dict[str, Any]
    author: str = "system"
    changelog: Optional[str] = None


class StrategyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    strategy_id: str
    name: str
    description: Optional[str] = None
    current_version: str
    status: str
    created_at: datetime
    updated_at: datetime


class StrategyVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    strategy_id: str
    version: str
    code_version: str
    parameters_json: str
    author: str
    status: str
    changelog: Optional[str] = None
    created_at: datetime
