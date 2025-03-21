# Neo4j Knowledge Graph Enhancement Plan

## Current Schema
The current Neo4j schema includes:
- StrategyType nodes (momentum, mean_reversion, etc.)
- Instrument nodes (BTCUSDT, ETHUSDT)
- Frequency nodes (1h, 4h, 1d)
- Indicator nodes (RSI, EMA, MACD)
- Parameter nodes (period, fast_period, slow_period)
- Condition nodes (entry/exit logic)
- Basic relationships (COMMONLY_USES, HAS_PARAMETER, APPROVED_FOR)

## Enhanced Schema Design

### New Node Types

#### 1. Position Sizing Methods
```cypher
CREATE (ps:PositionSizingMethod {name: "fixed", description: "Fixed position size", version: 1});
CREATE (ps:PositionSizingMethod {name: "percent", description: "Percentage of account balance", version: 1});
CREATE (ps:PositionSizingMethod {name: "risk_based", description: "Size based on risk percentage per trade", version: 1});
CREATE (ps:PositionSizingMethod {name: "kelly", description: "Kelly criterion for optimal sizing", version: 1});
```

#### 2. Risk Management
```cypher
CREATE (rm:RiskManagementType {name: "fixed_stop", description: "Fixed price/percentage stop loss", version: 1});
CREATE (rm:RiskManagementType {name: "trailing_stop", description: "Moving stop loss based on price action", version: 1});
CREATE (rm:RiskManagementType {name: "volatility_stop", description: "Stop based on asset volatility (e.g., ATR)", version: 1});
CREATE (rm:RiskManagementType {name: "time_stop", description: "Exit based on time elapsed", version: 1});
```

#### 3. Backtesting Methods
```cypher
CREATE (bt:BacktestMethod {name: "simple", description: "Single pass with fixed parameters", version: 1});
CREATE (bt:BacktestMethod {name: "walk_forward", description: "In-sample/out-of-sample validation", version: 1});
CREATE (bt:BacktestMethod {name: "monte_carlo", description: "Multiple simulations with random variations", version: 1});
CREATE (bt:BacktestMethod {name: "cross_validation", description: "K-fold cross validation approach", version: 1});
```

#### 4. Trade Management
```cypher
CREATE (tm:TradeManagementType {name: "single_exit", description: "Single exit for entire position", version: 1});
CREATE (tm:TradeManagementType {name: "partial_exits", description: "Multiple exits for portions of position", version: 1});
CREATE (tm:TradeManagementType {name: "scaled_entry", description: "Multiple entries to build position", version: 1});
CREATE (tm:TradeManagementType {name: "breakeven_move", description: "Move stop to entry after profit threshold", version: 1});
```

#### 5. Performance Metrics
```cypher
CREATE (pm:PerformanceMetric {name: "total_return", description: "Overall percentage return", version: 1});
CREATE (pm:PerformanceMetric {name: "sharpe_ratio", description: "Return relative to risk", version: 1});
CREATE (pm:PerformanceMetric {name: "max_drawdown", description: "Maximum peak-to-trough decline", version: 1});
CREATE (pm:PerformanceMetric {name: "win_rate", description: "Percentage of profitable trades", version: 1});
CREATE (pm:PerformanceMetric {name: "profit_factor", description: "Gross profit divided by gross loss", version: 1});
```

### New Relationships

#### 1. Strategy Type Relationships
```cypher
// Connect strategy types with appropriate position sizing
MATCH (s:StrategyType {name: "momentum"}), (ps:PositionSizingMethod {name: "risk_based"})
CREATE (s)-[:RECOMMENDS {strength: 0.8, reason: "Momentum strategies benefit from risk-based sizing due to variable win rates"}]->(ps);

// Connect strategy types with trade management approaches
MATCH (s:StrategyType {name: "trend_following"}), (tm:TradeManagementType {name: "trailing_stop"})
CREATE (s)-[:RECOMMENDS {strength: 0.9, reason: "Trend following strategies should use trailing stops to maximize profits"}]->(tm);

// Connect strategy types with backtesting methods
MATCH (s:StrategyType {name: "mean_reversion"}), (bt:BacktestMethod {name: "walk_forward"})
CREATE (s)-[:RECOMMENDED_TESTING {strength: 0.7, reason: "Mean reversion strategies need robust validation due to regime changes"}]->(bt);
```

#### 2. Compatibility Relationships
```cypher
// Connect indicators with appropriate risk management
MATCH (i:Indicator {name: "ATR"}), (rm:RiskManagementType {name: "volatility_stop"})
CREATE (i)-[:ENABLES {strength: 0.9}]->(rm);

// Connect instruments with appropriate position sizing
MATCH (ins:Instrument {symbol: "BTCUSDT"}), (ps:PositionSizingMethod {name: "risk_based"})
CREATE (ins)-[:WORKS_WELL_WITH {strength: 0.8, reason: "High volatility requires careful risk management"}]->(ps);
```

#### 3. Performance Optimization
```cypher
// Connect strategy types with performance metrics to prioritize
MATCH (s:StrategyType {name: "momentum"}), (pm:PerformanceMetric {name: "sharpe_ratio"})
CREATE (s)-[:PRIORITIZES {strength: 0.7, reason: "Momentum strategies should focus on risk-adjusted returns"}]->(pm);
```

## Repository Methods

The enhanced StrategyRepository should include:

1. **Component Retrieval Methods**
   - `get_recommended_indicators(strategy_type, strength_threshold=0.5)`
   - `get_compatible_position_sizing(strategy_type, instrument)`
   - `get_recommended_risk_management(strategy_type, indicators)`
   - `get_appropriate_backtesting_method(strategy_type)`

2. **Compatibility Checking Methods**
   - `check_component_compatibility(component1, component2)`
   - `get_compatibility_score(component_list)`
   - `find_incompatible_components(strategy_dict)`

3. **Template Generation Methods**
   - `generate_strategy_template(strategy_type, instrument, frequency)`
   - `get_default_parameters(strategy_type, indicator)`
   - `get_recommended_components(strategy_type)`

4. **Strategy Improvement Methods**
   - `suggest_improvements(strategy_dict)`
   - `find_alternative_components(component, compatibility_threshold=0.7)`
   - `optimize_parameter_ranges(strategy_type, indicator, parameter)`

## Integration with Agents

### ConversationalAgent Integration
1. The ConversationalAgent will use the StrategyRepository to:
   - Generate initial strategy templates based on user preferences
   - Suggest appropriate indicators and parameters from the knowledge graph
   - Guide component selection based on compatibility relationships
   - Offer intelligent defaults during the conversation flow

### ValidationAgent Integration
1. The ValidationAgent will use the StrategyRepository to:
   - Validate parameters against ranges stored in Neo4j
   - Check component compatibility using relationship data
   - Generate suggestions based on knowledge graph alternatives
   - Provide explanation context based on relationship metadata

## Implementation Phases

### Phase 1: Schema Enhancement
- Update Neo4j schema with new node types
- Add relationship data with compatibility scores
- Create indexes for efficient querying

### Phase 2: Repository Implementation
- Create basic retrieval methods
- Implement compatibility checking
- Add template generation capabilities

### Phase 3: Agent Integration
- Update ConversationalAgent to use Neo4j for strategy construction
- Enhance ValidationAgent with knowledge-based validation
- Create fallback mechanisms for database unavailability

### Phase 4: Advanced Features
- Add strategy templates system
- Implement automated improvement suggestions
- Create component recommendation engine