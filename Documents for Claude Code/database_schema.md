# Trading Strategy System: Database Schema

This document details the database schemas for the two primary databases used in the Trading Strategy System: Neo4j for the graph database and InfluxDB for time-series data. It provides implementation details, sample queries, and optimization guidelines.

## Table of Contents
1. [Neo4j Graph Database](#neo4j-graph-database)
2. [InfluxDB Time-Series Database](#influxdb-time-series-database)
3. [SQLite/PostgreSQL User Database](#sqlitepostgresql-user-database)
4. [Redis Cache](#redis-cache)
5. [Database Interaction Patterns](#database-interaction-patterns)

## Neo4j Graph Database

### Schema Overview

The Neo4j graph database stores the relationships between different trading strategy components, enabling validation, recommendations, and knowledge representation.

### Node Types

#### StrategyType
```cypher
CREATE (s:StrategyType {
  name: "momentum",
  description: "Trading strategy based on price momentum",
  version: 1
})
```

#### Instrument
```cypher
CREATE (i:Instrument {
  symbol: "BTCUSDT",
  type: "crypto",
  data_source: "Binance API",
  min_order_size: 0.001,
  max_order_size: 100
})
```

#### Frequency
```cypher
CREATE (f:Frequency {
  name: "1h",
  description: "1 hour interval",
  milliseconds: 3600000
})
```

#### Indicator
```cypher
CREATE (i:Indicator {
  name: "RSI",
  description: "Relative Strength Index",
  calculation_method: "ratio of average gains to average losses",
  version: 1
})
```

#### Parameter
```cypher
CREATE (p:Parameter {
  name: "period",
  default_value: 14,
  min_value: 5,
  max_value: 50,
  type: "integer",
  description: "Number of periods used in calculation"
})
```

#### Condition
```cypher
CREATE (c:Condition {
  logic: "RSI < 30",
  type: "entry",
  description: "Enter when RSI is below 30 (oversold)"
})
```

#### BacktestingMethod
```cypher
CREATE (b:BacktestingMethod {
  type: "walk_forward",
  description: "Testing strategy on sequential in-sample and out-of-sample periods",
  version: 1
})
```

#### Strategy (User-Created)
```cypher
CREATE (s:Strategy {
  id: "strat_123456",
  name: "My BTC Momentum Strategy",
  user_id: "user_123",
  created_at: timestamp(),
  updated_at: timestamp(),
  version: 1
})
```

### Relationships

#### Strategy Type Relationships
```cypher
// Strategy type commonly uses indicators
MATCH (s:StrategyType {name: "momentum"}), (i:Indicator {name: "RSI"})
CREATE (s)-[:COMMONLY_USES {strength: 0.8}]->(i)

// Strategy type is suitable for instruments
MATCH (s:StrategyType {name: "momentum"}), (i:Instrument {symbol: "BTCUSDT"})
CREATE (s)-[:SUITABLE_FOR {reason: "High volatility"}]->(i)

// Strategy type typically uses frequencies
MATCH (s:StrategyType {name: "momentum"}), (f:Frequency {name: "1h"})
CREATE (s)-[:TYPICAL_FREQUENCY {reason: "Captures intraday moves"}]->(f)

// Strategy type recommends backtesting methods
MATCH (s:StrategyType {name: "momentum"}), (b:BacktestingMethod {type: "walk_forward"})
CREATE (s)-[:RECOMMENDED_BACKTESTING {reason: "Tests strategy robustness"}]->(b)
```

#### Indicator Relationships
```cypher
// Indicator has parameters
MATCH (i:Indicator {name: "RSI"}), (p:Parameter {name: "period"})
CREATE (i)-[:HAS_PARAMETER {is_required: true}]->(p)

// Indicator used in conditions
MATCH (i:Indicator {name: "RSI"}), (c:Condition {logic: "RSI < 30"})
CREATE (i)-[:USED_IN]->(c)
```

#### Instrument Relationships
```cypher
// Instrument approved for frequencies
MATCH (i:Instrument {symbol: "BTCUSDT"}), (f:Frequency {name: "1h"})
CREATE (i)-[:APPROVED_FOR {status: "active", data_source: "Binance API"}]->(f)
```

#### User Strategy Relationships
```cypher
// User strategy is based on strategy type
MATCH (s:Strategy {id: "strat_123456"}), (t:StrategyType {name: "momentum"})
CREATE (s)-[:BASED_ON]->(t)

// User strategy uses instrument
MATCH (s:Strategy {id: "strat_123456"}), (i:Instrument {symbol: "BTCUSDT"})
CREATE (s)-[:USES_INSTRUMENT]->(i)

// User strategy uses frequency
MATCH (s:Strategy {id: "strat_123456"}), (f:Frequency {name: "1h"})
CREATE (s)-[:USES_FREQUENCY]->(f)

// User strategy uses indicators
MATCH (s:Strategy {id: "strat_123456"}), (i:Indicator {name: "RSI"})
CREATE (s)-[:USES_INDICATOR {parameters: {period: 14}}]->(i)

// User strategy has conditions
MATCH (s:Strategy {id: "strat_123456"}), (c:Condition {logic: "RSI < 30", type: "entry"})
CREATE (s)-[:HAS_CONDITION]->(c)
```

### Indexes and Constraints

```cypher
// Create unique constraints
CREATE CONSTRAINT strategy_type_name IF NOT EXISTS FOR (s:StrategyType) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT instrument_symbol IF NOT EXISTS FOR (i:Instrument) REQUIRE i.symbol IS UNIQUE;
CREATE CONSTRAINT indicator_name IF NOT EXISTS FOR (i:Indicator) REQUIRE i.name IS UNIQUE;
CREATE CONSTRAINT strategy_id IF NOT EXISTS FOR (s:Strategy) REQUIRE s.id IS UNIQUE;

// Create indexes for performance
CREATE INDEX strategy_user_idx IF NOT EXISTS FOR (s:Strategy) ON (s.user_id);
CREATE INDEX condition_type_idx IF NOT EXISTS FOR (c:Condition) ON (c.type);
```

### Sample Queries

#### Get indicators recommended for a strategy type
```cypher
MATCH (s:StrategyType {name: $strategy_type})-[:COMMONLY_USES]->(i:Indicator)
RETURN i.name AS name, i.description AS description
```

#### Get compatible instruments for a strategy type and frequency
```cypher
MATCH (s:StrategyType {name: $strategy_type})-[:SUITABLE_FOR]->(i:Instrument),
      (i)-[:APPROVED_FOR]->(f:Frequency {name: $frequency})
RETURN i.symbol AS symbol, i.type AS type
```

#### Get a complete user strategy with all components
```cypher
MATCH (s:Strategy {id: $strategy_id})
OPTIONAL MATCH (s)-[:BASED_ON]->(t:StrategyType)
OPTIONAL MATCH (s)-[:USES_INSTRUMENT]->(i:Instrument)
OPTIONAL MATCH (s)-[:USES_FREQUENCY]->(f:Frequency)
OPTIONAL MATCH (s)-[:USES_INDICATOR]->(ind:Indicator)
OPTIONAL MATCH (s)-[:HAS_CONDITION]->(c:Condition)
RETURN s, t, i, f,
       collect(distinct {indicator: ind, parameters: (s)-[:USES_INDICATOR]->(ind).parameters}) AS indicators,
       collect(distinct c) AS conditions
```

#### Validate indicator parameter
```cypher
MATCH (i:Indicator {name: $indicator_name})-[:HAS_PARAMETER]->(p:Parameter {name: $parameter_name})
RETURN $parameter_value >= p.min_value AND $parameter_value <= p.max_value AS is_valid,
       p.min_value AS min_value, p.max_value AS max_value
```

## InfluxDB Time-Series Database

### Data Structure

InfluxDB organizes data using the following concepts:
- **Bucket**: Container for time-series data (e.g., "market_data")
- **Measurement**: Name of the time-series (e.g., instrument symbol)
- **Tags**: Indexed metadata (e.g., frequency, data_source)
- **Fields**: Actual values (e.g., open, high, low, close, volume)
- **Timestamp**: Time for each data point

### Schema Example

```
bucket: market_data
  measurement: BTCUSDT
    tags:
      frequency: 1h
      data_source: binance
    fields:
      open: 50000.0
      high: 51000.0
      low: 49000.0
      close: 50500.0
      volume: 100.0
    timestamp: 2023-06-01T12:00:00Z
```

### Data Ingestion

#### Writing a Single Point
```python
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime

client = InfluxDBClient(url="http://localhost:8086", token="my-token", org="my-org")
write_api = client.write_api(write_options=SYNCHRONOUS)

point = Point("BTCUSDT") \
    .tag("frequency", "1h") \
    .tag("data_source", "binance") \
    .field("open", 50000.0) \
    .field("high", 51000.0) \
    .field("low", 49000.0) \
    .field("close", 50500.0) \
    .field("volume", 100.0) \
    .time(datetime.utcnow())

write_api.write(bucket="market_data", record=point)
```

#### Writing Multiple Points
```python
points = []
for i in range(100):
    timestamp = datetime(2023, 6, 1, 12, 0, 0) + timedelta(hours=i)
    point = Point("BTCUSDT") \
        .tag("frequency", "1h") \
        .tag("data_source", "binance") \
        .field("close", 50000.0 + (i * 10)) \
        .time(timestamp)
    points.append(point)

write_api.write(bucket="market_data", record=points)
```

### Data Querying

#### Basic Query (Last 24 Hours of BTCUSDT)
```python
query = '''
    from(bucket:"market_data")
    |> range(start: -24h)
    |> filter(fn: (r) => r._measurement == "BTCUSDT" and r.frequency == "1h")
    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
'''

query_api = client.query_api()
result = query_api.query(org="my-org", query=query)

# Process the result
for table in result:
    for record in table.records:
        print(f"Time: {record.get_time()}, Close: {record.values.get('close')}")
```

#### Aggregation Query (Daily OHLC for BTCUSDT)
```python
query = '''
    from(bucket:"market_data")
    |> range(start: -30d)
    |> filter(fn: (r) => r._measurement == "BTCUSDT" and r.frequency == "1h")
    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    |> window(every: 1d)
    |> first(column: "open")
    |> max(column: "high")
    |> min(column: "low")
    |> last(column: "close")
    |> sum(column: "volume")
'''
```

#### Downsampling Query (Convert 1-minute to 1-hour data)
```python
query = '''
    from(bucket:"market_data")
    |> range(start: -7d)
    |> filter(fn: (r) => r._measurement == "BTCUSDT" and r.frequency == "1m")
    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    |> window(every: 1h)
    |> first(column: "open")
    |> max(column: "high")
    |> min(column: "low")
    |> last(column: "close")
    |> sum(column: "volume")
'''
```

### Data Versioning

To support data versioning for backtesting:

```python
# Writing versioned data
point = Point("BTCUSDT") \
    .tag("frequency", "1h") \
    .tag("data_source", "binance") \
    .tag("version", "1.0") \
    .field("close", 50000.0) \
    .time(datetime.utcnow())

# Querying specific version
query = '''
    from(bucket:"market_data")
    |> range(start: -24h)
    |> filter(fn: (r) => r._measurement == "BTCUSDT" and 
                          r.frequency == "1h" and 
                          r.version == "1.0")
'''
```

### Optimization Strategies

1. **Data Partitioning**:
   - Store different timeframes in separate measurements or with distinct tags
   - Use downsampling for larger timeframes

2. **Query Optimization**:
   - Use precise time ranges to reduce data scanned
   - Filter early in the query chain
   - Use predefined variables for common filters

3. **Retention Policies**:
   - Set appropriate retention periods for different data granularities
   - Example: Keep 1-minute data for 30 days, 1-hour data for 1 year

## SQLite/PostgreSQL User Database

### Schema Overview

The relational database stores user account information, metadata, and relationships that don't fit well in the graph or time-series models.

### Tables

#### Users
```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
```

#### UserPreferences
```sql
CREATE TABLE user_preferences (
    user_id VARCHAR(36) PRIMARY KEY,
    theme VARCHAR(20) DEFAULT 'light',
    default_instrument VARCHAR(20),
    default_frequency VARCHAR(10),
    email_notifications BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### BacktestResults
```sql
CREATE TABLE backtest_results (
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
    parameters JSONB,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

#### TradeHistory
```sql
CREATE TABLE trade_history (
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
```

#### StrategySharing
```sql
CREATE TABLE strategy_sharing (
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
```

### Sample Queries

#### Get User's Backtest Results
```sql
SELECT 
    br.id, 
    br.name, 
    br.start_date, 
    br.end_date, 
    br.total_return, 
    br.max_drawdown, 
    br.sharpe_ratio, 
    br.trade_count, 
    br.win_rate
FROM 
    backtest_results br
WHERE 
    br.user_id = :user_id
ORDER BY 
    br.created_at DESC
LIMIT 10;
```

#### Get Trade History for a Backtest
```sql
SELECT 
    id, 
    entry_time, 
    exit_time, 
    instrument, 
    direction, 
    entry_price, 
    exit_price, 
    quantity, 
    profit_loss, 
    profit_loss_percent, 
    exit_reason
FROM 
    trade_history
WHERE 
    backtest_id = :backtest_id
ORDER BY 
    entry_time;
```

#### Get Shared Strategies
```sql
SELECT 
    s.id,
    s.name,
    u.username as owner,
    ss.permission_level,
    ss.created_at as shared_at
FROM 
    strategies s
JOIN 
    strategy_sharing ss ON s.id = ss.strategy_id
JOIN 
    users u ON ss.owner_id = u.id
WHERE 
    ss.shared_with_id = :user_id;
```

## Redis Cache

Redis is used for caching frequently accessed data to improve performance.

### Cache Structure

#### Session Cache
```
Key: "session:{session_id}"
Value: {
  "user_id": "user_123",
  "username": "testuser",
  "expires_at": "2023-06-02T12:00:00Z"
}
Expiry: 24 hours
```

#### API Rate Limiting
```
Key: "ratelimit:{ip_address}:{endpoint}"
Value: Counter (number of requests)
Expiry: 1 minute
```

#### Recent Market Data
```
Key: "market_data:{instrument}:{frequency}:recent"
Value: JSON array of recent OHLCV data
Expiry: 5 minutes
```

#### Indicator Calculations
```
Key: "indicator:{instrument}:{frequency}:{indicator}:{parameters_hash}"
Value: JSON array of calculated values
Expiry: 30 minutes
```

### Sample Code

#### Caching Indicator Calculations
```python
import redis
import json
import hashlib

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_indicator(instrument, frequency, indicator, parameters):
    # Create a hash of parameters for the cache key
    parameters_str = json.dumps(parameters, sort_keys=True)
    parameters_hash = hashlib.md5(parameters_str.encode()).hexdigest()
    
    cache_key = f"indicator:{instrument}:{frequency}:{indicator}:{parameters_hash}"
    
    # Try to get from cache
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)
    
    # Calculate if not in cache
    calculated_data = calculate_indicator(instrument, frequency, indicator, parameters)
    
    # Cache the result
    redis_client.setex(
        cache_key,
        1800,  # 30 minutes expiry
        json.dumps(calculated_data)
    )
    
    return calculated_data
```

#### Rate Limiting Implementation
```python
def check_rate_limit(ip_address, endpoint, limit=100):
    cache_key = f"ratelimit:{ip_address}:{endpoint}"
    
    # Increment counter
    current = redis_client.incr(cache_key)
    
    # Set expiry if first request
    if current == 1:
        redis_client.expire(cache_key, 60)  # 1 minute
    
    # Check if over limit
    return current <= limit
```

## Database Interaction Patterns

### Neo4j Interaction Pattern

```python
from neo4j import GraphDatabase

class Neo4jRepository:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def get_strategy_types(self):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:StrategyType)
                RETURN s.name AS name, s.description AS description
            """)
            return [dict(record) for record in result]
    
    def get_indicators_for_strategy(self, strategy_type):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (s:StrategyType {name: $strategy_type})-[:COMMONLY_USES]->(i:Indicator)
                RETURN i.name AS name, i.description AS description
            """, strategy_type=strategy_type)
            return [dict(record) for record in result]
    
    def create_user_strategy(self, strategy_data):
        with self.driver.session() as session:
            # Create unique ID
            import uuid
            strategy_id = f"strat_{uuid.uuid4().hex[:8]}"
            
            # Create strategy node
            session.run("""
                CREATE (s:Strategy {
                    id: $id,
                    name: $name,
                    user_id: $user_id,
                    created_at: datetime(),
                    updated_at: datetime(),
                    version: 1
                })
            """, id=strategy_id, name=strategy_data["name"], user_id=strategy_data["user_id"])
            
            # Create relationships
            session.run("""
                MATCH (s:Strategy {id: $id}), (t:StrategyType {name: $strategy_type})
                CREATE (s)-[:BASED_ON]->(t)
            """, id=strategy_id, strategy_type=strategy_data["strategy_type"])
            
            # Add instrument relationship
            session.run("""
                MATCH (s:Strategy {id: $id}), (i:Instrument {symbol: $symbol})
                CREATE (s)-[:USES_INSTRUMENT]->(i)
            """, id=strategy_id, symbol=strategy_data["instrument"])
            
            # Add other relationships...
            
            return strategy_id
```

### InfluxDB Interaction Pattern

```python
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd

class InfluxDBRepository:
    def __init__(self, url, token, org, bucket):
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.bucket = bucket
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
    
    def get_historical_data(self, instrument, frequency, start_date, end_date):
        query = f'''
            from(bucket:"{self.bucket}")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r._measurement == "{instrument}" and r.frequency == "{frequency}")
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        
        result = self.query_api.query_data_frame(query=query)
        
        # Convert to pandas DataFrame
        if isinstance(result, list) and len(result) > 0:
            df = pd.concat(result)
            # Clean up columns
            df = df[['_time', 'open', 'high', 'low', 'close', 'volume']]
            df.rename(columns={'_time': 'time'}, inplace=True)
            return df
        else:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume'])
    
    def store_calculation_results(self, instrument, frequency, calculation_type, values):
        points = []
        
        for timestamp, value in values.items():
            point = Point(instrument) \
                .tag("frequency", frequency) \
                .tag("calculation_type", calculation_type) \
                .field("value", value) \
                .time(timestamp)
            points.append(point)
        
        self.write_api.write(bucket=self.bucket, record=points)
```

### SQLite/PostgreSQL Interaction Pattern

```python
import sqlite3
import json
import uuid
from datetime import datetime

class SQLRepository:
    def __init__(self, db_path):
        self.db_path = db_path
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_user(self, username, email, password_hash):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            user_id = f"user_{uuid.uuid4().hex[:8]}"
            
            cursor.execute("""
                INSERT INTO users (id, username, email, password_hash)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, email, password_hash))
            
            return user_id
    
    def get_user_by_username(self, username):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, username, email, password_hash, created_at, last_login, is_active
                FROM users
                WHERE username = ?
            """, (username,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def store_backtest_result(self, user_id, strategy_id, name, start_date, end_date, 
                              performance_metrics, parameters):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            backtest_id = f"bt_{uuid.uuid4().hex[:8]}"
            
            cursor.execute("""
                INSERT INTO backtest_results (
                    id, user_id, strategy_id, name, start_date, end_date,
                    total_return, max_drawdown, sharpe_ratio, trade_count, win_rate,
                    parameters
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                backtest_id,
                user_id,
                strategy_id,
                name,
                start_date,
                end_date,
                performance_metrics["total_return"],
                performance_metrics["max_drawdown"],
                performance_metrics.get("sharpe_ratio"),
                performance_metrics["trade_count"],
                performance_metrics.get("win_rate"),
                json.dumps(parameters)
            ))
            
            # Store trade history
            for trade in performance_metrics.get("trades", []):
                trade_id = f"trade_{uuid.uuid4().hex[:8]}"
                cursor.execute("""
                    INSERT INTO trade_history (
                        id, backtest_id, entry_time, exit_time, instrument,
                        direction, entry_price, exit_price, quantity,
                        profit_loss, profit_loss_percent, exit_reason
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_id,
                    backtest_id,
                    trade["entry_time"],
                    trade.get("exit_time"),
                    trade["instrument"],
                    trade["direction"],
                    trade["entry_price"],
                    trade.get("exit_price"),
                    trade["quantity"],
                    trade.get("profit_loss"),
                    trade.get("profit_loss_percent"),
                    trade.get("exit_reason")
                ))
            
            return backtest_id
```

### Redis Interaction Pattern

```python
import redis
import json

class RedisRepository:
    def __init__(self, host, port, db):
        self.client = redis.Redis(host=host, port=port, db=db)
    
    def cache_market_data(self, instrument, frequency, data, expiry_seconds=300):
        cache_key = f"market_data:{instrument}:{frequency}:recent"
        self.client.setex(cache_key, expiry_seconds, json.dumps(data))
    
    def get_cached_market_data(self, instrument, frequency):
        cache_key = f"market_data:{instrument}:{frequency}:recent"
        data = self.client.get(cache_key)
        
        if data:
            return json.loads(data)
        return None
    
    def store_user_session(self, session_id, user_data, expiry_seconds=86400):
        cache_key = f"session:{session_id}"
        self.client.setex(cache_key, expiry_seconds, json.dumps(user_data))
    
    def get_user_session(self, session_id):
        cache_key = f"session:{session_id}"
        data = self.client.get(cache_key)
        
        if data:
            return json.loads(data)
        return None
    
    def delete_user_session(self, session_id):
        cache_key = f"session:{session_id}"
        self.client.delete(cache_key)
```

## Database Integration Guidelines

1. **Separation of Concerns**:
   - Use Neo4j for knowledge representation and relationships
   - Use InfluxDB for time-series market data
   - Use SQLite/PostgreSQL for user data and metadata
   - Use Redis for caching and ephemeral data

2. **Data Flow Patterns**:
   - Strategy creation: User input → Neo4j validation → Neo4j storage
   - Backtesting: Neo4j strategy → InfluxDB data → Processing → SQLite results
   - Real-time data: InfluxDB/Redis → WebSocket → Frontend

3. **Transaction Management**:
   - Use explicit transactions for operations that span multiple database operations
   - Implement rollback mechanisms for partial failures
   - Use optimistic locking for concurrent modifications

## Knowledge Graph Integration with Agents

The Neo4j knowledge graph has been fully integrated with the agent system to enable knowledge-driven strategy creation, validation, and visualization.

### Enhanced StrategyRepository

The `StrategyRepository` class has been enhanced with comprehensive methods for querying the knowledge graph:

```python
class StrategyRepository:
    """
    Repository for Neo4j operations supporting knowledge-driven strategy creation.
    Provides methods for component retrieval, relationship validation,
    recommendation algorithms, and template generation.
    """
    
    def __init__(self):
        """Initialize the strategy repository."""
        self.driver = db_manager.neo4j_driver
        
    def get_indicators_for_strategy_type(
        self,
        strategy_type: str,
        min_strength: float = 0.7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get indicators commonly used with a specific strategy type.
        
        Args:
            strategy_type: Type of strategy
            min_strength: Minimum compatibility score
            limit: Maximum number of results to return
            
        Returns:
            List of indicators with compatibility scores
        """
        # Implementation...
        
    def get_position_sizing_for_strategy_type(
        self,
        strategy_type: str,
        min_compatibility: float = 0.7,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get position sizing methods suitable for a specific strategy type.
        
        Args:
            strategy_type: Type of strategy
            min_compatibility: Minimum compatibility score
            limit: Maximum number of results to return
            
        Returns:
            List of position sizing methods with compatibility scores
        """
        # Implementation...
        
    def get_parameters_for_indicator(
        self,
        indicator_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get parameters required for a specific indicator.
        
        Args:
            indicator_name: Name of the indicator
            
        Returns:
            List of parameters with default values
        """
        # Implementation...
        
    def generate_strategy_template(
        self,
        strategy_type: str,
        instrument: str,
        timeframe: str
    ) -> Dict[str, Any]:
        """
        Generate a strategy template based on the knowledge graph.
        
        Args:
            strategy_type: Type of strategy
            instrument: Instrument symbol or type
            timeframe: Timeframe
            
        Returns:
            Strategy template with recommended components
        """
        # Implementation...
```

### Knowledge Integration Module

A `knowledge_integration.py` module provides standardized functions for agents to interact with Neo4j:

```python
def get_knowledge_recommendations(strategy_repository, strategy_type: str) -> Dict[str, Any]:
    """
    Get knowledge-driven recommendations for a strategy type.
    
    Args:
        strategy_repository: Neo4j strategy repository instance
        strategy_type: Type of trading strategy
        
    Returns:
        Dictionary with recommendations
    """
    # Implementation...
    
def enhance_validation_feedback(strategy_repository, errors: List[str], strategy_type: str) -> List[str]:
    """
    Generate knowledge-driven suggestions based on validation errors.
    
    Args:
        strategy_repository: Neo4j strategy repository instance
        errors: List of validation errors
        strategy_type: Strategy type
        
    Returns:
        List of knowledge-driven suggestions
    """
    # Implementation...
    
def enhance_strategy_with_knowledge(strategy_repository, strategy_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance a strategy with knowledge-driven recommendations.
    
    Args:
        strategy_repository: Neo4j strategy repository instance
        strategy_params: Basic strategy parameters
        
    Returns:
        Enhanced strategy parameters
    """
    # Implementation...
```

### Agent Usage

The agents use the knowledge graph to provide better recommendations and validations:

1. **ConversationalAgent**:
   - Enhanced parameter extraction with knowledge-driven recommendations
   - Improved conversations with Neo4j-based suggestions
   - Better template recommendations using compatibility data
   - Enhanced explanations using relationship metadata

2. **ValidationAgent**:
   - Parameter validation using Neo4j recommended ranges
   - Component compatibility checking with relationship data
   - Knowledge-driven suggestions for issues
   - Better error messages with explanation from relationship metadata

This integration enables a truly knowledge-driven approach to strategy creation, where the system can recommend appropriate components based on compatibility and provide meaningful explanations about why certain components work well together.

### Knowledge Graph Visualization

A visualization module has been implemented to provide graphical representations of the knowledge graph:

1. **Component Relationship Diagrams**:
   - Visual representation of how strategy components relate to each other
   - Displays relationship types and strength scores
   - Helps users understand component dependencies and connections

2. **Compatibility Matrices**:
   - Heatmap visualization of compatibility scores between components
   - Helps identify highly compatible component combinations
   - Supports better strategy design decisions

3. **Strategy Template Visualizations**:
   - Hierarchical representation of complete strategy templates
   - Shows all components and their parameter configurations
   - Enables easy understanding of complex strategy structures

The visualization tools enhance user understanding by providing intuitive graphical representations of the knowledge relationships, making it easier to create effective trading strategies.