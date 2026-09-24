"""Risk event and circuit breaker state models."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database.base import Base, TimestampMixin


class RiskEvent(Base, TimestampMixin):
    """Log of every risk decision, rule violation, or limit enforcement."""
    __tablename__ = "risk_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)  # ORDER_REJECTED, ORDER_SIZED, CIRCUIT_BREAKER_TRIGGERED, KILL_SWITCH_ENGAGED
    symbol: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    strategy_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    reason: Mapped[str] = mapped_column(String(128), nullable=False)
    metrics_snapshot_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_taken: Mapped[str] = mapped_column(String(64), nullable=False)


class CircuitBreakerState(Base, TimestampMixin):
    """Current state of system safety switches and circuit breakers."""
    __tablename__ = "circuit_breaker_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    system_kill_switch_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trading_paused: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    pause_reason: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    consecutive_losses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_day_loss: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    current_week_loss: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    peak_equity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    current_drawdown_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    last_reset_day: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
