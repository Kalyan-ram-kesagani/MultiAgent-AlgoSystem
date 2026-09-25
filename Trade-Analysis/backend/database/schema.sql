-- ====================================================================
-- Automated Trading System - Production PostgreSQL Database Schema
-- Designed for High-Throughput MT5 Execution, Multi-Account Isolation,
-- Risk Management, and Future AI Layer Ingestion.
-- ====================================================================

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(150),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Trading Accounts (Multiple MT5 Account Support)
CREATE TABLE IF NOT EXISTS trading_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    broker VARCHAR(100) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    account_number VARCHAR(50) NOT NULL,
    masked_number VARCHAR(20) NOT NULL,
    server VARCHAR(100) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    balance NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    equity NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    margin NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    free_margin NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    margin_level NUMERIC(8, 2) DEFAULT 0.00,
    floating_pl NUMERIC(15, 2) DEFAULT 0.00,
    status VARCHAR(20) DEFAULT 'connected' CHECK (status IN ('connected', 'disconnected', 'delayed')),
    account_type VARCHAR(20) DEFAULT 'demo' CHECK (account_type IN ('live', 'demo')),
    leverage INT DEFAULT 100,
    last_sync TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, account_number, server)
);

CREATE INDEX IF NOT EXISTS idx_trading_accounts_user_id ON trading_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_accounts_status ON trading_accounts(status);

-- 3. Strategies
CREATE TABLE IF NOT EXISTS strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'testing' CHECK (status IN ('active', 'testing', 'archived')),
    rules JSONB DEFAULT '[]'::jsonb,
    risk_parameters JSONB DEFAULT '{}'::jsonb,
    version_history JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_strategies_status ON strategies(status);

-- 4. Trades (Completed and Archived Execution Records)
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket BIGINT NOT NULL,
    account_id UUID NOT NULL REFERENCES trading_accounts(id) ON DELETE CASCADE,
    strategy_id UUID REFERENCES strategies(id) ON DELETE SET NULL,
    symbol VARCHAR(30) NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('BUY', 'SELL')),
    volume NUMERIC(10, 2) NOT NULL,
    entry_price NUMERIC(15, 5) NOT NULL,
    exit_price NUMERIC(15, 5) NOT NULL,
    stop_loss NUMERIC(15, 5),
    take_profit NUMERIC(15, 5),
    entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
    exit_time TIMESTAMP WITH TIME ZONE NOT NULL,
    profit_loss NUMERIC(15, 2) NOT NULL,
    commission NUMERIC(10, 2) DEFAULT 0.00,
    swap NUMERIC(10, 2) DEFAULT 0.00,
    net_pl NUMERIC(15, 2) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('WIN', 'LOSS', 'BREAKEVEN')),
    -- Risk Management Fields
    initial_risk_percent NUMERIC(5, 2) DEFAULT 1.00,
    initial_risk_amount NUMERIC(15, 2) DEFAULT 0.00,
    risk_free_status VARCHAR(10) DEFAULT 'NO' CHECK (risk_free_status IN ('YES', 'NO', 'N/A')),
    break_even_price NUMERIC(15, 5),
    risk_free_activated_time TIMESTAMP WITH TIME ZONE,
    risk_reward_ratio NUMERIC(6, 2),
    notes TEXT,
    -- Reserved fields for Future AI Layer Integration
    ai_analyzed BOOLEAN DEFAULT FALSE,
    ai_classification VARCHAR(50),
    ai_execution_quality_score NUMERIC(5, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, ticket)
);

CREATE INDEX IF NOT EXISTS idx_trades_account_id ON trades(account_id);
CREATE INDEX IF NOT EXISTS idx_trades_strategy_id ON trades(strategy_id);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time);
CREATE INDEX IF NOT EXISTS idx_trades_risk_free ON trades(risk_free_status);

-- 5. Open Positions (Live Real-Time Positions)
CREATE TABLE IF NOT EXISTS open_positions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket BIGINT NOT NULL,
    account_id UUID NOT NULL REFERENCES trading_accounts(id) ON DELETE CASCADE,
    symbol VARCHAR(30) NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('BUY', 'SELL')),
    volume NUMERIC(10, 2) NOT NULL,
    entry_price NUMERIC(15, 5) NOT NULL,
    current_price NUMERIC(15, 5) NOT NULL,
    stop_loss NUMERIC(15, 5),
    take_profit NUMERIC(15, 5),
    floating_pl NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
    risk_free_status VARCHAR(10) DEFAULT 'NO' CHECK (risk_free_status IN ('YES', 'NO', 'N/A')),
    break_even_price NUMERIC(15, 5),
    entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
    strategy_name VARCHAR(100),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, ticket)
);

CREATE INDEX IF NOT EXISTS idx_open_positions_account_id ON open_positions(account_id);

-- 6. Journal Entries
CREATE TABLE IF NOT EXISTS journal_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id UUID REFERENCES trades(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES trading_accounts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(30) NOT NULL,
    date DATE NOT NULL,
    result VARCHAR(20) NOT NULL CHECK (result IN ('WIN', 'LOSS', 'BREAKEVEN')),
    notes TEXT NOT NULL,
    reason TEXT NOT NULL,
    lessons TEXT NOT NULL,
    strategy_version VARCHAR(50),
    tags TEXT[] DEFAULT '{}',
    -- Reserved for AI Phase
    ai_detected_reason TEXT,
    ai_recommendation TEXT,
    ai_modification TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_journal_account_id ON journal_entries(account_id);
CREATE INDEX IF NOT EXISTS idx_journal_trade_id ON journal_entries(trade_id);

-- 7. System Activities (Event Audit Log)
CREATE TABLE IF NOT EXISTS system_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID REFERENCES trading_accounts(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    symbol VARCHAR(30),
    pl NUMERIC(15, 2),
    level VARCHAR(20) DEFAULT 'info' CHECK (level IN ('info', 'success', 'warning', 'error')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_system_activities_account_id ON system_activities(account_id);
CREATE INDEX IF NOT EXISTS idx_system_activities_created_at ON system_activities(created_at DESC);

-- 8. Risk Configurations
CREATE TABLE IF NOT EXISTS risk_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES trading_accounts(id) ON DELETE CASCADE UNIQUE,
    daily_risk_limit_percent NUMERIC(5, 2) DEFAULT 5.00,
    max_drawdown_limit_percent NUMERIC(5, 2) DEFAULT 4.00,
    max_risk_per_trade_percent NUMERIC(5, 2) DEFAULT 1.00,
    max_open_positions INT DEFAULT 3,
    breakeven_trigger_r NUMERIC(4, 2) DEFAULT 1.00,
    breakeven_offset_pips NUMERIC(4, 1) DEFAULT 1.0,
    trading_locked BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
