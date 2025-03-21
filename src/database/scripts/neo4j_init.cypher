// Neo4j Initialization Script for Multi-Agent Trading System V2

// Create constraints and indexes
CREATE CONSTRAINT strategy_type_name IF NOT EXISTS FOR (s:StrategyType) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT instrument_symbol IF NOT EXISTS FOR (i:Instrument) REQUIRE i.symbol IS UNIQUE;
CREATE CONSTRAINT indicator_name IF NOT EXISTS FOR (i:Indicator) REQUIRE i.name IS UNIQUE;
CREATE CONSTRAINT strategy_id IF NOT EXISTS FOR (s:Strategy) REQUIRE s.id IS UNIQUE;
CREATE INDEX strategy_user_idx IF NOT EXISTS FOR (s:Strategy) ON (s.user_id);
CREATE INDEX condition_type_idx IF NOT EXISTS FOR (c:Condition) ON (c.type);

// Create basic strategy types
CREATE (s:StrategyType {name: "momentum", description: "Trading strategy based on price momentum", version: 1});
CREATE (s:StrategyType {name: "mean_reversion", description: "Trading strategy based on price returning to mean", version: 1});
CREATE (s:StrategyType {name: "trend_following", description: "Trading strategy based on following established trends", version: 1});

// Create instruments
CREATE (i:Instrument {symbol: "BTCUSDT", type: "crypto", data_source: "Binance API", min_order_size: 0.001, max_order_size: 100});
CREATE (i:Instrument {symbol: "ETHUSDT", type: "crypto", data_source: "Binance API", min_order_size: 0.01, max_order_size: 1000});

// Create frequencies
CREATE (f:Frequency {name: "1h", description: "1 hour interval", milliseconds: 3600000});
CREATE (f:Frequency {name: "4h", description: "4 hour interval", milliseconds: 14400000});
CREATE (f:Frequency {name: "1d", description: "1 day interval", milliseconds: 86400000});

// Create indicators
CREATE (i:Indicator {name: "RSI", description: "Relative Strength Index", version: 1});
CREATE (i:Indicator {name: "EMA", description: "Exponential Moving Average", version: 1});
CREATE (i:Indicator {name: "MACD", description: "Moving Average Convergence Divergence", version: 1});

// Create parameters
CREATE (p:Parameter {name: "period", default_value: 14, min_value: 5, max_value: 50, type: "integer"});
CREATE (p:Parameter {name: "fast_period", default_value: 12, min_value: 5, max_value: 30, type: "integer"});
CREATE (p:Parameter {name: "slow_period", default_value: 26, min_value: 10, max_value: 50, type: "integer"});

// Create relationships
MATCH (i:Indicator {name: "RSI"}), (p:Parameter {name: "period"})
CREATE (i)-[:HAS_PARAMETER {is_required: true}]->(p);

MATCH (s:StrategyType {name: "momentum"}), (i:Indicator {name: "RSI"})
CREATE (s)-[:COMMONLY_USES {strength: 0.8}]->(i);

MATCH (i:Instrument {symbol: "BTCUSDT"}), (f:Frequency {name: "1h"})
CREATE (i)-[:APPROVED_FOR {status: "active"}]->(f);

// Create conditions
CREATE (c:Condition {logic: "RSI < 30", type: "entry", description: "Enter when RSI is below 30"});
CREATE (c:Condition {logic: "RSI > 70", type: "exit", description: "Exit when RSI is above 70"});