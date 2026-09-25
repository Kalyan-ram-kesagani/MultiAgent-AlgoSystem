import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Enum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    accounts = relationship("TradingAccount", back_populates="user", cascade="all, delete-orphan")
    journal_entries = relationship("JournalEntry", back_populates="user", cascade="all, delete-orphan")


class TradingAccount(Base):
    __tablename__ = "trading_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    broker = Column(String(100), nullable=False)
    account_name = Column(String(100), nullable=False)
    account_number = Column(String(50), nullable=False)
    balance = Column(Float, default=0.0)
    equity = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")
    account_type = Column(String(10), default="live")  # live, demo
    status = Column(String(20), default="disconnected")  # connected, disconnected, error
    last_sync = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="accounts")
    trades = relationship("Trade", back_populates="account", cascade="all, delete-orphan")


class Trade(Base):
    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("trading_accounts.id"), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    direction = Column(String(4), nullable=False)  # BUY, SELL
    volume = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=True)
    profit_loss = Column(Float, nullable=True)
    commission = Column(Float, default=0.0)
    swap = Column(Float, default=0.0)
    status = Column(String(20), nullable=False, default="OPEN")  # OPEN, CLOSED, PENDING, CANCELLED
    result = Column(String(20), nullable=True)  # WIN, LOSS, BREAKEVEN
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=True)

    # Risk management fields
    initial_risk_percent = Column(Float, nullable=True)
    initial_risk_amount = Column(Float, nullable=True)
    risk_free_status = Column(String(3), default="N/A")  # YES, NO, N/A
    break_even_price = Column(Float, nullable=True)
    risk_free_activated_time = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    account = relationship("TradingAccount", back_populates="trades")
    strategy = relationship("Strategy", back_populates="trades")
    journal_entry = relationship("JournalEntry", back_populates="trade", uselist=False)

    __table_args__ = (
        Index("ix_trades_account_symbol", "account_id", "symbol"),
        Index("ix_trades_account_status", "account_id", "status"),
        Index("ix_trades_entry_time", "entry_time"),
    )


class Strategy(Base):
    __tablename__ = "strategies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="active")  # active, testing, archived
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    trades = relationship("Trade", back_populates="strategy")


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trade_id = Column(UUID(as_uuid=True), ForeignKey("trades.id"), nullable=True, unique=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    lessons = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    trade = relationship("Trade", back_populates="journal_entry")
    user = relationship("User", back_populates="journal_entries")


# ─── Future AI Tables (schema only, not implemented) ───
# These will be added in Phase 5+ when AI functionality is built.
# Keeping the schema comment here for documentation:
#
# class AITradeAnalysis(Base):
#     __tablename__ = "ai_trade_analyses"
#     id, trade_id, analysis_type, analysis_result, confidence, created_at
#
# class AIStrategyVersion(Base):
#     __tablename__ = "ai_strategy_versions"
#     id, strategy_id, parent_version_id, changes, performance_prediction, created_at
#
# class AIRecommendation(Base):
#     __tablename__ = "ai_recommendations"
#     id, user_id, recommendation_type, content, status, created_at
