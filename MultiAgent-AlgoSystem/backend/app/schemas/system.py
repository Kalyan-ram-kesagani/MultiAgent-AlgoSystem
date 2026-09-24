"""Pydantic schemas for system telemetry and observability."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


class SystemStatusResponse(BaseModel):
    environment: str
    status: str
    api_online: bool
    database_connected: bool
    mt5_connected: bool
    is_simulation: bool = False
    gateway_mode: str = "SIMULATION"
    kill_switch_active: bool
    active_strategies_count: int
    open_positions_count: int
    daily_pnl: float
    total_equity: float
    timestamp: datetime


class SystemEventCreate(BaseModel):
    level: str  # INFO, WARNING, CRITICAL
    component: str
    event_type: str
    message: str
    details: Optional[Dict[str, Any]] = None


class SystemEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    level: str
    component: str
    event_type: str
    message: str
    details_json: Optional[str] = None
