"""Database engine and session management with async support."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from backend.app.core.config import settings
from backend.app.database.base import Base

# Configure engine: works seamlessly for both SQLite (aiosqlite) and PostgreSQL (asyncpg)
engine_kwargs = {
    "echo": False,
    "future": True,
}

if "sqlite" in settings.DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30.0}
else:
    # PostgreSQL / Supabase settings: robust pooling & pre-ping for remote connections
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for yielding an async database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables and run non-destructive schema migrations."""
    async with engine.begin() as conn:
        if "sqlite" in settings.DATABASE_URL:
            from sqlalchemy import text
            try:
                await conn.execute(text("PRAGMA journal_mode=WAL;"))
                await conn.execute(text("PRAGMA busy_timeout=30000;"))
            except Exception:
                pass

        await conn.run_sync(Base.metadata.create_all)

        # Non-destructive column additions for existing tables
        from sqlalchemy import text
        for stmt in [
            "ALTER TABLE order_requests ADD COLUMN execution_id VARCHAR(64);",
            "CREATE INDEX IF NOT EXISTS ix_order_requests_execution_id ON order_requests (execution_id);",
            "ALTER TABLE trades ADD COLUMN broker_deal_id BIGINT;",
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_trades_broker_deal_id ON trades (broker_deal_id);",
            "ALTER TABLE trades ADD COLUMN origin VARCHAR(30) DEFAULT 'SYSTEM_GENERATED';",
            "ALTER TABLE hypotheses ADD COLUMN strategy_id VARCHAR(64) DEFAULT 'strategy_v1';",
            "ALTER TABLE hypotheses ADD COLUMN evidence_json TEXT;",
            "ALTER TABLE experiments ADD COLUMN experiment_name VARCHAR(128) DEFAULT 'Experiment';",
            "ALTER TABLE experiments ADD COLUMN baseline_strategy_version VARCHAR(32) DEFAULT 'v1.0.0';",
            "ALTER TABLE experiments ADD COLUMN candidate_strategy_version VARCHAR(32) DEFAULT 'v1.1.0';",
            "ALTER TABLE experiments ADD COLUMN dataset_description VARCHAR(256) DEFAULT 'EURUSD_H1';",
            "ALTER TABLE experiments ADD COLUMN testing_period VARCHAR(128);",
            "ALTER TABLE experiments ADD COLUMN sample_size INTEGER DEFAULT 0;",
            "ALTER TABLE experiments ADD COLUMN created_by VARCHAR(64) DEFAULT 'TradingResearchAgent';",
            "ALTER TABLE experiments ADD COLUMN completed_at TIMESTAMP;",
            "ALTER TABLE strategy_versions ADD COLUMN rules TEXT;",
            "ALTER TABLE strategy_versions ADD COLUMN created_from VARCHAR(32);",
            "ALTER TABLE strategy_versions ADD COLUMN experiment_id VARCHAR(64);",
        ]:
            try:
                await conn.execute(text(stmt))
            except Exception:
                pass

