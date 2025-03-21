# Strategy Data Configuration Design

## Overview

The data configuration component of the strategy model is designed to manage how the system obtains, processes, and validates data for backtesting and analysis. It prioritizes the use of cached data in InfluxDB while providing fallback options to external sources when needed, ensuring efficient and reliable data management.

## Key Requirements

1. **Cached-First Approach**: Always check InfluxDB first before querying external APIs
2. **Incremental Updates**: Only fetch missing data segments
3. **Data Quality Validation**: Verify data meets quality requirements
4. **Flexible Source Selection**: Support multiple data sources with priority ordering
5. **Preprocessing Capabilities**: Support normalization, cleaning, and feature engineering
6. **User Dialog Support**: Enable ConversationalAgent to discuss data requirements

## Data Configuration Components

### 1. DataSource

Represents a specific data source with priority ranking:

```python
class DataSourceType(str, Enum):
    """Enumeration for data source types."""
    INFLUXDB = "influxdb"   # Internal InfluxDB (primary cache)
    BINANCE = "binance"     # Binance API
    YAHOO = "yahoo"         # Yahoo Finance
    ALPHA_VANTAGE = "alpha_vantage"  # Alpha Vantage API
    CSV = "csv"             # CSV file
    CUSTOM = "custom"       # Custom data source

class DataSource(BaseModel):
    """Model for data source configuration."""
    type: Union[str, DataSourceType]
    priority: int = 1  # Lower number = higher priority (1 = highest)
    api_key_reference: Optional[str] = None  # Reference to API key (not the key itself)
    required_fields: Set[Union[str, DataField]] = {
        DataField.OPEN, DataField.HIGH, DataField.LOW, DataField.CLOSE, DataField.VOLUME
    }
    custom_parameters: Optional[Dict[str, Any]] = None  # Custom parameters for the data source
```

### 2. BacktestDataRange

Specifies the date range for backtesting, including lookback periods for indicators:

```python
class BacktestDataRange(BaseModel):
    """Model for backtest data range configuration."""
    start_date: Union[str, datetime]  # Start date for backtesting
    end_date: Union[str, datetime]  # End date for backtesting
    lookback_period: Optional[str] = None  # Additional lookback period for indicators
```

### 3. DataQualityRequirement

Defines the quality standards for the data:

```python
class DataQualityRequirement(BaseModel):
    """Model for data quality requirements."""
    min_volume: Optional[float] = None  # Minimum trading volume
    max_missing_data_points: Optional[int] = None  # Maximum allowed missing data points
    min_data_points: Optional[int] = None  # Minimum required data points
    exclude_anomalies: bool = True  # Whether to exclude data anomalies
    exclude_gaps: bool = True  # Whether to exclude gaps in data
```

### 4. DataPreprocessing

Specifies how data should be processed before use:

```python
class DataPreprocessing(BaseModel):
    """Model for data preprocessing specifications."""
    normalization: Optional[str] = None  # min-max, z-score, etc.
    outlier_treatment: Optional[str] = None  # clip, remove, winsorize, etc.
    smoothing: Optional[Dict[str, Any]] = None  # smoothing method and parameters
    fill_missing: Optional[str] = "forward_fill"  # forward fill, backward fill, interpolate, etc.
    feature_engineering: Optional[List[Dict[str, Any]]] = None  # Feature engineering steps
```

### 5. DataConfig

The main container for all data configuration:

```python
class DataConfig(BaseModel):
    """Comprehensive model for data configuration."""
    sources: List[DataSource] = [
        DataSource(type=DataSourceType.INFLUXDB, priority=1),  # InfluxDB as primary source
        DataSource(type=DataSourceType.BINANCE, priority=2)    # Binance as fallback
    ]
    backtest_range: Optional[BacktestDataRange] = None
    quality_requirements: DataQualityRequirement = Field(default_factory=DataQualityRequirement)
    preprocessing: DataPreprocessing = Field(default_factory=DataPreprocessing)
    check_data_availability: bool = True  # Whether to check if data exists in InfluxDB first
    cache_external_data: bool = True  # Whether to cache external data in InfluxDB
```

## Data Handling Process Flow

1. **Data Requirements Gathering**:
   - ConversationalAgent asks user about data requirements
   - Based on instrument, frequency, and date range
   - Suggests appropriate sources based on instrument

2. **Availability Checking**:
   - Check InfluxDB for existing data
   - Determine data completeness
   - Identify missing segments

3. **Data Retrieval**:
   - If complete data exists in InfluxDB, use it directly
   - Otherwise, fetch only missing segments from external sources
   - Cache newly fetched data in InfluxDB

4. **Data Preprocessing**:
   - Apply quality filters
   - Perform normalization and cleaning
   - Apply any feature engineering steps

5. **Data Validation**:
   - Verify data meets quality requirements
   - Confirm sufficient data points
   - Check for gaps or anomalies

## Integration with Other Components

### ConversationalAgent Integration

The ConversationalAgent will be enhanced to discuss data requirements with users:

```
User: "I want to create a strategy for Bitcoin using RSI"
Agent: "Great, let me ask about your data requirements. What timeframe would you like to use?"
User: "1-hour candles"
Agent: "I'll set up 1-hour data. How far back would you like to backtest? I recommend at least 1 year of data for reliable results."
User: "Let's use 2 years"
Agent: "Perfect. I'll check our InfluxDB cache first, and if needed, fetch any missing data from Binance. Should I apply any specific data preprocessing?"
User: "No special preprocessing"
Agent: "Okay, I'll use standard preprocessing. Based on your RSI indicator, I'll include a 14-day lookback period before your backtest start date."
```

### ValidationAgent Integration

The ValidationAgent will verify data configuration completeness and consistency:

1. Ensure start and end dates are properly specified
2. Verify lookback periods are appropriate for the chosen indicators
3. Check that required data fields are available
4. Validate that preprocessing settings are appropriate for the strategy type

### DataFeatureAgent Integration

The DataFeatureAgent will use data configuration to intelligently manage data:

1. Check InfluxDB first based on the priority in DataConfig
2. Only fetch missing data from external sources
3. Apply specified preprocessing steps
4. Verify data quality meets the specified requirements

## Implementation Plan

1. Create DataConfig models in the strategy.py file
2. Update StrategyBase model to include data configuration
3. Modify ConversationalAgent to discuss data requirements
4. Enhance ValidationAgent to validate data configuration
5. Update DataFeatureAgent to use the data configuration for intelligent fetching
6. Create tests for data configuration validation and usage

## Benefits

1. **Efficiency**: Minimizes external API calls by prioritizing cached data
2. **Reliability**: Ensures consistent data quality across strategies
3. **Flexibility**: Supports multiple data sources with fallback options
4. **Transparency**: Makes data requirements explicit in strategy definition
5. **User Experience**: Guides users to specify appropriate data requirements