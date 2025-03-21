# Enhanced Strategy Model Documentation

## Overview

The strategy model has been enhanced to include all components necessary for a complete trading strategy, from basic information to advanced backtesting configurations and performance metrics. This document provides an overview of the model structure and components.

## Core Strategy Components

### Basic Information
- **name**: Strategy name (3-100 characters)
- **description**: Description of the strategy
- **strategy_type**: Type of strategy (momentum, mean_reversion, etc.)
- **instrument**: Trading instrument (e.g., BTCUSDT)
- **frequency**: Trading timeframe (e.g., 1h, 4h, 1d)
- **tags**: List of tags for categorization
- **version**: Version number of the strategy
- **source**: Source of the strategy (manual, template, etc.)

### Technical Components
- **indicators**: List of technical indicators
  - name, description, parameters
  - plot_type (line, histogram, band)
  - overlay (whether indicator overlays on price chart)
  - source_data (close, open, high, low, volume)
  
- **conditions**: List of entry, exit, and filter conditions
  - type (entry, exit, filter)
  - logic (conditional expression)
  - direction (long, short, both)
  - priority (higher number = higher priority)
  - requires_indicators (dependencies)

## Risk and Position Management

### Position Sizing
- **method**: Different methods (fixed, percent, risk_based, volatility, kelly)
- **value**: Size value (percentage, fixed amount, risk percentage)
- **max_position_size**: Maximum position size
- **scaling**: Whether to scale in/out of positions
- **scaling_steps**: Number of scaling steps
- **scaling_factor**: Factor for each step

### Risk Management
- **stop_loss**: Stop loss percentage or price
- **take_profit**: Take profit percentage or price
- **max_positions**: Maximum number of concurrent positions
- **max_risk_per_trade**: Maximum risk per trade
- **max_risk_total**: Maximum total risk
- **stop_type**: Type of stop (fixed, trailing, volatility, time, indicator)
- **trailing_distance**: Distance for trailing stops
- **volatility_multiplier**: Multiplier for volatility-based stops

### Trade Management
- **partial_exits**: List of partial exit thresholds and sizes
- **breakeven_threshold**: When to move stop to breakeven
- **stop_adjustment_ratio**: How to adjust stops
- **pyramiding**: Whether to add to winning positions
- **pyramiding_max_additions**: Maximum number of additions
- **pyramiding_threshold**: Profit threshold for adding

## Testing and Performance

### Backtesting Configuration
- **method**: Backtesting method (simple, walk_forward, monte_carlo, optimization)
- **initial_capital**: Starting capital
- **commission**: Commission percentage
- **slippage**: Slippage percentage
- **walk_forward**: Walk-forward configuration
  - in_sample_size, out_sample_size, windows
- **optimization**: Optimization configuration
  - parameters, iterations, metric, method
- **monte_carlo**: Monte Carlo configuration
  - simulations, capital_variations, shuffle_trades

### Performance Configuration
- **primary_metric**: Primary performance metric (sharpe_ratio, total_return, etc.)
- **benchmark**: Benchmark symbol for comparison
- **risk_free_rate**: Risk-free rate for Sharpe/Sortino calculation
- **required_metrics**: List of metrics to calculate
- **minimum_trades**: Minimum trades for reliable statistics

## Validation and Metadata

- **validation_methods**: The strategy includes multiple validation methods
  - `is_valid()`: Checks if strategy has entry conditions, indicators, and risk management
  - Model validators for component compatibility
  - Field validators for specific data types and formats
  
- **metadata**:
  - compatibility_score: Neo4j-based component compatibility score
  - knowledge_source: Source of knowledge for strategy components

## Model Relationships

The strategy model uses a hierarchical structure with these key relationships:

1. StrategyBase contains:
   - List of Indicator objects
   - List of Condition objects
   - PositionSizing object
   - RiskManagement object
   - TradeManagement object
   - BacktestingConfig object
   - PerformanceConfig object

2. BacktestResult contains:
   - BacktestPerformance object
   - List of TradeRecord objects

## Usage Examples

### Basic Strategy

```python
strategy = StrategyBase(
    name="Simple Moving Average Crossover",
    strategy_type="trend_following",
    instrument="BTCUSDT",
    frequency="1h",
    indicators=[
        Indicator(name="SMA", parameters={"period": 50}),
        Indicator(name="SMA", parameters={"period": 200})
    ],
    conditions=[
        Condition(
            type=ConditionType.ENTRY, 
            logic="SMA_50 crosses above SMA_200",
            direction="long"
        )
    ],
    risk_management=RiskManagement(
        stop_loss=0.02,
        take_profit=0.06
    )
)
```

### Comprehensive Strategy

```python
strategy = StrategyBase(
    name="Advanced Mean Reversion",
    description="Bollinger Band + RSI mean reversion strategy",
    strategy_type="mean_reversion",
    instrument="ETHUSDT",
    frequency="4h",
    indicators=[
        Indicator(name="Bollinger Bands", parameters={"period": 20, "std_dev": 2}),
        Indicator(name="RSI", parameters={"period": 14})
    ],
    conditions=[
        Condition(type=ConditionType.ENTRY, logic="close < lower_band and RSI < 30"),
        Condition(type=ConditionType.EXIT, logic="close > middle_band or RSI > 70")
    ],
    position_sizing=PositionSizing(
        method=PositionSizingMethod.RISK_BASED,
        value=0.01  # 1% risk per trade
    ),
    risk_management=RiskManagement(
        stop_loss=0.02,
        take_profit=0.06,
        stop_type=StopType.TRAILING,
        trailing_distance=0.01
    ),
    trade_management=TradeManagement(
        partial_exits=[
            PartialExit(threshold=0.02, size=0.5)
        ]
    ),
    backtesting=BacktestingConfig(
        method=BacktestMethod.WALK_FORWARD,
        walk_forward=WalkForwardConfig(
            in_sample_size="6M",
            out_sample_size="2M",
            windows=3
        )
    )
)
```