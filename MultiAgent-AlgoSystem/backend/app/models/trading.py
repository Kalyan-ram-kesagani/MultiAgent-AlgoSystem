"""Signals, Orders, Trades, and Positions models."""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database.base import Base, TimestampMixin


class Signal(Base, TimestampMixin):
    """Trading signal emitted by strategy rule evaluator."""
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    signal_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    strategy_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    strategy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)  # BUY, SELL
    timeframe: Mapped[str] = mapped_column(String(16), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    suggested_entry: Mapped[float] = mapped_column(Float, nullable=False)
    suggested_sl: Mapped[float] = mapped_column(Float, nullable=False)
    suggested_tp: Mapped[float] = mapped_column(Float, nullable=False)
    risk_points: Mapped[float] = mapped_column(Float, nullable=False)
    ml_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    market_regime: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    context_data_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Order(Base, TimestampMixin):
    """Order submitted for execution through Risk Engine and MT5 Gateway."""
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_order_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    strategy_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    signal_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(16), nullable=False)  # BUY, SELL
    order_type: Mapped[str] = mapped_column(String(32), default="MARKET", nullable=False)

    quantity: Mapped[float] = mapped_column(Float, nullable=False)  # Lot size
    price: Mapped[float] = mapped_column(Float, nullable=False)
    sl: Mapped[float] = mapped_column(Float, nullable=False)
    tp: Mapped[float] = mapped_column(Float, nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="PENDING_RISK", nullable=False, index=True)
    risk_evaluation_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    broker_ticket: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    broker_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class Trade(Base, TimestampMixin):
    """Closed trade record for performance analysis and automated journaling."""
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trade_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    strategy_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ticket: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    broker_deal_id: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True, nullable=True, index=True)

    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exit_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    stop_price: Mapped[float] = mapped_column(Float, nullable=False)
    target_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[float] = mapped_column(Float, nullable=False)

    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    commission: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    swap: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    pnl: Mapped[float] = mapped_column(Float, nullable=False)
    r_multiple: Mapped[float] = mapped_column(Float, nullable=False)
    mfe: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # Maximum Favorable Excursion
    mae: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # Maximum Adverse Excursion
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    session: Mapped[str] = mapped_column(String(32), default="UNKNOWN", nullable=False)
    origin: Mapped[str] = mapped_column(String(32), default="SYSTEM_GENERATED", nullable=False)  # SYSTEM_GENERATED, MANUAL, EXTERNAL, UNKNOWN
    market_regime: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    exit_reason: Mapped[str] = mapped_column(String(32), default="TP", nullable=False)  # TP, SL, TIMEOUT, MANUAL, KILL_SWITCH


class Position(Base, TimestampMixin):
    """Currently open market position."""
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    strategy_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(16), nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    open_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float] = mapped_column(Float, nullable=False)
    sl: Mapped[float] = mapped_column(Float, nullable=False)
    tp: Mapped[float] = mapped_column(Float, nullable=False)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
