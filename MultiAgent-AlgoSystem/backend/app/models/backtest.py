"""Backtest run and backtest trade models."""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.database.base import Base, TimestampMixin


class BacktestRun(Base, TimestampMixin):
    """Backtesting execution record with detailed metrics and assumptions."""
    __tablename__ = "backtest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    backtest_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    strategy_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    strategy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(16), nullable=False)

    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    initial_capital: Mapped[float] = mapped_column(Float, default=10000.0, nullable=False)

    # Execution assumptions
    spread_pips: Mapped[float] = mapped_column(Float, default=1.5, nullable=False)
    slippage_points: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    commission_per_lot: Mapped[float] = mapped_column(Float, default=7.0, nullable=False)
    parameters_json: Mapped[str] = mapped_column(Text, nullable=False)

    # Performance Metrics
    total_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    winning_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    losing_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    net_profit: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    profit_factor: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    expectancy: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_win: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_loss: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_drawdown_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sharpe_ratio: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    sortino_ratio: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    average_r: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Anti-overfitting / Walk-forward / Monte Carlo summary
    is_out_of_sample: Mapped[bool] = mapped_column(default=False)
    monte_carlo_drawdown_95: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    equity_curve_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class BacktestTrade(Base, TimestampMixin):
    """Simulated trade executed during backtest run."""
    __tablename__ = "backtest_trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    backtest_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    direction: Mapped[str] = mapped_column(String(16), nullable=False)

    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exit_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[float] = mapped_column(Float, nullable=False)
    sl: Mapped[float] = mapped_column(Float, nullable=False)
    tp: Mapped[float] = mapped_column(Float, nullable=False)

    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    pnl: Mapped[float] = mapped_column(Float, nullable=False)
    r_multiple: Mapped[float] = mapped_column(Float, nullable=False)
    commission: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    slippage_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    exit_reason: Mapped[str] = mapped_column(String(32), nullable=False)
