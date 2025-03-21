import pytest
from datetime import datetime, timedelta
from src.models.strategy import (
    Strategy, StrategyBase, Indicator, Condition, PositionSizing, RiskManagement,
    TradeManagement, BacktestingConfig, PerformanceConfig, ConditionType,
    PositionSizingMethod, StopType, BacktestMethod, PerformanceMetric,
    PartialExit, WalkForwardConfig
)


def test_basic_strategy_creation():
    """Test creating a basic strategy with minimal components."""
    strategy = StrategyBase(
        name="Test Strategy",
        strategy_type="momentum",
        instrument="BTCUSDT",
        frequency="1h",
        indicators=[
            Indicator(name="RSI", parameters={"period": 14})
        ],
        conditions=[
            Condition(type=ConditionType.ENTRY, logic="RSI < 30")
        ],
        risk_management=RiskManagement(
            stop_loss=0.05,
            take_profit=0.15
        )
    )
    
    assert strategy.name == "Test Strategy"
    assert strategy.strategy_type == "momentum"
    assert strategy.instrument == "BTCUSDT"
    assert strategy.frequency == "1h"
    assert len(strategy.indicators) == 1
    assert strategy.indicators[0].name == "RSI"
    assert strategy.indicators[0].parameters["period"] == 14
    assert len(strategy.conditions) == 1
    assert strategy.conditions[0].type == ConditionType.ENTRY
    assert strategy.conditions[0].logic == "RSI < 30"
    assert strategy.risk_management.stop_loss == 0.05
    assert strategy.risk_management.take_profit == 0.15
    assert strategy.is_valid() == True


def test_comprehensive_strategy_creation():
    """Test creating a comprehensive strategy with all components."""
    strategy = StrategyBase(
        name="Comprehensive Test Strategy",
        description="A comprehensive test strategy with all components",
        strategy_type="mean_reversion",
        instrument="ETHUSDT",
        frequency="4h",
        tags=["test", "comprehensive", "mean_reversion"],
        notes="This is a test strategy",
        version="1.0.0",
        source="manual",
        
        # Technical components
        indicators=[
            Indicator(
                name="Bollinger Bands", 
                parameters={"period": 20, "std_dev": 2},
                plot_type="band",
                overlay=True,
                source_data="close"
            ),
            Indicator(
                name="RSI",
                parameters={"period": 14},
                plot_type="line",
                overlay=False,
                source_data="close"
            )
        ],
        conditions=[
            Condition(
                type=ConditionType.ENTRY, 
                logic="close < lower_band",
                direction="long",
                priority=1,
                requires_indicators=["Bollinger Bands"]
            ),
            Condition(
                type=ConditionType.EXIT,
                logic="close > middle_band",
                direction="long",
                priority=1,
                requires_indicators=["Bollinger Bands"]
            ),
            Condition(
                type=ConditionType.FILTER,
                logic="RSI > 30",
                direction="both",
                priority=2,
                requires_indicators=["RSI"]
            )
        ],
        
        # Risk and position management
        position_sizing=PositionSizing(
            method=PositionSizingMethod.RISK_BASED,
            value=0.01,  # 1% risk per trade
            max_position_size=0.1,  # 10% max position size
            scaling=True,
            scaling_steps=2,
            scaling_factor=0.5  # Half size for each step
        ),
        risk_management=RiskManagement(
            stop_loss=0.02,  # 2% stop loss
            take_profit=0.06,  # 6% take profit
            max_positions=2,
            max_risk_per_trade=0.01,  # 1% risk per trade
            max_risk_total=0.05,  # 5% total risk
            stop_type=StopType.TRAILING,
            trailing_distance=0.01  # 1% trailing stop
        ),
        trade_management=TradeManagement(
            partial_exits=[
                PartialExit(threshold=0.02, size=0.5, stop_adjustment=0.005)
            ],
            breakeven_threshold=0.01,  # Move to breakeven after 1% profit
            stop_adjustment_ratio=0.5,  # Move stop to capture 50% of profits
            pyramiding=True,
            pyramiding_max_additions=2,
            pyramiding_threshold=0.01  # Add after 1% profit
        ),
        
        # Testing and performance
        backtesting=BacktestingConfig(
            method=BacktestMethod.WALK_FORWARD,
            initial_capital=10000.0,
            commission=0.001,  # 0.1% commission
            slippage=0.0005,  # 0.05% slippage
            walk_forward=WalkForwardConfig(in_sample_size="6M", out_sample_size="2M", windows=3)
        ),
        performance_config=PerformanceConfig(
            primary_metric=PerformanceMetric.SHARPE_RATIO,
            benchmark="BTCUSDT",
            risk_free_rate=0.01,  # 1% risk-free rate
            required_metrics=[
                PerformanceMetric.SHARPE_RATIO,
                PerformanceMetric.MAX_DRAWDOWN,
                PerformanceMetric.SORTINO_RATIO,
                PerformanceMetric.PROFIT_FACTOR
            ]
        ),
        
        # Additional metadata
        compatibility_score=0.85,
        knowledge_source={"source": "neo4j", "graph_id": "test_graph"}
    )
    
    # Verify strategy is valid
    assert strategy.is_valid() == True
    
    # Verify comprehensive components
    assert strategy.description == "A comprehensive test strategy with all components"
    assert "test" in strategy.tags
    assert strategy.position_sizing.method == PositionSizingMethod.RISK_BASED
    assert strategy.trade_management.partial_exits[0].threshold == 0.02
    assert strategy.backtesting.method == BacktestMethod.WALK_FORWARD
    assert strategy.backtesting.walk_forward.in_sample_size == "6M"
    assert strategy.performance_config.primary_metric == PerformanceMetric.SHARPE_RATIO
    assert strategy.compatibility_score == 0.85


def test_invalid_strategy():
    """Test that a strategy without required components is invalid."""
    # Strategy without entry conditions
    strategy_no_entry = StrategyBase(
        name="Invalid Strategy",
        strategy_type="momentum",
        instrument="BTCUSDT",
        frequency="1h",
        indicators=[
            Indicator(name="RSI", parameters={"period": 14})
        ],
        # Only exit conditions, no entry
        conditions=[
            Condition(type=ConditionType.EXIT, logic="RSI > 70")
        ],
        risk_management=RiskManagement(
            stop_loss=0.05,
            take_profit=0.15
        )
    )
    
    assert strategy_no_entry.is_valid() == False
    
    # Strategy without risk management
    strategy_no_risk = StrategyBase(
        name="Invalid Strategy",
        strategy_type="momentum",
        instrument="BTCUSDT",
        frequency="1h",
        indicators=[
            Indicator(name="RSI", parameters={"period": 14})
        ],
        conditions=[
            Condition(type=ConditionType.ENTRY, logic="RSI < 30")
        ],
        # No stop loss or take profit
        risk_management=RiskManagement()
    )
    
    assert strategy_no_risk.is_valid() == False


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])