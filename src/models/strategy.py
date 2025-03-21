from pydantic import BaseModel, Field, model_validator, field_validator
from typing import Optional, Dict, Any, List, Literal, Union, Set
from datetime import datetime, timedelta, time
from enum import Enum


class ParameterType(str, Enum):
    """Enumeration for parameter types."""
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    BOOLEAN = "boolean"
    ENUM = "enum"
    LIST = "list"
    DICT = "dict"


class Parameter(BaseModel):
    """Model for indicator or backtesting parameter."""
    name: str
    default_value: Any
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    type: Union[str, ParameterType] = "float"
    description: Optional[str] = None
    options: Optional[List[Any]] = None  # For enum types
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v, info):
        """Validate that options are provided for enum type."""
        values = info.data
        if values.get('type') == ParameterType.ENUM and (not v or len(v) == 0):
            raise ValueError("Options must be provided for enum parameter type")
        return v


class Indicator(BaseModel):
    """Model for a technical indicator."""
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = {}
    plot_type: Optional[str] = None  # line, histogram, band, etc.
    color: Optional[str] = None
    overlay: bool = False  # Whether indicator overlays on price chart
    source_data: Optional[str] = None  # close, open, high, low, volume, etc.


class SignalDirection(str, Enum):
    """Enumeration for signal directions."""
    LONG = "long"
    SHORT = "short"
    BOTH = "both"


class ConditionType(str, Enum):
    """Enumeration for condition types."""
    ENTRY = "entry"
    EXIT = "exit"
    FILTER = "filter"  # Market condition filter


class Condition(BaseModel):
    """Model for an entry or exit condition."""
    type: Union[str, ConditionType]  # entry, exit, filter
    logic: str
    description: Optional[str] = None
    direction: Union[str, SignalDirection] = SignalDirection.BOTH
    priority: int = 1  # Higher number = higher priority
    requires_indicators: List[str] = []  # Names of required indicators


class PositionSizingMethod(str, Enum):
    """Enumeration for position sizing methods."""
    FIXED = "fixed"  # Fixed quantity
    PERCENT = "percent"  # Percentage of account
    RISK_BASED = "risk_based"  # Size based on risk percentage per trade
    VOLATILITY = "volatility"  # Volatility-adjusted position size
    KELLY = "kelly"  # Kelly criterion for optimal sizing
    MARTINGALE = "martingale"  # Increase size after losses
    ANTI_MARTINGALE = "anti_martingale"  # Increase size after wins


class PositionSizing(BaseModel):
    """Enhanced model for position sizing settings."""
    method: Union[str, PositionSizingMethod] = "percent"  # percent, fixed, risk_based
    value: float = 1.0  # Percentage, fixed amount, or risk percentage
    max_position_size: Optional[float] = None  # Maximum position size as % of account
    sizing_indicator: Optional[str] = None  # Indicator used for volatility-based sizing
    scaling: bool = False  # Whether to scale in/out of positions
    scaling_steps: Optional[int] = None  # Number of steps for scaling
    scaling_factor: Optional[float] = None  # Factor for each scaling step


class StopType(str, Enum):
    """Enumeration for stop loss types."""
    FIXED = "fixed"  # Fixed price or percentage
    TRAILING = "trailing"  # Moving stop based on price action
    VOLATILITY = "volatility"  # Stop based on volatility (e.g., ATR)
    TIME = "time"  # Exit based on time elapsed
    INDICATOR = "indicator"  # Exit based on indicator value


class RiskManagement(BaseModel):
    """Enhanced model for risk management settings."""
    stop_loss: Optional[float] = None  # Price or percentage
    take_profit: Optional[float] = None  # Price or percentage
    max_positions: int = 1
    max_risk_per_trade: Optional[float] = None  # Max % risk per trade
    max_risk_total: Optional[float] = None  # Max total risk percentage
    max_drawdown_exit: Optional[float] = None  # Exit all if drawdown exceeds this
    stop_type: Union[str, StopType] = "fixed"
    trailing_distance: Optional[float] = None  # For trailing stops
    volatility_multiplier: Optional[float] = None  # For volatility stops
    time_exit_bars: Optional[int] = None  # For time-based exits
    indicator_exit: Optional[Dict[str, Any]] = None  # For indicator-based exits


class PartialExit(BaseModel):
    """Model for partial exit definition."""
    threshold: float  # Profit threshold to trigger exit
    size: float  # Portion of position to exit (0-1)
    stop_adjustment: Optional[float] = None  # How to adjust stop after exit


class TradeManagement(BaseModel):
    """Model for trade management rules."""
    partial_exits: List[PartialExit] = []
    breakeven_threshold: Optional[float] = None  # Move stop to entry after this profit
    stop_adjustment_ratio: Optional[float] = None  # Adjust stop by portion of profit
    time_exit_days: Optional[int] = None  # Exit after this many days
    profit_target_scaling: bool = False  # Scale profit targets
    re_entry_rules: Optional[Dict[str, Any]] = None  # Rules for re-entering after exit
    pyramiding: bool = False  # Add to winning positions
    pyramiding_max_additions: Optional[int] = None  # Maximum additions to position
    pyramiding_threshold: Optional[float] = None  # Profit threshold for adding
    
    @model_validator(mode='after')
    def validate_pyramiding(self):
        """Validate the pyramiding configuration."""
        if self.pyramiding and (self.pyramiding_max_additions is None or self.pyramiding_threshold is None):
            raise ValueError("pyramiding_max_additions and pyramiding_threshold must be provided when pyramiding is enabled")
        return self


class BacktestMethod(str, Enum):
    """Enumeration for backtesting methods."""
    SIMPLE = "simple"  # Single pass with fixed parameters
    WALK_FORWARD = "walk_forward"  # In-sample/out-of-sample validation
    MONTE_CARLO = "monte_carlo"  # Multiple simulations with random variations
    OPTIMIZATION = "optimization"  # Parameter optimization
    CROSS_VALIDATION = "cross_validation"  # K-fold cross validation


class WalkForwardConfig(BaseModel):
    """Configuration for walk-forward backtesting."""
    in_sample_size: str  # e.g., "6M" for 6 months
    out_sample_size: str  # e.g., "2M" for 2 months
    windows: int = 3  # Number of windows
    anchor: bool = False  # Whether to anchor the start date
    
    @field_validator('in_sample_size', 'out_sample_size')
    @classmethod
    def validate_time_period(cls, v):
        if not (v[-1] in ['D', 'W', 'M', 'Y'] and v[:-1].isdigit()):
            raise ValueError(f"Invalid time period format: {v}. Use format like '6M', '30D', etc.")
        return v


class OptimizationConfig(BaseModel):
    """Configuration for parameter optimization."""
    parameters: Dict[str, Dict[str, Any]]  # Parameters to optimize with ranges
    iterations: int = 100  # Number of iterations
    metric: str = "sharpe_ratio"  # Metric to optimize for
    method: str = "grid"  # grid, random, bayesian, genetic


class MonteCarloConfig(BaseModel):
    """Configuration for Monte Carlo simulations."""
    simulations: int = 1000
    capital_variations: bool = True  # Vary starting capital
    shuffle_trades: bool = True  # Shuffle trade order
    random_seed: Optional[int] = None  # For reproducibility


class BacktestingConfig(BaseModel):
    """Model for backtesting configuration."""
    method: Union[str, BacktestMethod] = "simple"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    initial_capital: float = 10000.0
    commission: float = 0.0
    slippage: float = 0.0
    data_source: str = "default"
    walk_forward: Optional[WalkForwardConfig] = None
    optimization: Optional[OptimizationConfig] = None
    monte_carlo: Optional[MonteCarloConfig] = None
    
    @model_validator(mode='after')
    def validate_config(self):
        """Validate that the appropriate configuration is provided based on the method."""
        if self.method == BacktestMethod.WALK_FORWARD and self.walk_forward is None:
            raise ValueError("walk_forward configuration must be provided for walk_forward method")
        if self.method == BacktestMethod.OPTIMIZATION and self.optimization is None:
            raise ValueError("optimization configuration must be provided for optimization method")
        if self.method == BacktestMethod.MONTE_CARLO and self.monte_carlo is None:
            raise ValueError("monte_carlo configuration must be provided for monte_carlo method")
        return self


class PerformanceMetric(str, Enum):
    """Enumeration for performance metrics."""
    TOTAL_RETURN = "total_return"
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    CALMAR_RATIO = "calmar_ratio"
    EXPECTANCY = "expectancy"
    RECOVERY_FACTOR = "recovery_factor"
    ULCER_INDEX = "ulcer_index"
    GAIN_TO_PAIN_RATIO = "gain_to_pain_ratio"


class PerformanceConfig(BaseModel):
    """Model for performance measurement configuration."""
    primary_metric: Union[str, PerformanceMetric] = PerformanceMetric.SHARPE_RATIO
    benchmark: Optional[str] = None  # Symbol for benchmark comparison
    risk_free_rate: float = 0.0  # For Sharpe/Sortino calculation
    required_metrics: List[Union[str, PerformanceMetric]] = [
        PerformanceMetric.TOTAL_RETURN,
        PerformanceMetric.SHARPE_RATIO,
        PerformanceMetric.MAX_DRAWDOWN,
        PerformanceMetric.WIN_RATE,
        PerformanceMetric.PROFIT_FACTOR
    ]
    minimum_trades: int = 30  # Minimum trades for reliable statistics
    custom_metrics: Optional[Dict[str, Any]] = None  # Custom performance metrics


class DataSourceType(str, Enum):
    """Enumeration for data source types."""
    INFLUXDB = "influxdb"   # Internal InfluxDB (primary cache)
    BINANCE = "binance"     # Binance API
    YAHOO = "yahoo"         # Yahoo Finance
    ALPHA_VANTAGE = "alpha_vantage"  # Alpha Vantage API
    CSV = "csv"             # CSV file
    CUSTOM = "custom"       # Custom data source


class DataField(str, Enum):
    """Enumeration for required data fields."""
    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    VOLUME = "volume"
    VWAP = "vwap"           # Volume-weighted average price
    OI = "open_interest"    # Open interest (for futures)


class DataQualityRequirement(BaseModel):
    """Model for data quality requirements."""
    min_volume: Optional[float] = None  # Minimum trading volume
    max_missing_data_points: Optional[int] = None  # Maximum allowed missing data points
    min_data_points: Optional[int] = None  # Minimum required data points
    exclude_anomalies: bool = True  # Whether to exclude data anomalies
    exclude_gaps: bool = True  # Whether to exclude gaps in data


class DataPreprocessing(BaseModel):
    """Model for data preprocessing specifications."""
    normalization: Optional[str] = None  # min-max, z-score, etc.
    outlier_treatment: Optional[str] = None  # clip, remove, winsorize, etc.
    smoothing: Optional[Dict[str, Any]] = None  # smoothing method and parameters
    fill_missing: Optional[str] = "forward_fill"  # forward fill, backward fill, interpolate, etc.
    feature_engineering: Optional[List[Dict[str, Any]]] = None  # Feature engineering steps


class DataSource(BaseModel):
    """Model for data source configuration."""
    type: Union[str, DataSourceType]
    priority: int = 1  # Lower number = higher priority (1 = highest)
    api_key_reference: Optional[str] = None  # Reference to API key (not the key itself)
    required_fields: Set[Union[str, DataField]] = {
        DataField.OPEN, DataField.HIGH, DataField.LOW, DataField.CLOSE, DataField.VOLUME
    }
    custom_parameters: Optional[Dict[str, Any]] = None  # Custom parameters for the data source


class BacktestDataRange(BaseModel):
    """Model for backtest data range configuration."""
    start_date: Union[str, datetime]  # Start date for backtesting
    end_date: Union[str, datetime]  # End date for backtesting
    lookback_period: Optional[str] = None  # Additional lookback period for indicators
    
    @field_validator('lookback_period')
    @classmethod
    def validate_lookback_period(cls, v):
        if v is not None and not (v[-1] in ['D', 'W', 'M', 'Y'] and v[:-1].isdigit()):
            raise ValueError(f"Invalid time period format: {v}. Use format like '6M', '30D', etc.")
        return v
    
    @model_validator(mode='after')
    def validate_dates(self):
        """Validate that the backtest dates make sense."""
        # Convert string dates to datetime if needed
        start = self.start_date if isinstance(self.start_date, datetime) else datetime.fromisoformat(self.start_date)
        end = self.end_date if isinstance(self.end_date, datetime) else datetime.fromisoformat(self.end_date)
        
        if end <= start:
            raise ValueError("End date must be after start date")
        
        # Minimum period for meaningful backtest
        min_duration = timedelta(days=30)
        if end - start < min_duration:
            raise ValueError(f"Backtest duration must be at least {min_duration.days} days")
        
        return self


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
    
    @model_validator(mode='after')
    def validate_sources(self):
        """Validate data sources configuration."""
        if not self.sources:
            raise ValueError("At least one data source must be specified")
        
        # Ensure InfluxDB is included as a source for caching
        if self.cache_external_data and not any(s.type == DataSourceType.INFLUXDB for s in self.sources):
            self.sources.append(DataSource(type=DataSourceType.INFLUXDB, priority=len(self.sources) + 1))
        
        # Ensure priorities are unique
        priorities = [s.priority for s in self.sources]
        if len(priorities) != len(set(priorities)):
            raise ValueError("Data source priorities must be unique")
            
        return self


class StrategyBase(BaseModel):
    """Enhanced base strategy model with comprehensive attributes."""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    strategy_type: str
    instrument: str
    frequency: str
    tags: List[str] = []
    notes: Optional[str] = None
    version: str = "1.0.0"
    source: Optional[str] = None  # Source of the strategy (manual, template, etc.)
    
    # Technical components
    indicators: List[Indicator] = []
    conditions: List[Condition] = []
    
    # Risk and position management
    position_sizing: PositionSizing = Field(default_factory=PositionSizing)
    risk_management: RiskManagement = Field(default_factory=RiskManagement)
    trade_management: TradeManagement = Field(default_factory=TradeManagement)
    
    # Testing and performance
    backtesting: BacktestingConfig = Field(default_factory=BacktestingConfig)
    performance_config: PerformanceConfig = Field(default_factory=PerformanceConfig)
    
    # Data configuration
    data_config: DataConfig = Field(default_factory=DataConfig)
    
    model_config = {
        "arbitrary_types_allowed": True
    }
    
    # Additional metadata
    compatibility_score: Optional[float] = None  # Neo4j-based component compatibility
    knowledge_source: Optional[Dict[str, Any]] = None  # Knowledge graph sources
    
    @model_validator(mode='after')
    def validate_conditions_and_indicators(self):
        """Validate that all indicators required by conditions are present."""
        # Check that all indicators required by conditions are present
        indicator_names = [ind.name for ind in self.indicators]
        for condition in self.conditions:
            if hasattr(condition, 'requires_indicators') and condition.requires_indicators:
                for req_indicator in condition.requires_indicators:
                    if req_indicator not in indicator_names:
                        raise ValueError(f"Condition requires indicator '{req_indicator}' which is not present in the strategy")
        return self
        
    @model_validator(mode='after')
    def validate_data_requirements(self):
        """Validate data configuration meets strategy requirements."""
        # If backtest date range is provided in both places, modify to match automatically
        if (self.backtesting.start_date and self.backtesting.end_date and 
            self.data_config.backtest_range):
            # Just use the backtesting dates for consistency
            self.data_config.backtest_range.start_date = self.backtesting.start_date
            self.data_config.backtest_range.end_date = self.backtesting.end_date
        
        # If no backtest range in data_config but exists in backtesting, copy it over
        elif self.backtesting.start_date and self.backtesting.end_date and not self.data_config.backtest_range:
            self.data_config.backtest_range = BacktestDataRange(
                start_date=self.backtesting.start_date,
                end_date=self.backtesting.end_date
            )
            
        # Check that at least one source can provide required fields
        if self.indicators:
            # For now, assume all indicators need OHLCV data
            required_fields = {
                DataField.OPEN, 
                DataField.HIGH, 
                DataField.LOW, 
                DataField.CLOSE, 
                DataField.VOLUME
            }
            
            # Check if any source can provide all required fields
            any_source_complete = False
            for source in self.data_config.sources:
                if all(field in source.required_fields for field in required_fields):
                    any_source_complete = True
                    break
                    
            if not any_source_complete:
                raise ValueError("No data source configured to provide all required fields for the strategy indicators")
                
        return self
    
    def is_valid(self) -> bool:
        """Check if the strategy is valid and complete."""
        # A valid strategy needs at least one entry condition
        has_entry = any(c.type == "entry" or c.type == ConditionType.ENTRY for c in self.conditions)
        
        # Strategy should have at least one indicator
        has_indicators = len(self.indicators) > 0
        
        # Risk management should have either stop_loss or take_profit
        has_risk_management = (self.risk_management.stop_loss is not None or 
                              self.risk_management.take_profit is not None)
        
        # Data configuration should have at least one source and backtest range if using backtesting
        has_data_config = (len(self.data_config.sources) > 0 and
                          (not self.backtesting.start_date or self.data_config.backtest_range is not None))
        
        return has_entry and has_indicators and has_risk_management and has_data_config
        
    def get_data_requirements(self) -> Dict[str, Any]:
        """Generate a summary of data requirements for this strategy."""
        # Format dates to strings if they are datetime objects
        start_date = self.data_config.backtest_range.start_date if self.data_config.backtest_range else None
        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d")
            
        end_date = self.data_config.backtest_range.end_date if self.data_config.backtest_range else None
        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d")
            
        return {
            "instrument": self.instrument,
            "frequency": self.frequency,
            "start_date": start_date,
            "end_date": end_date,
            "lookback_period": self.data_config.backtest_range.lookback_period if self.data_config.backtest_range else None,
            "sources": [{"type": s.type, "priority": s.priority} for s in self.data_config.sources],
            "required_fields": list({f for s in self.data_config.sources for f in s.required_fields}),
            "quality_requirements": (self.data_config.quality_requirements.model_dump(exclude_none=True) 
                                 if hasattr(self.data_config.quality_requirements, 'model_dump') 
                                 else self.data_config.quality_requirements.dict(exclude_none=True)),
            "preprocessing": (self.data_config.preprocessing.model_dump(exclude_none=True)
                            if hasattr(self.data_config.preprocessing, 'model_dump')
                            else self.data_config.preprocessing.dict(exclude_none=True))
        }


class StrategyCreate(StrategyBase):
    """Strategy creation model."""
    pass


class StrategyUpdate(BaseModel):
    """Enhanced strategy update model."""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    strategy_type: Optional[str] = None
    instrument: Optional[str] = None
    frequency: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    version: Optional[str] = None
    source: Optional[str] = None
    
    # Technical components
    indicators: Optional[List[Indicator]] = None
    conditions: Optional[List[Condition]] = None
    
    # Risk and position management
    position_sizing: Optional[PositionSizing] = None
    risk_management: Optional[RiskManagement] = None
    trade_management: Optional[TradeManagement] = None
    
    # Testing and performance
    backtesting: Optional[BacktestingConfig] = None
    performance_config: Optional[PerformanceConfig] = None
    
    # Additional metadata
    compatibility_score: Optional[float] = None
    knowledge_source: Optional[Dict[str, Any]] = None


class StrategyInDB(StrategyBase):
    """Strategy model as stored in the database."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    version_history: List[str] = []  # List of previous version IDs
    
    model_config = {
        "from_attributes": True
    }


class Strategy(StrategyBase):
    """Strategy model returned to clients."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class BacktestRequest(BaseModel):
    """Enhanced model for backtest request."""
    strategy_id: str
    start_date: datetime
    end_date: datetime
    initial_capital: float = 10000.0
    parameters: Optional[Dict[str, Any]] = None
    method: Union[str, BacktestMethod] = BacktestMethod.SIMPLE
    walk_forward_config: Optional[WalkForwardConfig] = None
    optimization_config: Optional[OptimizationConfig] = None
    monte_carlo_config: Optional[MonteCarloConfig] = None
    data_sources: Optional[List["DataSource"]] = None  # Override strategy data sources if provided
    data_preprocessing: Optional["DataPreprocessing"] = None  # Override preprocessing if provided
    benchmark: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_dates(self):
        """Validate that the backtest dates are valid."""
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")
        
        # Minimum 30 days for backtesting
        min_duration = timedelta(days=30)
        if self.end_date - self.start_date < min_duration:
            raise ValueError(f"Backtest duration must be at least {min_duration.days} days")
        
        return self


class TradeDirection(str, Enum):
    """Enumeration for trade directions."""
    LONG = "long"
    SHORT = "short"


class ExitReason(str, Enum):
    """Enumeration for trade exit reasons."""
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"
    TIME_EXIT = "time_exit"
    SIGNAL_EXIT = "signal_exit"
    MANUAL_EXIT = "manual_exit"
    SESSION_CLOSE = "session_close"
    POSITION_CLOSE = "position_close"


class TradeRecord(BaseModel):
    """Enhanced model for individual trade in backtest results."""
    entry_time: datetime
    exit_time: Optional[datetime] = None
    instrument: str
    direction: Union[str, TradeDirection]
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    profit_loss: Optional[float] = None
    profit_loss_percent: Optional[float] = None
    exit_reason: Optional[Union[str, ExitReason]] = None
    entry_condition: Optional[str] = None  # Which condition triggered entry
    exit_condition: Optional[str] = None  # Which condition triggered exit
    fees: float = 0.0
    slippage: float = 0.0
    risk_reward_ratio: Optional[float] = None  # Potential R:R at entry
    bars_held: Optional[int] = None  # Number of bars position was held
    trade_id: Optional[str] = None  # Unique identifier
    drawdown: Optional[float] = None  # Maximum drawdown during trade
    partial_exits: List[Dict[str, Any]] = []  # Records of partial exits
    entry_notes: Optional[str] = None  # Custom notes about entry
    exit_notes: Optional[str] = None  # Custom notes about exit
    entry_score: Optional[float] = None  # Quality score of entry
    exit_score: Optional[float] = None  # Quality score of exit
    trade_tags: List[str] = []  # Categorization tags


class BacktestPerformance(BaseModel):
    """Enhanced model for backtest performance metrics."""
    total_return: float
    total_return_percent: float
    annualized_return: float
    max_drawdown: float
    max_drawdown_percent: float
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    trade_count: int
    win_rate: Optional[float] = None
    average_win: Optional[float] = None
    average_loss: Optional[float] = None
    profit_factor: Optional[float] = None
    expectancy: Optional[float] = None
    average_hold_time: Optional[float] = None
    recovery_factor: Optional[float] = None
    ulcer_index: Optional[float] = None
    gain_to_pain_ratio: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    volatility: Optional[float] = None
    var_95: Optional[float] = None  # 95% Value at Risk
    cvar_95: Optional[float] = None  # Conditional VaR
    max_consecutive_wins: Optional[int] = None
    max_consecutive_losses: Optional[int] = None
    win_loss_ratio: Optional[float] = None
    largest_win: Optional[float] = None
    largest_loss: Optional[float] = None
    drawdown_duration: Optional[int] = None
    best_month: Optional[float] = None
    worst_month: Optional[float] = None
    monthly_returns: Optional[Dict[str, float]] = None
    
    # Performance by market condition
    trending_market_performance: Optional[float] = None
    ranging_market_performance: Optional[float] = None
    volatile_market_performance: Optional[float] = None
    
    # Additional metrics
    custom_metrics: Optional[Dict[str, float]] = None


class BacktestResult(BaseModel):
    """Enhanced model for complete backtest results."""
    id: str
    strategy_id: str
    user_id: str
    name: str
    start_date: datetime
    end_date: datetime
    created_at: datetime
    method: Union[str, BacktestMethod]
    initial_capital: float
    final_capital: float
    parameters: Dict[str, Any]
    performance: BacktestPerformance
    trades: List[TradeRecord] = []
    equity_curve: Optional[List[Dict[str, Any]]] = None
    drawdown_curve: Optional[List[Dict[str, Any]]] = None
    monthly_performance: Optional[Dict[str, float]] = None
    position_history: Optional[List[Dict[str, Any]]] = None
    benchmark_performance: Optional[Dict[str, Any]] = None
    walk_forward_results: Optional[List[Dict[str, Any]]] = None
    optimization_results: Optional[Dict[str, Any]] = None
    monte_carlo_results: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    tags: List[str] = []
    
    @property
    def duration_days(self) -> int:
        """Calculate the duration of the backtest in days."""
        return (self.end_date - self.start_date).days