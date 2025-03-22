// Neo4j Initialization Script for Multi-Agent Trading System V2
// Enhanced Schema for Complete Trading Strategy Knowledge Graph

// Create constraints and indexes
CREATE CONSTRAINT strategy_type_name IF NOT EXISTS FOR (s:StrategyType) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT instrument_symbol IF NOT EXISTS FOR (i:Instrument) REQUIRE i.symbol IS UNIQUE;
CREATE CONSTRAINT indicator_name IF NOT EXISTS FOR (i:Indicator) REQUIRE i.name IS UNIQUE;
CREATE CONSTRAINT strategy_id IF NOT EXISTS FOR (s:Strategy) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT position_sizing_method_name IF NOT EXISTS FOR (p:PositionSizingMethod) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT risk_management_technique_name IF NOT EXISTS FOR (r:RiskManagementTechnique) REQUIRE r.name IS UNIQUE;
CREATE CONSTRAINT stop_type_name IF NOT EXISTS FOR (s:StopType) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT backtest_method_name IF NOT EXISTS FOR (b:BacktestMethod) REQUIRE b.name IS UNIQUE;
CREATE CONSTRAINT trade_management_technique_name IF NOT EXISTS FOR (t:TradeManagementTechnique) REQUIRE t.name IS UNIQUE;
CREATE CONSTRAINT performance_metric_name IF NOT EXISTS FOR (p:PerformanceMetric) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT data_source_type_name IF NOT EXISTS FOR (d:DataSourceType) REQUIRE d.name IS UNIQUE;

CREATE INDEX strategy_user_idx IF NOT EXISTS FOR (s:Strategy) ON (s.user_id);
CREATE INDEX condition_type_idx IF NOT EXISTS FOR (c:Condition) ON (c.type);
CREATE INDEX indicator_category_idx IF NOT EXISTS FOR (i:Indicator) ON (i.category);
CREATE INDEX strategy_type_category_idx IF NOT EXISTS FOR (s:StrategyType) ON (s.category);

// Create basic strategy types
CREATE (s:StrategyType {name: "momentum", description: "Trading strategy based on price momentum", category: "trend", version: 1, suitability: "trending_markets", typical_timeframe: "medium_term"});
CREATE (s:StrategyType {name: "mean_reversion", description: "Trading strategy based on price returning to mean", category: "reversal", version: 1, suitability: "ranging_markets", typical_timeframe: "short_term"});
CREATE (s:StrategyType {name: "trend_following", description: "Trading strategy based on following established trends", category: "trend", version: 1, suitability: "trending_markets", typical_timeframe: "long_term"});
CREATE (s:StrategyType {name: "breakout", description: "Trading strategy based on price breaking through significant levels", category: "volatility", version: 1, suitability: "volatile_markets", typical_timeframe: "short_term"});
CREATE (s:StrategyType {name: "pattern_recognition", description: "Trading strategy based on chart patterns", category: "chart_pattern", version: 1, suitability: "all_markets", typical_timeframe: "medium_term"});

// Create instruments with enhanced properties
CREATE (i:Instrument {symbol: "BTCUSDT", type: "crypto", exchange: "Binance", data_source: "Binance API", min_order_size: 0.001, max_order_size: 100, base_asset: "BTC", quote_asset: "USDT", tick_size: 0.01, trading_hours: "24/7", typical_volatility: "high"});
CREATE (i:Instrument {symbol: "ETHUSDT", type: "crypto", exchange: "Binance", data_source: "Binance API", min_order_size: 0.01, max_order_size: 1000, base_asset: "ETH", quote_asset: "USDT", tick_size: 0.01, trading_hours: "24/7", typical_volatility: "high"});
CREATE (i:Instrument {symbol: "AAPL", type: "stock", exchange: "NASDAQ", data_source: "Yahoo Finance", min_order_size: 1, base_asset: "AAPL", quote_asset: "USD", tick_size: 0.01, trading_hours: "9:30-16:00 EST", typical_volatility: "medium"});
CREATE (i:Instrument {symbol: "EURUSD", type: "forex", exchange: "Forex", data_source: "Alpha Vantage", min_order_size: 0.01, base_asset: "EUR", quote_asset: "USD", tick_size: 0.0001, trading_hours: "24/5", typical_volatility: "low"});

// Create frequencies with enhanced properties
CREATE (f:Frequency {name: "1m", description: "1 minute interval", milliseconds: 60000, typical_noise: "very_high", suitable_for_strategies: ["scalping", "high_frequency"], min_backtest_period: "1 week"});
CREATE (f:Frequency {name: "5m", description: "5 minute interval", milliseconds: 300000, typical_noise: "high", suitable_for_strategies: ["scalping", "intraday"], min_backtest_period: "2 weeks"});
CREATE (f:Frequency {name: "15m", description: "15 minute interval", milliseconds: 900000, typical_noise: "high", suitable_for_strategies: ["intraday"], min_backtest_period: "1 month"});
CREATE (f:Frequency {name: "1h", description: "1 hour interval", milliseconds: 3600000, typical_noise: "medium", suitable_for_strategies: ["intraday", "swing"], min_backtest_period: "3 months"});
CREATE (f:Frequency {name: "4h", description: "4 hour interval", milliseconds: 14400000, typical_noise: "medium", suitable_for_strategies: ["swing"], min_backtest_period: "6 months"});
CREATE (f:Frequency {name: "1d", description: "1 day interval", milliseconds: 86400000, typical_noise: "low", suitable_for_strategies: ["swing", "position"], min_backtest_period: "1 year"});
CREATE (f:Frequency {name: "1w", description: "1 week interval", milliseconds: 604800000, typical_noise: "very_low", suitable_for_strategies: ["position", "trend_following"], min_backtest_period: "3 years"});

// Create position sizing methods
CREATE (p:PositionSizingMethod {name: "fixed", description: "Fixed quantity position sizing", complexity: "low", risk_profile: "variable", suitability: "beginners", version: 1});
CREATE (p:PositionSizingMethod {name: "percent", description: "Percentage of account position sizing", complexity: "low", risk_profile: "moderate", suitability: "all_levels", version: 1});
CREATE (p:PositionSizingMethod {name: "risk_based", description: "Risk percentage per trade position sizing", complexity: "medium", risk_profile: "controlled", suitability: "intermediate", version: 1});
CREATE (p:PositionSizingMethod {name: "volatility", description: "Volatility-adjusted position sizing", complexity: "high", risk_profile: "adaptive", suitability: "advanced", version: 1});
CREATE (p:PositionSizingMethod {name: "kelly", description: "Kelly criterion for optimal position sizing", complexity: "high", risk_profile: "optimal", suitability: "advanced", version: 1});
CREATE (p:PositionSizingMethod {name: "martingale", description: "Increase position size after losses", complexity: "medium", risk_profile: "aggressive", suitability: "high_risk", version: 1});
CREATE (p:PositionSizingMethod {name: "anti_martingale", description: "Increase position size after wins", complexity: "medium", risk_profile: "pyramiding", suitability: "trend_following", version: 1});

// Create risk management techniques
CREATE (r:RiskManagementTechnique {name: "fixed_stop_loss", description: "Fixed price or percentage stop loss", complexity: "low", effectiveness: "moderate", suitability: "all_strategies", version: 1});
CREATE (r:RiskManagementTechnique {name: "trailing_stop", description: "Moving stop based on price action", complexity: "medium", effectiveness: "high", suitability: "trend_following", version: 1});
CREATE (r:RiskManagementTechnique {name: "volatility_stop", description: "Stop based on volatility (e.g., ATR)", complexity: "medium", effectiveness: "high", suitability: "volatile_markets", version: 1});
CREATE (r:RiskManagementTechnique {name: "time_stop", description: "Exit based on time elapsed", complexity: "low", effectiveness: "situational", suitability: "pattern_strategies", version: 1});
CREATE (r:RiskManagementTechnique {name: "indicator_stop", description: "Exit based on indicator value", complexity: "medium", effectiveness: "high", suitability: "technical_strategies", version: 1});
CREATE (r:RiskManagementTechnique {name: "max_positions", description: "Limit on simultaneous positions", complexity: "low", effectiveness: "moderate", suitability: "portfolio_strategies", version: 1});
CREATE (r:RiskManagementTechnique {name: "max_risk_per_trade", description: "Maximum risk percentage per trade", complexity: "low", effectiveness: "high", suitability: "all_strategies", version: 1});
CREATE (r:RiskManagementTechnique {name: "max_risk_total", description: "Maximum total risk percentage", complexity: "medium", effectiveness: "high", suitability: "portfolio_strategies", version: 1});
CREATE (r:RiskManagementTechnique {name: "max_drawdown_exit", description: "Exit all positions on drawdown threshold", complexity: "medium", effectiveness: "protective", suitability: "all_strategies", version: 1});

// Create stop types (subset of risk management techniques)
CREATE (s:StopType {name: "fixed", description: "Fixed price or percentage", complexity: "low", suitability: "all_strategies", version: 1});
CREATE (s:StopType {name: "trailing", description: "Moving stop based on price action", complexity: "medium", suitability: "trend_following", version: 1});
CREATE (s:StopType {name: "volatility", description: "Stop based on volatility (e.g., ATR)", complexity: "medium", suitability: "volatile_markets", version: 1});
CREATE (s:StopType {name: "time", description: "Exit based on time elapsed", complexity: "low", suitability: "pattern_strategies", version: 1});
CREATE (s:StopType {name: "indicator", description: "Exit based on indicator value", complexity: "medium", suitability: "technical_strategies", version: 1});

// Create trade management techniques
CREATE (t:TradeManagementTechnique {name: "partial_exits", description: "Exit positions in parts at different levels", complexity: "medium", effectiveness: "high", suitability: "trend_following", version: 1});
CREATE (t:TradeManagementTechnique {name: "breakeven_stop", description: "Move stop to entry after profit threshold", complexity: "low", effectiveness: "moderate", suitability: "all_strategies", version: 1});
CREATE (t:TradeManagementTechnique {name: "scaled_profit_targets", description: "Multiple profit targets at different levels", complexity: "medium", effectiveness: "high", suitability: "trend_following", version: 1});
CREATE (t:TradeManagementTechnique {name: "time_based_exit", description: "Exit after specified time period", complexity: "low", effectiveness: "situational", suitability: "mean_reversion", version: 1});
CREATE (t:TradeManagementTechnique {name: "pyramiding", description: "Add to winning positions", complexity: "high", effectiveness: "high_potential", suitability: "strong_trends", version: 1});
CREATE (t:TradeManagementTechnique {name: "stop_adjustment", description: "Adjust stop by portion of profit", complexity: "medium", effectiveness: "protective", suitability: "all_strategies", version: 1});
CREATE (t:TradeManagementTechnique {name: "re_entry", description: "Rules for re-entering after exit", complexity: "high", effectiveness: "opportunity", suitability: "volatility_strategies", version: 1});

// Create backtesting methods
CREATE (b:BacktestMethod {name: "simple", description: "Single pass with fixed parameters", complexity: "low", accuracy: "basic", suitable_for: "initial_testing", version: 1});
CREATE (b:BacktestMethod {name: "walk_forward", description: "In-sample/out-of-sample validation", complexity: "medium", accuracy: "high", suitable_for: "robustness_testing", version: 1});
CREATE (b:BacktestMethod {name: "monte_carlo", description: "Multiple simulations with random variations", complexity: "high", accuracy: "probabilistic", suitable_for: "risk_assessment", version: 1});
CREATE (b:BacktestMethod {name: "optimization", description: "Parameter optimization", complexity: "high", accuracy: "parameter_specific", suitable_for: "fine_tuning", version: 1});
CREATE (b:BacktestMethod {name: "cross_validation", description: "K-fold cross validation", complexity: "high", accuracy: "highest", suitable_for: "final_validation", version: 1});

// Create performance metrics
CREATE (p:PerformanceMetric {name: "total_return", description: "Absolute return over the period", importance: "high", category: "returns", interpretation: "higher_better", version: 1});
CREATE (p:PerformanceMetric {name: "sharpe_ratio", description: "Return per unit of risk", importance: "very_high", category: "risk_adjusted", interpretation: "higher_better", version: 1});
CREATE (p:PerformanceMetric {name: "sortino_ratio", description: "Return per unit of downside risk", importance: "high", category: "risk_adjusted", interpretation: "higher_better", version: 1});
CREATE (p:PerformanceMetric {name: "max_drawdown", description: "Maximum peak to trough decline", importance: "very_high", category: "risk", interpretation: "lower_better", version: 1});
CREATE (p:PerformanceMetric {name: "win_rate", description: "Percentage of winning trades", importance: "medium", category: "trading", interpretation: "context_dependent", version: 1});
CREATE (p:PerformanceMetric {name: "profit_factor", description: "Gross profit / gross loss", importance: "high", category: "trading", interpretation: "higher_better", version: 1});
CREATE (p:PerformanceMetric {name: "calmar_ratio", description: "Return / max drawdown", importance: "high", category: "risk_adjusted", interpretation: "higher_better", version: 1});
CREATE (p:PerformanceMetric {name: "expectancy", description: "Average profit/loss per trade", importance: "high", category: "trading", interpretation: "higher_better", version: 1});
CREATE (p:PerformanceMetric {name: "recovery_factor", description: "Return / max drawdown", importance: "medium", category: "recovery", interpretation: "higher_better", version: 1});
CREATE (p:PerformanceMetric {name: "ulcer_index", description: "Measures drawdown depth and duration", importance: "medium", category: "risk", interpretation: "lower_better", version: 1});
CREATE (p:PerformanceMetric {name: "gain_to_pain_ratio", description: "Sum of returns / sum of absolute drawdowns", importance: "medium", category: "risk_adjusted", interpretation: "higher_better", version: 1});

// Create data source types
CREATE (d:DataSourceType {name: "influxdb", description: "Internal InfluxDB (primary cache)", reliability: "very_high", latency: "very_low", cost: "none", version: 1});
CREATE (d:DataSourceType {name: "binance", description: "Binance cryptocurrency exchange API", reliability: "high", latency: "low", cost: "free_with_limits", crypto_only: true, version: 1});
CREATE (d:DataSourceType {name: "yahoo", description: "Yahoo Finance API", reliability: "medium", latency: "medium", cost: "free", version: 1});
CREATE (d:DataSourceType {name: "alpha_vantage", description: "Alpha Vantage API", reliability: "high", latency: "medium", cost: "freemium", version: 1});
CREATE (d:DataSourceType {name: "csv", description: "CSV file data source", reliability: "variable", latency: "very_low", cost: "none", local_only: true, version: 1});
CREATE (d:DataSourceType {name: "custom", description: "Custom data source", reliability: "variable", latency: "variable", cost: "variable", version: 1});

// Create indicators with enhanced properties - using string representation for parameters instead of maps
CREATE (i:Indicator {name: "RSI", description: "Relative Strength Index", category: "momentum", version: 1, complexity: "medium", calculation_speed: "fast", typical_parameter_period: 14, interpretation: "Measures the speed and change of price movements. Above 70 is considered overbought, below 30 is considered oversold."});
CREATE (i:Indicator {name: "EMA", description: "Exponential Moving Average", category: "trend", version: 1, complexity: "low", calculation_speed: "very_fast", typical_parameter_period: 20, interpretation: "Assigns more weight to recent prices. Moving above/below price can signal trend changes."});
CREATE (i:Indicator {name: "SMA", description: "Simple Moving Average", category: "trend", version: 1, complexity: "low", calculation_speed: "very_fast", typical_parameter_period: 50, interpretation: "Average price over a specific period. Moving above/below can signal trend changes."});
CREATE (i:Indicator {name: "MACD", description: "Moving Average Convergence Divergence", category: "momentum", version: 1, complexity: "medium", calculation_speed: "fast", typical_parameter_fast_period: 12, typical_parameter_slow_period: 26, typical_parameter_signal_period: 9, interpretation: "Shows relationship between two moving averages. Crossovers and divergence can signal trend changes."});
CREATE (i:Indicator {name: "Bollinger Bands", description: "Volatility bands placed above and below moving average", category: "volatility", version: 1, complexity: "medium", calculation_speed: "medium", typical_parameter_period: 20, typical_parameter_std_dev: 2, interpretation: "Measures volatility. Price approaching upper band may indicate overbought, lower band may indicate oversold."});
CREATE (i:Indicator {name: "ATR", description: "Average True Range", category: "volatility", version: 1, complexity: "medium", calculation_speed: "fast", typical_parameter_period: 14, interpretation: "Measures market volatility. Higher values indicate higher volatility, often used for position sizing."});
CREATE (i:Indicator {name: "Stochastic", description: "Stochastic Oscillator", category: "momentum", version: 1, complexity: "medium", calculation_speed: "medium", typical_parameter_k_period: 14, typical_parameter_d_period: 3, interpretation: "Compares closing price to price range. Above 80 is considered overbought, below 20 is considered oversold."});
CREATE (i:Indicator {name: "Fibonacci Retracement", description: "Key Fibonacci levels for potential support/resistance", category: "pattern", version: 1, complexity: "medium", calculation_speed: "medium", typical_parameter_levels: "[0.236, 0.382, 0.5, 0.618, 0.786]", interpretation: "Potential support/resistance levels based on Fibonacci ratios, often used to identify reversal points."});
CREATE (i:Indicator {name: "Volume Profile", description: "Distribution of volume across price levels", category: "volume", version: 1, complexity: "high", calculation_speed: "slow", typical_parameter_period: 30, interpretation: "Shows price levels with highest trading activity, which may act as support/resistance."});

// Create parameters (more comprehensive)
CREATE (p:Parameter {name: "period", default_value: 14, min_value: 2, max_value: 200, type: "integer", description: "Number of periods to calculate indicator"});
CREATE (p:Parameter {name: "fast_period", default_value: 12, min_value: 2, max_value: 50, type: "integer", description: "Number of periods for fast moving average"});
CREATE (p:Parameter {name: "slow_period", default_value: 26, min_value: 5, max_value: 200, type: "integer", description: "Number of periods for slow moving average"});
CREATE (p:Parameter {name: "signal_period", default_value: 9, min_value: 2, max_value: 50, type: "integer", description: "Number of periods for signal line"});
CREATE (p:Parameter {name: "k_period", default_value: 14, min_value: 3, max_value: 50, type: "integer", description: "Number of periods for %K line"});
CREATE (p:Parameter {name: "d_period", default_value: 3, min_value: 1, max_value: 30, type: "integer", description: "Number of periods for %D line"});
CREATE (p:Parameter {name: "std_dev", default_value: 2, min_value: 0.5, max_value: 5, type: "float", description: "Number of standard deviations for bands"});
CREATE (p:Parameter {name: "lookback", default_value: 50, min_value: 10, max_value: 500, type: "integer", description: "Lookback period for historical comparison"});
CREATE (p:Parameter {name: "threshold", default_value: 30, min_value: 5, max_value: 50, type: "integer", description: "Threshold value for indicator"});
CREATE (p:Parameter {name: "risk_percentage", default_value: 1, min_value: 0.1, max_value: 10, type: "float", description: "Percentage of account to risk per trade"});
CREATE (p:Parameter {name: "profit_target", default_value: 2, min_value: 0.5, max_value: 10, type: "float", description: "Profit target as ratio of risk"});
CREATE (p:Parameter {name: "trailing_percentage", default_value: 1, min_value: 0.1, max_value: 10, type: "float", description: "Percentage for trailing stop"});

// Create conditions (more comprehensive)
CREATE (c:Condition {logic: "RSI < 30", type: "entry", direction: "long", description: "Enter long when RSI is below 30", priority: 1});
CREATE (c:Condition {logic: "RSI > 70", type: "exit", direction: "long", description: "Exit long when RSI is above 70", priority: 1});
CREATE (c:Condition {logic: "EMA(50) > EMA(200)", type: "filter", direction: "long", description: "Only allow long trades when 50 EMA is above 200 EMA", priority: 2});
CREATE (c:Condition {logic: "price > EMA(20)", type: "entry", direction: "long", description: "Enter long when price crosses above 20 EMA", priority: 1});
CREATE (c:Condition {logic: "price < EMA(20)", type: "entry", direction: "short", description: "Enter short when price crosses below 20 EMA", priority: 1});
CREATE (c:Condition {logic: "MACD > Signal", type: "entry", direction: "long", description: "Enter long when MACD crosses above signal line", priority: 1});
CREATE (c:Condition {logic: "MACD < Signal", type: "entry", direction: "short", description: "Enter short when MACD crosses below signal line", priority: 1});
CREATE (c:Condition {logic: "ATR(14) > threshold", type: "filter", direction: "both", description: "Only trade when volatility (ATR) is above threshold", priority: 2});

// Create relationships between strategy types and indicators with compatibility scores
MATCH (s:StrategyType {name: "momentum"}), (i:Indicator {name: "RSI"})
CREATE (s)-[:COMMONLY_USES {strength: 0.9, explanation: "RSI effectively identifies overbought/oversold conditions for momentum strategies"}]->(i);

MATCH (s:StrategyType {name: "trend_following"}), (i:Indicator {name: "EMA"})
CREATE (s)-[:COMMONLY_USES {strength: 0.9, explanation: "EMAs help identify and follow trends, essential for trend following strategies"}]->(i);

MATCH (s:StrategyType {name: "mean_reversion"}), (i:Indicator {name: "Bollinger Bands"})
CREATE (s)-[:COMMONLY_USES {strength: 0.9, explanation: "Bollinger Bands help identify price extremes for mean reversion"}]->(i);

MATCH (s:StrategyType {name: "breakout"}), (i:Indicator {name: "ATR"})
CREATE (s)-[:COMMONLY_USES {strength: 0.8, explanation: "ATR helps size positions based on volatility, important for breakout strategies"}]->(i);

// Create relationships between indicators and parameters with compatibility scores
MATCH (i:Indicator {name: "RSI"}), (p:Parameter {name: "period"})
CREATE (i)-[:HAS_PARAMETER {is_required: true, default_value: 14, explanation: "Standard period for RSI calculation"}]->(p);

MATCH (i:Indicator {name: "EMA"}), (p:Parameter {name: "period"})
CREATE (i)-[:HAS_PARAMETER {is_required: true, default_value: 20, explanation: "Common period for EMA calculation"}]->(p);

MATCH (i:Indicator {name: "MACD"}), (p:Parameter {name: "fast_period"})
CREATE (i)-[:HAS_PARAMETER {is_required: true, default_value: 12, explanation: "Standard fast period for MACD"}]->(p);

MATCH (i:Indicator {name: "MACD"}), (p:Parameter {name: "slow_period"})
CREATE (i)-[:HAS_PARAMETER {is_required: true, default_value: 26, explanation: "Standard slow period for MACD"}]->(p);

MATCH (i:Indicator {name: "MACD"}), (p:Parameter {name: "signal_period"})
CREATE (i)-[:HAS_PARAMETER {is_required: true, default_value: 9, explanation: "Standard signal period for MACD"}]->(p);

// Create relationships between strategy types and position sizing methods
MATCH (s:StrategyType {name: "trend_following"}), (p:PositionSizingMethod {name: "volatility"})
CREATE (s)-[:SUITABLE_SIZING {compatibility: 0.9, explanation: "Volatility-based sizing works well with trend following as it adjusts for market conditions"}]->(p);

MATCH (s:StrategyType {name: "momentum"}), (p:PositionSizingMethod {name: "risk_based"})
CREATE (s)-[:SUITABLE_SIZING {compatibility: 0.8, explanation: "Risk-based sizing is optimal for momentum strategies to control exposure"}]->(p);

MATCH (s:StrategyType {name: "mean_reversion"}), (p:PositionSizingMethod {name: "percent"})
CREATE (s)-[:SUITABLE_SIZING {compatibility: 0.7, explanation: "Percentage sizing works well with mean reversion for consistent exposure"}]->(p);

// Create relationships between strategy types and risk management techniques
MATCH (s:StrategyType {name: "trend_following"}), (r:RiskManagementTechnique {name: "trailing_stop"})
CREATE (s)-[:SUITABLE_RISK_MANAGEMENT {compatibility: 0.9, explanation: "Trailing stops maximize profit in trending markets while protecting capital"}]->(r);

MATCH (s:StrategyType {name: "momentum"}), (r:RiskManagementTechnique {name: "fixed_stop_loss"})
CREATE (s)-[:SUITABLE_RISK_MANAGEMENT {compatibility: 0.8, explanation: "Fixed stops provide clear exit points for momentum strategies"}]->(r);

MATCH (s:StrategyType {name: "breakout"}), (r:RiskManagementTechnique {name: "volatility_stop"})
CREATE (s)-[:SUITABLE_RISK_MANAGEMENT {compatibility: 0.9, explanation: "Volatility stops adjust to market conditions, ideal for breakout strategies"}]->(r);

// Create relationships between strategy types and trade management techniques
MATCH (s:StrategyType {name: "trend_following"}), (t:TradeManagementTechnique {name: "partial_exits"})
CREATE (s)-[:SUITABLE_TRADE_MANAGEMENT {compatibility: 0.9, explanation: "Partial exits allow locking in profit while letting winners run"}]->(t);

MATCH (s:StrategyType {name: "momentum"}), (t:TradeManagementTechnique {name: "breakeven_stop"})
CREATE (s)-[:SUITABLE_TRADE_MANAGEMENT {compatibility: 0.8, explanation: "Moving to breakeven protects capital after initial momentum move"}]->(t);

MATCH (s:StrategyType {name: "breakout"}), (t:TradeManagementTechnique {name: "pyramiding"})
CREATE (s)-[:SUITABLE_TRADE_MANAGEMENT {compatibility: 0.8, explanation: "Adding to winning positions works well with strong breakout moves"}]->(t);

// Create relationships between strategy types and backtest methods
MATCH (s:StrategyType {name: "trend_following"}), (b:BacktestMethod {name: "walk_forward"})
CREATE (s)-[:SUITABLE_BACKTESTING {compatibility: 0.9, explanation: "Walk-forward testing helps confirm trend following robustness across periods"}]->(b);

MATCH (s:StrategyType {name: "mean_reversion"}), (b:BacktestMethod {name: "monte_carlo"})
CREATE (s)-[:SUITABLE_BACKTESTING {compatibility: 0.8, explanation: "Monte Carlo simulation helps understand probability distribution of returns"}]->(b);

MATCH (s:StrategyType {name: "momentum"}), (b:BacktestMethod {name: "optimization"})
CREATE (s)-[:SUITABLE_BACKTESTING {compatibility: 0.7, explanation: "Parameter optimization helps find ideal settings for momentum indicators"}]->(b);

// Create relationships between strategy types and performance metrics
MATCH (s:StrategyType {name: "trend_following"}), (p:PerformanceMetric {name: "profit_factor"})
CREATE (s)-[:SUITABLE_METRIC {compatibility: 0.9, explanation: "Profit factor is important for trend following as it needs high win:loss ratio"}]->(p);

MATCH (s:StrategyType {name: "mean_reversion"}), (p:PerformanceMetric {name: "win_rate"})
CREATE (s)-[:SUITABLE_METRIC {compatibility: 0.8, explanation: "Win rate is critical for mean reversion strategies which typically have higher win rates"}]->(p);

MATCH (s:StrategyType {name: "breakout"}), (p:PerformanceMetric {name: "expectancy"})
CREATE (s)-[:SUITABLE_METRIC {compatibility: 0.9, explanation: "Expectancy captures the balance of win rate and win:loss ratio important for breakouts"}]->(p);

// Create relationships between instruments and frequencies
MATCH (i:Instrument {symbol: "BTCUSDT"}), (f:Frequency {name: "1h"})
CREATE (i)-[:SUITABLE_FOR {compatibility: 0.9, liquidity: "high", explanation: "BTC has high liquidity at 1h timeframe"}]->(f);

MATCH (i:Instrument {symbol: "BTCUSDT"}), (f:Frequency {name: "4h"})
CREATE (i)-[:SUITABLE_FOR {compatibility: 0.9, liquidity: "high", explanation: "BTC has excellent liquidity at 4h timeframe"}]->(f);

MATCH (i:Instrument {symbol: "BTCUSDT"}), (f:Frequency {name: "1d"})
CREATE (i)-[:SUITABLE_FOR {compatibility: 0.9, liquidity: "high", explanation: "BTC has excellent liquidity at daily timeframe"}]->(f);

MATCH (i:Instrument {symbol: "AAPL"}), (f:Frequency {name: "1d"})
CREATE (i)-[:SUITABLE_FOR {compatibility: 0.9, liquidity: "high", explanation: "AAPL has excellent liquidity at daily timeframe"}]->(f);

// Create relationships between instruments and data sources
MATCH (i:Instrument {symbol: "BTCUSDT"}), (d:DataSourceType {name: "binance"})
CREATE (i)-[:AVAILABLE_FROM {quality: "high", history_length: "complete", explanation: "Binance provides complete history for BTCUSDT"}]->(d);

MATCH (i:Instrument {symbol: "AAPL"}), (d:DataSourceType {name: "yahoo"})
CREATE (i)-[:AVAILABLE_FROM {quality: "high", history_length: "long", explanation: "Yahoo provides long-term history for AAPL"}]->(d);

MATCH (i:Instrument {symbol: "AAPL"}), (d:DataSourceType {name: "alpha_vantage"})
CREATE (i)-[:AVAILABLE_FROM {quality: "high", history_length: "medium", explanation: "Alpha Vantage provides good quality data for AAPL"}]->(d);

// Create compatibility relationships between different components
// Position sizing and risk management compatibility
MATCH (p:PositionSizingMethod {name: "risk_based"}), (r:RiskManagementTechnique {name: "fixed_stop_loss"})
CREATE (p)-[:COMPATIBLE_WITH {strength: 0.9, explanation: "Risk-based sizing works perfectly with fixed stops for consistent risk exposure"}]->(r);

MATCH (p:PositionSizingMethod {name: "volatility"}), (r:RiskManagementTechnique {name: "volatility_stop"})
CREATE (p)-[:COMPATIBLE_WITH {strength: 0.9, explanation: "Volatility-based sizing and stops form a consistent approach to market conditions"}]->(r);

// Risk management and trade management compatibility
MATCH (r:RiskManagementTechnique {name: "trailing_stop"}), (t:TradeManagementTechnique {name: "partial_exits"})
CREATE (r)-[:COMPATIBLE_WITH {strength: 0.9, explanation: "Trailing stops work well with partial exits to lock in profits and maximize returns"}]->(t);

MATCH (r:RiskManagementTechnique {name: "fixed_stop_loss"}), (t:TradeManagementTechnique {name: "breakeven_stop"})
CREATE (r)-[:COMPATIBLE_WITH {strength: 0.8, explanation: "Starting with fixed stops and moving to breakeven creates balanced risk approach"}]->(t);

// Indicator compatibility for combined signals
MATCH (i1:Indicator {name: "RSI"}), (i2:Indicator {name: "MACD"})
CREATE (i1)-[:COMPLEMENTS {strength: 0.8, explanation: "RSI and MACD together provide confirmation from different calculation approaches"}]->(i2);

MATCH (i1:Indicator {name: "EMA"}), (i2:Indicator {name: "ATR"})
CREATE (i1)-[:COMPLEMENTS {strength: 0.7, explanation: "EMA for trend direction pairs well with ATR for volatility assessment"}]->(i2);

// Create strategy templates
CREATE (t:StrategyTemplate {
    name: "Simple Trend Following",
    description: "Basic trend following strategy using moving averages",
    strategy_type: "trend_following",
    complexity: "low",
    suitable_instruments: ["stocks", "forex", "crypto"],
    suitable_timeframes: ["1h", "4h", "1d"],
    component_indicators: ["EMA", "ATR"],
    component_entry_conditions: ["Price crosses above EMA"],
    component_exit_conditions: ["Price crosses below EMA", "Fixed profit target", "ATR-based stop loss"],
    component_position_sizing: "risk_based",
    component_risk_management: "volatility_stop",
    version: 1
});

CREATE (t:StrategyTemplate {
    name: "RSI Mean Reversion",
    description: "Mean reversion strategy using RSI oscillator",
    strategy_type: "mean_reversion",
    complexity: "medium",
    suitable_instruments: ["stocks", "forex", "crypto"],
    suitable_timeframes: ["1h", "4h", "1d"],
    component_indicators: ["RSI", "SMA"],
    component_entry_conditions: ["RSI below 30 for longs", "RSI above 70 for shorts", "Price within 5% of SMA"],
    component_exit_conditions: ["RSI crosses back above 50 for longs", "RSI crosses back below 50 for shorts", "Fixed stop loss"],
    component_position_sizing: "percent",
    component_risk_management: "fixed_stop_loss",
    version: 1
});

CREATE (t:StrategyTemplate {
    name: "MACD Momentum",
    description: "Momentum strategy using MACD crossovers",
    strategy_type: "momentum",
    complexity: "medium",
    suitable_instruments: ["stocks", "forex", "crypto"],
    suitable_timeframes: ["1h", "4h", "1d"],
    component_indicators: ["MACD", "EMA"],
    component_entry_conditions: ["MACD crosses above signal line", "Price above 200 EMA for longs"],
    component_exit_conditions: ["MACD crosses below signal line", "Trailing stop"],
    component_position_sizing: "risk_based",
    component_risk_management: "trailing_stop",
    version: 1
});

// Connect templates to their strategy types
MATCH (t:StrategyTemplate {name: "Simple Trend Following"}), (s:StrategyType {name: "trend_following"})
CREATE (t)-[:BASED_ON]->(s);

MATCH (t:StrategyTemplate {name: "RSI Mean Reversion"}), (s:StrategyType {name: "mean_reversion"})
CREATE (t)-[:BASED_ON]->(s);

MATCH (t:StrategyTemplate {name: "MACD Momentum"}), (s:StrategyType {name: "momentum"})
CREATE (t)-[:BASED_ON]->(s);