"""Agent state, task, event, and performance snapshot database models."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, JSON, ForeignKey, Text, Float, BigInteger
from sqlalchemy.orm import relationship

from backend.app.database.base import Base


class AgentStateModel(Base):
    """Persisted state of agents in the multi-agent runtime."""
    __tablename__ = "agents"

    agent_id = Column(String(50), primary_key=True)
    status = Column(String(20), nullable=False, default="OFFLINE")
    version = Column(String(20), nullable=False, default="1.0.0")
    started_at = Column(DateTime, nullable=True)
    last_heartbeat = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    current_task = Column(String(100), nullable=True)
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)

    tasks = relationship("AgentTaskModel", back_populates="agent", cascade="all, delete-orphan")
    events = relationship("AgentEventModel", back_populates="agent", cascade="all, delete-orphan")


class AgentTaskModel(Base):
    """Persisted agent tasks."""
    __tablename__ = "agent_tasks"

    task_id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(50), ForeignKey("agents.agent_id"), nullable=False, index=True)
    task_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    priority = Column(Integer, default=5)
    payload = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    agent = relationship("AgentStateModel", back_populates="tasks")


class AgentEventModel(Base):
    """Persisted events emitted across the multi-agent algo system."""
    __tablename__ = "agent_events"

    event_id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    agent_id = Column(String(50), ForeignKey("agents.agent_id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    task_id = Column(String(50), nullable=True, index=True)
    message = Column(Text, nullable=True)
    event_metadata = Column("metadata", JSON, nullable=True)

    agent = relationship("AgentStateModel", back_populates="events")


class PerformanceSnapshot(Base):
    """Periodic or event-driven portfolio performance metrics."""
    __tablename__ = "performance_snapshots"

    snapshot_id = Column(String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    expectancy = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    equity = Column(Float, default=0.0)
    balance = Column(Float, default=0.0)
    metrics_json = Column(JSON, nullable=True)
