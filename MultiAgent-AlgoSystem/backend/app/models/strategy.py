"""Strategy and strategy version models."""
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database.base import Base, TimestampMixin


class Strategy(Base, TimestampMixin):
    """Trading strategy definition."""
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    current_version: Mapped[str] = mapped_column(String(32), default="v1.0.0", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", nullable=False)  # DRAFT, VALIDATED, PAPER, LIVE, etc.


class StrategyVersion(Base, TimestampMixin):
    """Immutable versioned snapshot of strategy code and parameters."""
    __tablename__ = "strategy_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    code_version: Mapped[str] = mapped_column(String(64), default="v1.0.0", nullable=False)
    rules: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parameters_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON-encoded parameters
    created_from: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    experiment_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    author: Mapped[str] = mapped_column(String(64), default="system", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="CANDIDATE", nullable=False)  # BASELINE, CANDIDATE, REJECTED, DEMO, APPROVED
    changelog: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_strategy_version", "strategy_id", "version", unique=True),
    )
