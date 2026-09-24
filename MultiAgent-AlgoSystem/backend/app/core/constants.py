"""System-wide enums and core constants."""
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "DEVELOPMENT"
    BACKTEST = "BACKTEST"
    PAPER = "PAPER"
    LIVE = "LIVE"


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    RESEARCH = "research"
    DATA = "data"
    STRATEGY = "strategy"
    ML = "ml"
    BACKTEST = "backtest"
    RISK = "risk"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    JOURNAL = "journal"
    PERFORMANCE = "performance"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class OrderStatus(str, Enum):
    PENDING_RISK = "PENDING_RISK"
    RISK_APPROVED = "RISK_APPROVED"
    RISK_REJECTED = "RISK_REJECTED"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    SUBMITTING = "SUBMITTING"
    RECONCILED = "RECONCILED"


class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RISK_REJECTED = "RISK_REJECTED"
    APPROVED = "APPROVED"
    SUBMITTING = "SUBMITTING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RECONCILED = "RECONCILED"


class StrategyStatus(str, Enum):
    DRAFT = "DRAFT"
    BACKTESTING = "BACKTESTING"
    VALIDATED = "VALIDATED"
    PAPER = "PAPER"
    LIVE = "LIVE"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


class ModelStatus(str, Enum):
    TRAINING = "TRAINING"
    VALIDATED = "VALIDATED"
    PAPER = "PAPER"
    PRODUCTION = "PRODUCTION"
    RETIRED = "RETIRED"


class MarketRegime(str, Enum):
    TREND_UP = "TREND_UP"
    TREND_DOWN = "TREND_DOWN"
    RANGE = "RANGE"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    UNCERTAIN = "UNCERTAIN"


class DataQualityStatus(str, Enum):
    VALIDATED = "VALIDATED"
    FLAGGED = "FLAGGED"
    REJECTED = "REJECTED"


class AlertLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class TimeFrame(str, Enum):
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    M30 = "M30"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"
