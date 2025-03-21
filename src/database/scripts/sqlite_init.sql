-- SQLite initialization script for Multi-Agent Trading System V2

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id VARCHAR(36) PRIMARY KEY,
    theme VARCHAR(20) DEFAULT 'light',
    default_instrument VARCHAR(20),
    default_frequency VARCHAR(10),
    email_notifications BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Backtest results table
CREATE TABLE IF NOT EXISTS backtest_results (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    strategy_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    total_return DECIMAL(10, 2) NOT NULL,
    max_drawdown DECIMAL(10, 2) NOT NULL,
    sharpe_ratio DECIMAL(10, 2),
    trade_count INTEGER NOT NULL,
    win_rate DECIMAL(5, 2),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    parameters TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Trade history table
CREATE TABLE IF NOT EXISTS trade_history (
    id VARCHAR(36) PRIMARY KEY,
    backtest_id VARCHAR(36) NOT NULL,
    entry_time TIMESTAMP NOT NULL,
    exit_time TIMESTAMP,
    instrument VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    entry_price DECIMAL(16, 8) NOT NULL,
    exit_price DECIMAL(16, 8),
    quantity DECIMAL(16, 8) NOT NULL,
    profit_loss DECIMAL(16, 8),
    profit_loss_percent DECIMAL(10, 2),
    exit_reason VARCHAR(50),
    FOREIGN KEY (backtest_id) REFERENCES backtest_results(id) ON DELETE CASCADE
);

-- Strategy sharing table
CREATE TABLE IF NOT EXISTS strategy_sharing (
    id VARCHAR(36) PRIMARY KEY,
    strategy_id VARCHAR(36) NOT NULL,
    owner_id VARCHAR(36) NOT NULL,
    shared_with_id VARCHAR(36) NOT NULL,
    permission_level VARCHAR(20) NOT NULL DEFAULT 'read',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(strategy_id, shared_with_id),
    FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (shared_with_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_backtest_user ON backtest_results(user_id);
CREATE INDEX IF NOT EXISTS idx_trades_backtest ON trade_history(backtest_id);
CREATE INDEX IF NOT EXISTS idx_sharing_owner ON strategy_sharing(owner_id);
CREATE INDEX IF NOT EXISTS idx_sharing_shared ON strategy_sharing(shared_with_id);

-- Insert test data (only for development)
INSERT OR IGNORE INTO users (id, username, email, password_hash, is_active)
VALUES 
    ('user_test1', 'testuser', 'test@example.com', 'pbkdf2:sha256:150000$AbC123$789def...', TRUE);

INSERT OR IGNORE INTO user_preferences (user_id, theme, default_instrument, default_frequency)
VALUES 
    ('user_test1', 'dark', 'BTCUSDT', '1h');