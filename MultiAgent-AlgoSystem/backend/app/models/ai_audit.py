"""AI Agent Auditing, Tool Calls, Order Requests, and Kill Switch State Models."""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base, TimestampMixin


class AIAgentRun(Base, TimestampMixin):
    """Immutable audit record of each AI Trading & Research Agent execution."""
    __tablename__ = "ai_agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True, default=lambda: f"RUN-{uuid.uuid4().hex[:12].upper()}")
    agent_name: Mapped[str] = mapped_column(String(64), default="TradingResearchAgent", nullable=False)
    task: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="RUNNING", nullable=False, index=True)  # RUNNING, COMPLETED, FAILED, TIMEOUT
    model: Mapped[str] = mapped_column(String(64), default="gpt-4o-mini", nullable=False)
    
    input_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    final_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tool_calls: Mapped[list["AIToolCall"]] = relationship("AIToolCall", back_populates="run", cascade="all, delete-orphan")
    order_requests: Mapped[list["OrderRequestModel"]] = relationship("OrderRequestModel", back_populates="run")


class AIToolCall(Base, TimestampMixin):
    """Audit record of every individual tool execution called by the AI Agent."""
    __tablename__ = "ai_tool_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tool_call_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True, default=lambda: f"TC-{uuid.uuid4().hex[:12].upper()}")
    run_id: Mapped[str] = mapped_column(String(64), ForeignKey("ai_agent_runs.run_id", ondelete="CASCADE"), nullable=False, index=True)
    tool_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    input_arguments_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    output_result_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    run: Mapped["AIAgentRun"] = relationship("AIAgentRun", back_populates="tool_calls")


class OrderRequestModel(Base, TimestampMixin):
    """
    Controlled order proposal created by the AI Agent.
    Strictly evaluated by the Deterministic Risk Engine before any broker placement.
    """
    __tablename__ = "order_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True, default=lambda: f"REQ-{uuid.uuid4().hex[:12].upper()}")
    run_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("ai_agent_runs.run_id", ondelete="SET NULL"), nullable=True, index=True)
    
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(16), nullable=False)  # BUY, SELL
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    stop_loss: Mapped[float] = mapped_column(Float, nullable=False)
    take_profit: Mapped[float] = mapped_column(Float, nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Risk Engine Validation Outcome
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rejection_reasons_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_evaluation_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_lots: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Execution Outcome
    execution_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    execution_status: Mapped[str] = mapped_column(String(32), default="PENDING_RISK", nullable=False)  # PENDING, RISK_REJECTED, APPROVED, SUBMITTING, EXECUTED, FAILED, CANCELLED, RECONCILED
    broker_ticket: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    broker_deal_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    execution_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    run: Mapped[Optional["AIAgentRun"]] = relationship("AIAgentRun", back_populates="order_requests")


class KillSwitchStateModel(Base, TimestampMixin):
    """Persisted Kill Switch state in Supabase PostgreSQL / SQLite."""
    __tablename__ = "kill_switch_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    operator: Mapped[Optional[str]] = mapped_column(String(64), default="SYSTEM", nullable=True)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
