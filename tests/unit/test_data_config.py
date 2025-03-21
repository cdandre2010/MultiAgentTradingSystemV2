import pytest
from datetime import datetime, timedelta
from src.models.strategy import (
    StrategyBase, DataConfig, DataSource, BacktestDataRange, 
    DataQualityRequirement, DataPreprocessing, DataSourceType, DataField,
    Indicator, Condition, ConditionType, PositionSizing, RiskManagement,
    BacktestingConfig
)


def test_basic_data_config_creation():
    """Test creating a basic data configuration."""
    data_config = DataConfig(
        sources=[
            DataSource(type=DataSourceType.INFLUXDB, priority=1),
            DataSource(type=DataSourceType.BINANCE, priority=2)
        ],
        backtest_range=BacktestDataRange(
            start_date="2023-01-01",
            end_date="2023-12-31",
            lookback_period="30D"
        ),
        quality_requirements=DataQualityRequirement(
            min_volume=1000.0,
            max_missing_data_points=5
        ),
        preprocessing=DataPreprocessing(
            fill_missing="forward_fill"
        )
    )
    
    assert len(data_config.sources) == 2
    assert data_config.sources[0].type == DataSourceType.INFLUXDB
    assert data_config.sources[1].type == DataSourceType.BINANCE
    assert data_config.backtest_range.start_date == "2023-01-01"
    assert data_config.backtest_range.end_date == "2023-12-31"
    assert data_config.backtest_range.lookback_period == "30D"
    assert data_config.quality_requirements.min_volume == 1000.0
    assert data_config.quality_requirements.max_missing_data_points == 5
    assert data_config.preprocessing.fill_missing == "forward_fill"


def test_data_source_fields():
    """Test required fields in data sources."""
    source = DataSource(
        type=DataSourceType.YAHOO,
        priority=1,
        required_fields={
            DataField.OPEN, DataField.HIGH, DataField.LOW, 
            DataField.CLOSE, DataField.VOLUME, DataField.VWAP
        }
    )
    
    assert DataField.OPEN in source.required_fields
    assert DataField.VWAP in source.required_fields
    assert len(source.required_fields) == 6


def test_backtest_data_range_validation():
    """Test validation of backtest date ranges."""
    # Valid date range
    valid_range = BacktestDataRange(
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    assert valid_range.start_date == "2023-01-01"
    assert valid_range.end_date == "2023-12-31"
    
    # Invalid date range (end before start)
    with pytest.raises(ValueError):
        BacktestDataRange(
            start_date="2023-12-31",
            end_date="2023-01-01"
        )
    
    # Invalid date range (too short)
    with pytest.raises(ValueError):
        BacktestDataRange(
            start_date="2023-01-01",
            end_date="2023-01-15"  # Less than 30 days
        )
    
    # Invalid lookback period format
    with pytest.raises(ValueError):
        BacktestDataRange(
            start_date="2023-01-01",
            end_date="2023-12-31",
            lookback_period="invalid"
        )


def test_strategy_with_data_config():
    """Test creating a strategy with data configuration."""
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
        ),
        data_config=DataConfig(
            sources=[
                DataSource(type=DataSourceType.INFLUXDB, priority=1),
                DataSource(type=DataSourceType.BINANCE, priority=2)
            ],
            backtest_range=BacktestDataRange(
                start_date="2023-01-01",
                end_date="2023-12-31"
            )
        ),
        backtesting=BacktestingConfig(
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31)
        )
    )
    
    assert strategy.is_valid() == True
    assert len(strategy.data_config.sources) == 2
    assert strategy.data_config.backtest_range.start_date == datetime(2023, 1, 1)
    
    # Test get_data_requirements method
    requirements = strategy.get_data_requirements()
    assert requirements["instrument"] == "BTCUSDT"
    assert requirements["frequency"] == "1h"
    assert requirements["start_date"] == "2023-01-01"
    assert len(requirements["sources"]) == 2
    assert "OPEN" in requirements["required_fields"] or "open" in requirements["required_fields"]


def test_data_source_priority_validation():
    """Test validation of data source priorities."""
    # Valid priorities
    valid_config = DataConfig(
        sources=[
            DataSource(type=DataSourceType.INFLUXDB, priority=1),
            DataSource(type=DataSourceType.BINANCE, priority=2),
            DataSource(type=DataSourceType.YAHOO, priority=3)
        ]
    )
    assert len(valid_config.sources) == 3
    
    # Invalid priorities (duplicate)
    with pytest.raises(ValueError):
        DataConfig(
            sources=[
                DataSource(type=DataSourceType.INFLUXDB, priority=1),
                DataSource(type=DataSourceType.BINANCE, priority=1),  # Duplicate priority
            ]
        )


def test_influxdb_auto_addition():
    """Test automatic addition of InfluxDB for caching."""
    # Without InfluxDB but caching enabled
    config = DataConfig(
        sources=[
            DataSource(type=DataSourceType.BINANCE, priority=1)
        ],
        cache_external_data=True
    )
    
    # Should automatically add InfluxDB
    assert len(config.sources) == 2
    assert any(s.type == DataSourceType.INFLUXDB for s in config.sources)
    
    # With caching disabled
    config_no_cache = DataConfig(
        sources=[
            DataSource(type=DataSourceType.BINANCE, priority=1)
        ],
        cache_external_data=False
    )
    
    # Should not add InfluxDB
    assert len(config_no_cache.sources) == 1
    assert not any(s.type == DataSourceType.INFLUXDB for s in config_no_cache.sources)


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])