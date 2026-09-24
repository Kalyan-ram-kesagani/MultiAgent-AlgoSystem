"""Pydantic schemas for research hypotheses and experiments."""
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class HypothesisCreate(BaseModel):
    title: str
    hypothesis_statement: str
    reasoning: str
    test_plan: str
    success_metric: str
    failure_condition: str


class HypothesisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hypothesis_id: str
    title: str
    hypothesis_statement: str
    reasoning: str
    test_plan: str
    success_metric: str
    failure_condition: str
    status: str
    created_at: datetime


class ExperimentCreate(BaseModel):
    hypothesis_id: Optional[str] = None
    strategy_id: str
    strategy_version: str
    dataset_period: str
    parameters: Dict[str, Any]


class ExperimentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    experiment_id: str
    hypothesis_id: Optional[str] = None
    strategy_id: str
    strategy_version: str
    dataset_period: str
    parameters_json: str
    results_summary_json: Optional[str] = None
    conclusion: Optional[str] = None
    action: str
    human_approved: bool
    created_at: datetime
