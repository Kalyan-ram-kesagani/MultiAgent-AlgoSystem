"""Agent Runtime Types, Enums, Metadata, and Task Models."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    ORCHESTRATOR = "ORCHESTRATOR"
    RESEARCH = "RESEARCH"
    DATA = "DATA"
    STRATEGY = "STRATEGY"
    AI_ML = "AI_ML"
    BACKTEST = "BACKTEST"
    RISK = "RISK"
    EXECUTION = "EXECUTION"
    MONITORING = "MONITORING"
    JOURNAL = "JOURNAL"
    PERFORMANCE = "PERFORMANCE"


class AgentType(str, Enum):
    AI_REASONING = "AI_REASONING"          # Orchestrator, Research, AI/ML, Performance
    DETERMINISTIC_SOFTWARE = "DETERMINISTIC_SOFTWARE"  # Data, Strategy, Backtest, Risk, Execution, Monitoring, Journal


class AgentLifecycleState(str, Enum):
    OFFLINE = "OFFLINE"
    STARTING = "STARTING"
    IDLE = "IDLE"
    WORKING = "WORKING"
    WAITING = "WAITING"
    ERROR = "ERROR"
    STOPPED = "STOPPED"


class TaskStatus(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    ASSIGNED = "ASSIGNED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AgentPermission(str, Enum):
    # Strictly scoped permissions (Principle of Least Privilege)
    READ_MARKET_DATA = "READ_MARKET_DATA"
    WRITE_RESEARCH = "WRITE_RESEARCH"
    READ_MT5 = "READ_MT5"
    WRITE_DATABASE = "WRITE_DATABASE"
    EVALUATE_SIGNALS = "EVALUATE_SIGNALS"
    TRAIN_MODELS = "TRAIN_MODELS"
    EXECUTE_BACKTEST = "EXECUTE_BACKTEST"
    APPROVE_RISK = "APPROVE_RISK"
    EXECUTE_ORDERS = "EXECUTE_ORDERS"
    MONITOR_HEALTH = "MONITOR_HEALTH"
    WRITE_JOURNAL = "WRITE_JOURNAL"
    COMPUTE_METRICS = "COMPUTE_METRICS"
    COORDINATE_SYSTEM = "COORDINATE_SYSTEM"


class AgentTask(BaseModel):
    """Lifecycle representation of an agent task."""
    task_id: str
    agent_id: str
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.CREATED
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    output_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    duration_ms: Optional[float] = None


class AgentMetadata(BaseModel):
    """Immutable configuration and identity of an agent."""
    agent_id: str
    name: str
    description: str
    role: AgentRole
    agent_type: AgentType
    version: str = "1.0.0"
    capabilities: List[str] = Field(default_factory=list)
    permissions: List[AgentPermission] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    model: Optional[str] = None  # Populated for AI reasoning agents


class AgentState(BaseModel):
    """Mutable runtime telemetry of an agent."""
    agent_id: str
    name: str
    status: AgentLifecycleState = AgentLifecycleState.IDLE
    heartbeat_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_task: Optional[str] = None
    current_task_id: Optional[str] = None
    last_task: Optional[str] = None
    last_result: Optional[str] = None
    last_action_timestamp: Optional[datetime] = None
    tasks_completed_today: int = 0
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
