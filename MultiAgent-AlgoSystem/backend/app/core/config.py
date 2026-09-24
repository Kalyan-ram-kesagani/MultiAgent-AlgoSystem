from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentMode(str, Enum):
    SANDBOX = "SANDBOX"
    DEMO = "DEMO"
    LIVE = "LIVE"
    DEVELOPMENT = "DEVELOPMENT"  # Alias mapped to SANDBOX for dev workflows


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Environment
    PROJECT_NAME: str = "Autonomous AI Trading System"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "SANDBOX"
    TRADING_MODE: str = "DEMO"                  # DEMO | PAPER | LIVE (LIVE locked by default)
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # OpenAI & AI Trading Agent
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    SECRET_KEY: str = "trading_secret_key_default"

    # Database: SQLite fallback by default, PostgreSQL supported
    DATABASE_URL: str = "sqlite+aiosqlite:///./trading_platform.db"
    REDIS_URL: Optional[str] = None

    # MetaTrader 5 Configuration
    MT5_PATH: str = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
    MT5_LOGIN: Optional[int] = None
    MT5_PASSWORD: Optional[str] = None
    MT5_SERVER: Optional[str] = None
    MT5_TIMEOUT_MS: int = 60000
    MT5_PORTABLE: bool = False

    # Live & Demo Safety Locks
    LIVE_TRADING_ACKNOWLEDGED: bool = False     # Hard gate: MUST be True in .env to allow LIVE orders
    MAX_TICK_AGE_SECONDS: float = 10.0         # Reject signals if market ticks are older than 10s
    IDEMPOTENCY_WINDOW_SECONDS: int = 30       # Deduplicate repeated orders within 30s
    DEMO_MAX_ORDER_LOTS: float = 0.50          # Guardrail ceiling for demo order volume

    @field_validator("MT5_LOGIN", mode="before")
    @classmethod
    def parse_mt5_login(cls, v):
        if v == "" or v is None:
            return None
        return int(v)

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def parse_database_url(cls, v):
        if not v:
            return "sqlite+aiosqlite:///./trading_platform.db"
        url = str(v).strip().strip("'\"")
        # Automatically upgrade postgresql/postgres URLs to use asyncpg dialect
        if url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://"):]
        return url

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def parse_environment(cls, v):
        if not v:
            return "SANDBOX"
        val = str(v).strip().upper()
        if val in ("DEV", "DEVELOPMENT"):
            return "SANDBOX"
        return val

    # Risk Engine Hard Limits
    RISK_PER_TRADE_PCT: float = 0.01          # 1% per trade
    MAX_DAILY_LOSS_PCT: float = 0.03          # 3% daily loss triggers circuit breaker
    MAX_WEEKLY_LOSS_PCT: float = 0.06         # 6% weekly loss
    MAX_ACCOUNT_DRAWDOWN_PCT: float = 0.10    # 10% maximum portfolio drawdown
    MAX_OPEN_POSITIONS: int = 5
    MAX_SYMBOL_EXPOSURE: int = 2
    MAX_ALLOWED_SPREAD_PIPS: float = 5.0
    MAX_SLIPPAGE_POINTS: int = 20
    CONSECUTIVE_LOSS_LIMIT: int = 3

    # Emergency Kill Switch
    EMERGENCY_KILL_SWITCH_ACTIVE: bool = False
    AUTO_KILL_ON_MT5_DISCONNECT: bool = True

    @property
    def is_sandbox(self) -> bool:
        return self.ENVIRONMENT.upper() in ("SANDBOX", "DEVELOPMENT")

    @property
    def is_demo(self) -> bool:
        return self.ENVIRONMENT.upper() == "DEMO"

    @property
    def is_live(self) -> bool:
        return self.ENVIRONMENT.upper() == "LIVE"

    def get_safe_dict(self) -> Dict[str, Any]:
        """Return configuration dictionary with all secrets and passwords masked."""
        data = self.model_dump()
        if data.get("MT5_PASSWORD"):
            data["MT5_PASSWORD"] = "********"
        if data.get("SECRET_KEY"):
            data["SECRET_KEY"] = "********"
        if data.get("OPENAI_API_KEY"):
            data["OPENAI_API_KEY"] = "********"
        db_url = data.get("DATABASE_URL", "")
        if "@" in db_url and "://" in db_url:
            # Mask user:password in database url
            prefix, rest = db_url.split("://", 1)
            auth, host = rest.split("@", 1)
            if ":" in auth:
                user = auth.split(":", 1)[0]
                data["DATABASE_URL"] = f"{prefix}://{user}:********@{host}"
        return data


settings = Settings()

