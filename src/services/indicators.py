"""
On-demand indicator calculation service.

This module provides services for calculating technical indicators on-demand
based on raw OHLCV data, with support for various indicator types and parameters.
It includes optimized calculation functions, parameter validation, and caching
for improved performance.

Implementation based on TA-Lib for reliability, performance, and maintenance benefits.
"""

import logging
import numpy as np
import pandas as pd
import talib
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Callable, Tuple
import hashlib
import json
from enum import Enum
from functools import lru_cache
import warnings

from ..models.market_data import OHLCV, OHLCVPoint

# Suppress pandas future warnings during indicator calculations
warnings.simplefilter(action='ignore', category=FutureWarning)

logger = logging.getLogger(__name__)


class IndicatorCategory(str, Enum):
    """Categories of technical indicators."""
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    PATTERN = "pattern"
    CUSTOM = "custom"


class IndicatorType(str, Enum):
    """Types of technical indicators."""
    # Trend indicators
    SMA = "sma"  # Simple Moving Average
    EMA = "ema"  # Exponential Moving Average
    WMA = "wma"  # Weighted Moving Average
    DEMA = "dema"  # Double Exponential Moving Average
    TEMA = "tema"  # Triple Exponential Moving Average
    TRIX = "trix"  # Triple Exponential Average Oscillator
    ADX = "adx"  # Average Directional Index
    ICHIMOKU = "ichimoku"  # Ichimoku Cloud
    SUPERTREND = "supertrend"  # Supertrend
    
    # Momentum indicators
    RSI = "rsi"  # Relative Strength Index
    STOCHASTIC = "stochastic"  # Stochastic Oscillator
    MACD = "macd"  # Moving Average Convergence Divergence
    MFI = "mfi"  # Money Flow Index
    CCI = "cci"  # Commodity Channel Index
    ROC = "roc"  # Rate of Change
    
    # Volatility indicators
    BOLLINGER_BANDS = "bollinger_bands"  # Bollinger Bands
    ATR = "atr"  # Average True Range
    KC = "keltner_channel"  # Keltner Channel
    
    # Volume indicators
    OBV = "obv"  # On-Balance Volume
    VWAP = "vwap"  # Volume-Weighted Average Price
    CMF = "cmf"  # Chaikin Money Flow
    
    # Pattern indicators
    ENGULFING = "engulfing"  # Bullish/Bearish Engulfing Pattern
    DOJI = "doji"  # Doji Pattern
    
    # Custom
    CUSTOM = "custom"  # Custom indicator


class IndicatorService:
    """
    Service for on-demand calculation of technical indicators.
    
    This service provides methods for calculating various technical indicators
    based on raw OHLCV data, with support for parameter customization,
    optimization, and caching. It includes a comprehensive set of indicators
    across multiple categories (trend, momentum, volatility, volume, pattern).
    
    Implementation uses TA-Lib for reliable and optimized calculations.
    """
    
    def __init__(self, cache_enabled: bool = True, max_cache_size: int = 100,
                optimize: bool = True, validate_params: bool = True):
        """
        Initialize the service.
        
        Args:
            cache_enabled: Whether to enable in-memory caching
            max_cache_size: Maximum number of cached calculations
            optimize: Whether to use optimized calculation methods
            validate_params: Whether to validate indicator parameters
        """
        self._cache_enabled = cache_enabled
        self._max_cache_size = max_cache_size
        self._cache = {}
        self._cache_keys = []  # Used for LRU cache management
        self._optimize = optimize
        self._validate_params = validate_params
        
        # Indicator metadata with default parameters
        self._indicator_metadata = self._initialize_indicator_metadata()
        
        # Initialize LRU cache for pandas operations
        if self._optimize:
            # Apply LRU cache to expensive operations
            self._optimize_pandas_operations()
            logger.info("Optimized pandas operations enabled")
            
        logger.debug(f"IndicatorService initialized: cache_enabled={cache_enabled}, "
                    f"max_cache_size={max_cache_size}, optimize={optimize}, "
                    f"validate_params={validate_params}")
            
    def _initialize_indicator_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize metadata for all supported indicators.
        
        Returns:
            Dictionary with indicator metadata
        """
        return {
            # Trend indicators
            IndicatorType.SMA: {
                "name": "Simple Moving Average",
                "category": IndicatorCategory.TREND,
                "default_params": {"period": 14, "source": "close"},
                "param_validation": {
                    "period": {"type": int, "min": 1, "max": 500},
                    "source": {"type": str, "options": ["open", "high", "low", "close", "volume", "hlc3", "ohlc4"]}
                },
                "description": "Trend-following indicator that averages price over a period"
            },
            IndicatorType.EMA: {
                "name": "Exponential Moving Average",
                "category": IndicatorCategory.TREND,
                "default_params": {"period": 14, "source": "close"},
                "param_validation": {
                    "period": {"type": int, "min": 1, "max": 500},
                    "source": {"type": str, "options": ["open", "high", "low", "close", "volume", "hlc3", "ohlc4"]}
                },
                "description": "Trend-following indicator with more weight to recent prices"
            },
            IndicatorType.WMA: {
                "name": "Weighted Moving Average",
                "category": IndicatorCategory.TREND,
                "default_params": {"period": 14, "source": "close"},
                "param_validation": {
                    "period": {"type": int, "min": 1, "max": 500},
                    "source": {"type": str, "options": ["open", "high", "low", "close", "volume", "hlc3", "ohlc4"]}
                },
                "description": "Trend-following indicator that assigns more weight to recent data"
            },
            IndicatorType.DEMA: {
                "name": "Double Exponential Moving Average",
                "category": IndicatorCategory.TREND,
                "default_params": {"period": 14, "source": "close"},
                "param_validation": {
                    "period": {"type": int, "min": 1, "max": 500},
                    "source": {"type": str, "options": ["open", "high", "low", "close", "volume", "hlc3", "ohlc4"]}
                },
                "description": "Trend-following indicator with reduced lag compared to EMA"
            },
            IndicatorType.TEMA: {
                "name": "Triple Exponential Moving Average",
                "category": IndicatorCategory.TREND,
                "default_params": {"period": 14, "source": "close"},
                "param_validation": {
                    "period": {"type": int, "min": 1, "max": 500},
                    "source": {"type": str, "options": ["open", "high", "low", "close", "volume", "hlc3", "ohlc4"]}
                },
                "description": "Trend-following indicator with minimal lag"
            },
            IndicatorType.RSI: {
                "name": "Relative Strength Index",
                "category": IndicatorCategory.MOMENTUM,
                "default_params": {"period": 14, "source": "close"},
                "param_validation": {
                    "period": {"type": int, "min": 1, "max": 500},
                    "source": {"type": str, "options": ["open", "high", "low", "close", "hlc3", "ohlc4"]}
                },
                "description": "Momentum oscillator measuring the speed and change of price movements"
            },
            IndicatorType.MACD: {
                "name": "Moving Average Convergence Divergence",
                "category": IndicatorCategory.MOMENTUM,
                "default_params": {"fast_period": 12, "slow_period": 26, "signal_period": 9, "source": "close"},
                "param_validation": {
                    "fast_period": {"type": int, "min": 1, "max": 100},
                    "slow_period": {"type": int, "min": 1, "max": 100},
                    "signal_period": {"type": int, "min": 1, "max": 100},
                    "source": {"type": str, "options": ["open", "high", "low", "close", "hlc3", "ohlc4"]}
                },
                "description": "Trend-following momentum indicator showing relationship between two EMAs"
            },
            IndicatorType.STOCHASTIC: {
                "name": "Stochastic Oscillator",
                "category": IndicatorCategory.MOMENTUM,
                "default_params": {"k_period": 14, "d_period": 3},
                "param_validation": {
                    "k_period": {"type": int, "min": 1, "max": 100},
                    "d_period": {"type": int, "min": 1, "max": 100}
                },
                "description": "Momentum indicator comparing closing price to price range over time"
            },
            IndicatorType.BOLLINGER_BANDS: {
                "name": "Bollinger Bands",
                "category": IndicatorCategory.VOLATILITY,
                "default_params": {"period": 20, "std_dev": 2.0, "source": "close"},
                "param_validation": {
                    "period": {"type": int, "min": 1, "max": 500},
                    "std_dev": {"type": (int, float), "min": 0.1, "max": 10},
                    "source": {"type": str, "options": ["open", "high", "low", "close", "hlc3", "ohlc4"]}
                },
                "description": "Volatility indicator that creates bands around a moving average"
            },
            IndicatorType.ATR: {
                "name": "Average True Range",
                "category": IndicatorCategory.VOLATILITY,
                "default_params": {"period": 14},
                "param_validation": {
                    "period": {"type": int, "min": 1, "max": 100}
                },
                "description": "Volatility indicator showing average range of price movement"
            },
            IndicatorType.OBV: {
                "name": "On-Balance Volume",
                "category": IndicatorCategory.VOLUME,
                "default_params": {},
                "param_validation": {},
                "description": "Volume indicator that shows buying/selling pressure"
            },
            IndicatorType.VWAP: {
                "name": "Volume-Weighted Average Price",
                "category": IndicatorCategory.VOLUME,
                "default_params": {},
                "param_validation": {},
                "description": "Shows average price weighted by volume"
            },
            IndicatorType.ADX: {
                "name": "Average Directional Index",
                "category": IndicatorCategory.TREND,
                "default_params": {"period": 14},
                "param_validation": {
                    "period": {"type": int, "min": 1, "max": 100}
                },
                "description": "Trend strength indicator"
            },
            IndicatorType.ICHIMOKU: {
                "name": "Ichimoku Cloud",
                "category": IndicatorCategory.TREND,
                "default_params": {"tenkan_period": 9, "kijun_period": 26, "senkou_span_b_period": 52, "displacement": 26},
                "param_validation": {
                    "tenkan_period": {"type": int, "min": 1, "max": 100},
                    "kijun_period": {"type": int, "min": 1, "max": 100},
                    "senkou_span_b_period": {"type": int, "min": 1, "max": 100},
                    "displacement": {"type": int, "min": 1, "max": 100}
                },
                "description": "Comprehensive indicator showing support/resistance, momentum, and trend direction"
            }
            # Add more indicators as needed...
        }
    
    def calculate_indicator(self, indicator_type: str, ohlcv_data: OHLCV,
                           parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate a technical indicator from OHLCV data.
        
        Args:
            indicator_type: The type of indicator (e.g., "sma", "rsi")
            ohlcv_data: The OHLCV data
            parameters: Parameters for the indicator calculation
            
        Returns:
            Dict containing indicator values and metadata
        """
        try:
            # Normalize indicator type
            indicator_type = indicator_type.lower()
            
            # Merge default parameters with provided parameters
            if indicator_type in self._indicator_metadata:
                default_params = self._indicator_metadata[indicator_type].get("default_params", {})
                # Parameters from user override defaults
                merged_params = {**default_params, **parameters}
            else:
                merged_params = parameters
            
            # Validate parameters if enabled
            if self._validate_params:
                is_valid, error = self.validate_parameters(indicator_type, merged_params)
                if not is_valid:
                    logger.error(f"Invalid parameters for {indicator_type}: {error}")
                    return {"error": error}
            
            # Check cache first if enabled
            if self._cache_enabled:
                cache_key = self._generate_cache_key(indicator_type, ohlcv_data, merged_params)
                if cache_key in self._cache:
                    # Update cache order for LRU
                    self._cache_keys.remove(cache_key)
                    self._cache_keys.append(cache_key)
                    return self._cache[cache_key]
            
            # Convert OHLCV data to pandas DataFrame for calculations
            df = self._convert_to_dataframe(ohlcv_data)
            
            # Calculate the requested indicator
            indicator_func = self._get_indicator_function(indicator_type)
            if indicator_func is None:
                logger.error(f"Unknown indicator type: {indicator_type}")
                return {"error": f"Unknown indicator type: {indicator_type}"}
            
            # Calculate indicator
            result = indicator_func(df, merged_params)
            
            # Add indicator metadata
            metadata = {
                "indicator_type": indicator_type,
                "parameters": merged_params,
                "instrument": ohlcv_data.instrument,
                "timeframe": ohlcv_data.timeframe,
                "calculation_time": datetime.now().isoformat(),
                "data_points": len(ohlcv_data.data),
                "data_start": ohlcv_data.start_date.isoformat() if ohlcv_data.start_date else None,
                "data_end": ohlcv_data.end_date.isoformat() if ohlcv_data.end_date else None
            }
            
            # Add category if available
            if indicator_type in self._indicator_metadata:
                category = self._indicator_metadata[indicator_type].get("category")
                if category:
                    metadata["category"] = category
            
            result["metadata"] = metadata
            
            # Cache the result if enabled
            if self._cache_enabled:
                self._add_to_cache(cache_key, result)
            
            return result
                
        except Exception as e:
            logger.error(f"Error calculating {indicator_type}: {e}")
            return {"error": str(e)}
    
    def calculate_multiple_indicators(self, ohlcv_data: OHLCV,
                                    indicators_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate multiple indicators at once for efficiency.
        
        Optimizes calculations by:
        1. Converting OHLCV data to DataFrame only once
        2. Reusing shared intermediate calculations where possible
        3. Using cached results when available
        
        Args:
            ohlcv_data: The OHLCV data
            indicators_config: List of indicator configurations with format:
                               [{"type": "sma", "parameters": {...}, "name": "optional_name"}, ...]
            
        Returns:
            Dict containing all calculated indicators with the specified names as keys
        """
        try:
            results = {}
            
            # Convert data to DataFrame once for all calculations
            df = self._convert_to_dataframe(ohlcv_data)
            
            # Calculate each indicator
            for config in indicators_config:
                indicator_type = config.get("type", "").lower()
                parameters = config.get("parameters", {})
                name = config.get("name", indicator_type)
                
                if not indicator_type:
                    logger.warning("Missing indicator type in configuration")
                    results[name] = {"error": "Missing indicator type"}
                    continue
                
                # Merge with default parameters if available
                if indicator_type in self._indicator_metadata:
                    default_params = self._indicator_metadata[indicator_type].get("default_params", {})
                    # Parameters from user override defaults
                    merged_params = {**default_params, **parameters}
                else:
                    merged_params = parameters
                
                # Validate parameters if enabled
                if self._validate_params:
                    is_valid, error = self.validate_parameters(indicator_type, merged_params)
                    if not is_valid:
                        logger.error(f"Invalid parameters for {indicator_type}: {error}")
                        results[name] = {"error": error}
                        continue
                
                # Check cache first if enabled
                cache_hit = False
                if self._cache_enabled:
                    cache_key = self._generate_cache_key(indicator_type, ohlcv_data, merged_params)
                    if cache_key in self._cache:
                        results[name] = self._cache[cache_key]
                        # Update cache order for LRU
                        self._cache_keys.remove(cache_key)
                        self._cache_keys.append(cache_key)
                        cache_hit = True
                
                if not cache_hit:
                    # Get the calculation function
                    indicator_func = self._get_indicator_function(indicator_type)
                    if indicator_func is None:
                        logger.error(f"Unknown indicator type: {indicator_type}")
                        results[name] = {"error": f"Unknown indicator type: {indicator_type}"}
                        continue
                    
                    try:
                        # Calculate indicator
                        result = indicator_func(df, merged_params)
                        
                        # Add indicator metadata
                        metadata = {
                            "indicator_type": indicator_type,
                            "parameters": merged_params,
                            "instrument": ohlcv_data.instrument,
                            "timeframe": ohlcv_data.timeframe,
                            "calculation_time": datetime.now().isoformat(),
                            "data_points": len(ohlcv_data.data),
                            "data_start": ohlcv_data.start_date.isoformat() if ohlcv_data.start_date else None,
                            "data_end": ohlcv_data.end_date.isoformat() if ohlcv_data.end_date else None
                        }
                        
                        # Add category if available
                        if indicator_type in self._indicator_metadata:
                            category = self._indicator_metadata[indicator_type].get("category")
                            if category:
                                metadata["category"] = category
                        
                        result["metadata"] = metadata
                        
                        results[name] = result
                        
                        # Cache the result if enabled
                        if self._cache_enabled:
                            cache_key = self._generate_cache_key(indicator_type, ohlcv_data, merged_params)
                            self._add_to_cache(cache_key, result)
                    
                    except Exception as e:
                        logger.error(f"Error calculating {indicator_type}: {e}")
                        results[name] = {"error": str(e)}
            
            return results
        
        except Exception as e:
            logger.error(f"Error in batch calculation: {e}")
            return {"error": str(e)}
    
    def clear_cache(self):
        """Clear the indicator calculation cache."""
        self._cache = {}
        self._cache_keys = []
        logger.info("Indicator calculation cache cleared")
    
    def _convert_to_dataframe(self, ohlcv_data: OHLCV) -> pd.DataFrame:
        """
        Convert OHLCV data to pandas DataFrame.
        
        Args:
            ohlcv_data: The OHLCV data
            
        Returns:
            pandas DataFrame with OHLCV data
        """
        # Extract data points as dictionaries
        data_dicts = [
            {
                "timestamp": p.timestamp,
                "open": float(p.open),
                "high": float(p.high),
                "low": float(p.low),
                "close": float(p.close),
                "volume": float(p.volume)
            }
            for p in ohlcv_data.data
        ]
        
        df = pd.DataFrame(data_dicts)
        
        # Set timestamp as index
        if len(df) > 0:
            df.set_index("timestamp", inplace=True)
            df.sort_index(inplace=True)
        
        return df
    
    def _optimize_pandas_operations(self):
        """Apply LRU caching to expensive pandas operations."""
        # Apply lru_cache to expensive pandas operations
        pd.Series.rolling = lru_cache(maxsize=32)(pd.Series.rolling)
        pd.Series.ewm = lru_cache(maxsize=32)(pd.Series.ewm)
        
    def get_available_indicators(self) -> Dict[str, Any]:
        """
        Get a list of all available indicators with metadata.
        
        Returns:
            Dictionary with indicator information organized by category
        """
        result = {}
        
        # Group indicators by category
        for indicator_type, metadata in self._indicator_metadata.items():
            category = metadata["category"]
            if category not in result:
                result[category] = []
                
            result[category].append({
                "type": indicator_type,
                "name": metadata["name"],
                "description": metadata["description"],
                "default_params": metadata["default_params"]
            })
            
        return result
    
    def validate_parameters(self, indicator_type: str, parameters: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate parameters for an indicator.
        
        Args:
            indicator_type: The type of indicator
            parameters: Parameters to validate
            
        Returns:
            Tuple with (is_valid, error_message)
        """
        if not self._validate_params:
            return True, None
            
        if indicator_type not in self._indicator_metadata:
            return False, f"Unknown indicator type: {indicator_type}"
            
        metadata = self._indicator_metadata[indicator_type]
        
        if "param_validation" not in metadata:
            return True, None
            
        validation_rules = metadata["param_validation"]
        
        # Check each parameter against its validation rules
        for param_name, rules in validation_rules.items():
            # If parameter is not provided, skip validation
            if param_name not in parameters:
                continue
                
            param_value = parameters[param_name]
            
            # Type validation
            if "type" in rules:
                expected_type = rules["type"]
                if isinstance(expected_type, tuple):
                    # Multiple allowed types
                    if not isinstance(param_value, expected_type):
                        type_names = [t.__name__ for t in expected_type]
                        return False, f"Parameter '{param_name}' should be one of these types: {', '.join(type_names)}"
                elif not isinstance(param_value, expected_type):
                    return False, f"Parameter '{param_name}' should be of type {expected_type.__name__}"
                
            # Min/max validation for numeric types
            if isinstance(param_value, (int, float)):
                if "min" in rules and param_value < rules["min"]:
                    return False, f"Parameter '{param_name}' should be >= {rules['min']}"
                if "max" in rules and param_value > rules["max"]:
                    return False, f"Parameter '{param_name}' should be <= {rules['max']}"
                    
            # Options validation for string types
            if isinstance(param_value, str) and "options" in rules:
                if param_value not in rules["options"]:
                    return False, f"Parameter '{param_name}' should be one of: {', '.join(rules['options'])}"
                    
        return True, None
            
    def preprocess_source_data(self, df: pd.DataFrame, source: str) -> pd.Series:
        """
        Preprocess source data for indicator calculation.
        
        Args:
            df: DataFrame with OHLCV data
            source: Source field to use
            
        Returns:
            Processed Series of source data
        """
        if source == "hlc3":
            # (High + Low + Close) / 3
            return (df["high"] + df["low"] + df["close"]) / 3
        elif source == "ohlc4":
            # (Open + High + Low + Close) / 4
            return (df["open"] + df["high"] + df["low"] + df["close"]) / 4
        elif source in df.columns:
            return df[source]
        else:
            raise ValueError(f"Invalid source: {source}")
    
    def _generate_cache_key(self, indicator_type: str, ohlcv_data: OHLCV,
                          parameters: Dict[str, Any]) -> str:
        """
        Generate a cache key for indicator calculation.
        
        Args:
            indicator_type: The type of indicator
            ohlcv_data: The OHLCV data
            parameters: Parameters for the indicator calculation
            
        Returns:
            Cache key string
        """
        # Create a unique identifier using indicator type, parameters, 
        # instrument, timeframe, and data range
        
        # Create a serializable copy of parameters
        serializable_params = {}
        for k, v in parameters.items():
            if isinstance(v, pd.Series):
                # Skip Series objects as they're not hashable
                continue
            elif isinstance(v, (int, float, str, bool, type(None))):
                serializable_params[k] = v
            else:
                # Convert other objects to string representation
                serializable_params[k] = str(v)
        
        key_data = {
            "type": indicator_type,
            "parameters": serializable_params,
            "instrument": ohlcv_data.instrument,
            "timeframe": ohlcv_data.timeframe,
            "start_date": ohlcv_data.start_date.isoformat() if ohlcv_data.start_date else None,
            "end_date": ohlcv_data.end_date.isoformat() if ohlcv_data.end_date else None,
            "data_points": len(ohlcv_data.data)
        }
        
        # Generate a hash of the key data
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _add_to_cache(self, key: str, value: Dict[str, Any]):
        """
        Add an indicator calculation to the cache.
        
        Args:
            key: The cache key
            value: The indicator calculation result
        """
        # If cache is full, remove the least recently used item
        if len(self._cache) >= self._max_cache_size and self._cache_keys:
            lru_key = self._cache_keys.pop(0)
            if lru_key in self._cache:
                del self._cache[lru_key]
        
        # Add new item to cache
        self._cache[key] = value
        self._cache_keys.append(key)
    
    def _get_indicator_function(self, indicator_type: str) -> Optional[Callable]:
        """
        Get the calculation function for an indicator type.
        
        Args:
            indicator_type: The type of indicator
            
        Returns:
            Callable function for calculating the indicator, or None if not supported
        """
        # Convert indicator_type to lowercase for case-insensitive matching
        indicator_type_lower = indicator_type.lower()
        
        # Use a simple string-based lookup map
        indicator_map = {
            # Trend indicators
            "sma": self._calculate_sma,
            "ema": self._calculate_ema,
            "wma": self._calculate_wma,
            "dema": self._calculate_dema,
            "tema": self._calculate_tema,
            "trix": self._calculate_trix,
            "adx": self._calculate_adx,
            "ichimoku": self._calculate_ichimoku,
            "supertrend": self._calculate_supertrend,
            
            # Momentum indicators
            "rsi": self._calculate_rsi,
            "stochastic": self._calculate_stochastic,
            "macd": self._calculate_macd,
            "mfi": self._calculate_mfi,
            "cci": self._calculate_cci,
            "roc": self._calculate_roc,
            
            # Volatility indicators
            "bollinger_bands": self._calculate_bollinger_bands,
            "atr": self._calculate_atr,
            "keltner_channel": self._calculate_keltner_channel,
            
            # Volume indicators
            "obv": self._calculate_obv,
            "vwap": self._calculate_vwap,
            "cmf": self._calculate_cmf,
            
            # Pattern indicators
            "engulfing": self._calculate_engulfing,
            "doji": self._calculate_doji,
        }
        
        return indicator_map.get(indicator_type_lower)
    
    # Indicator calculation functions using TA-Lib
    
    def _calculate_sma(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Simple Moving Average using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        source = parameters.get("source", "close")
        
        # Get source data
        source_data = self.preprocess_source_data(df, source)
        
        # Calculate SMA using TA-Lib
        sma = talib.SMA(source_data.values, timeperiod=period)
        
        # Convert to dictionary with timestamps as keys
        result_dict = {}
        for i, timestamp in enumerate(df.index):
            result_dict[str(timestamp)] = float(sma[i]) if not np.isnan(sma[i]) else float('nan')
        
        return {
            "values": result_dict,
            "info": {
                "description": f"Simple Moving Average ({period} periods)",
                "formula": f"SMA = sum(price) / {period}",
                "interpretation": "Trend following indicator that smooths price data"
            }
        }
    
    def _calculate_ema(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Exponential Moving Average using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        source = parameters.get("source", "close")
        
        # Get source data
        source_data = self.preprocess_source_data(df, source)
        
        # Calculate EMA using TA-Lib
        ema = talib.EMA(source_data.values, timeperiod=period)
        
        # Convert to dictionary with timestamps as keys
        result_dict = {}
        for i, timestamp in enumerate(df.index):
            result_dict[str(timestamp)] = float(ema[i]) if not np.isnan(ema[i]) else float('nan')
        
        return {
            "values": result_dict,
            "info": {
                "description": f"Exponential Moving Average ({period} periods)",
                "formula": f"EMA = (Price * (2 / ({period} + 1))) + (EMA[previous] * (1 - (2 / ({period} + 1))))",
                "interpretation": "Trend following indicator that gives more weight to recent prices"
            }
        }
    
    def _calculate_wma(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Weighted Moving Average using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        source = parameters.get("source", "close")
        
        # Get source data
        source_data = self.preprocess_source_data(df, source)
        
        # Calculate WMA using TA-Lib
        wma = talib.WMA(source_data.values, timeperiod=period)
        
        # Convert to dictionary with timestamps as keys
        result_dict = {}
        for i, timestamp in enumerate(df.index):
            result_dict[str(timestamp)] = float(wma[i]) if not np.isnan(wma[i]) else float('nan')
        
        return {
            "values": result_dict,
            "info": {
                "description": f"Weighted Moving Average ({period} periods)",
                "formula": "WMA = sum(price * weight) / sum(weights)",
                "interpretation": "Trend following indicator that assigns more weight to recent data"
            }
        }
    
    def _calculate_dema(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Double Exponential Moving Average using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        source = parameters.get("source", "close")
        
        # Get source data
        source_data = self.preprocess_source_data(df, source)
        
        # Calculate DEMA using TA-Lib
        dema = talib.DEMA(source_data.values, timeperiod=period)
        
        # Convert to dictionary with timestamps as keys
        result_dict = {}
        for i, timestamp in enumerate(df.index):
            result_dict[str(timestamp)] = float(dema[i]) if not np.isnan(dema[i]) else float('nan')
        
        return {
            "values": result_dict,
            "info": {
                "description": f"Double Exponential Moving Average ({period} periods)",
                "formula": f"DEMA = (2 * EMA(price, {period})) - EMA(EMA(price, {period}), {period})",
                "interpretation": "Trend following indicator with reduced lag compared to EMA"
            }
        }
    
    def _calculate_tema(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Triple Exponential Moving Average using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        source = parameters.get("source", "close")
        
        # Get source data
        source_data = self.preprocess_source_data(df, source)
        
        # Calculate TEMA using TA-Lib
        tema = talib.TEMA(source_data.values, timeperiod=period)
        
        # Convert to dictionary with timestamps as keys
        result_dict = {}
        for i, timestamp in enumerate(df.index):
            result_dict[str(timestamp)] = float(tema[i]) if not np.isnan(tema[i]) else float('nan')
        
        return {
            "values": result_dict,
            "info": {
                "description": f"Triple Exponential Moving Average ({period} periods)",
                "formula": "TEMA = 3 * EMA - 3 * EMA(EMA) + EMA(EMA(EMA))",
                "interpretation": "Trend following indicator with minimal lag"
            }
        }
    
    def _calculate_rsi(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Relative Strength Index using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        source = parameters.get("source", "close")
        
        # Get source data
        source_data = self.preprocess_source_data(df, source)
        
        # Calculate RSI using TA-Lib
        rsi = talib.RSI(source_data.values, timeperiod=period)
        
        # Convert to dictionary with timestamps as keys
        result_dict = {}
        for i, timestamp in enumerate(df.index):
            result_dict[str(timestamp)] = float(rsi[i]) if not np.isnan(rsi[i]) else float('nan')
        
        return {
            "values": result_dict,
            "info": {
                "description": f"Relative Strength Index ({period} periods)",
                "formula": "RSI = 100 - (100 / (1 + RS)), where RS = Average Gain / Average Loss",
                "interpretation": "Momentum oscillator that measures the speed and change of price movements",
                "typical_range": "0-100",
                "overbought": "70+",
                "oversold": "30-"
            }
        }
    
    def _calculate_stochastic(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Stochastic Oscillator using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        k_period = parameters.get("k_period", 14)
        d_period = parameters.get("d_period", 3)
        
        # Calculate Stochastic using TA-Lib
        # Note that TA-Lib uses fastk_period, slowk_period, and slowd_period
        # We map k_period to fastk_period and d_period to slowd_period with default slowk_period=1
        slowk, slowd = talib.STOCH(
            df["high"].values, 
            df["low"].values, 
            df["close"].values,
            fastk_period=k_period,
            slowk_period=1,
            slowk_matype=0,
            slowd_period=d_period,
            slowd_matype=0
        )
        
        # Convert to dictionaries with timestamps as keys
        k_dict = {}
        d_dict = {}
        for i, timestamp in enumerate(df.index):
            k_dict[str(timestamp)] = float(slowk[i]) if not np.isnan(slowk[i]) else float('nan')
            d_dict[str(timestamp)] = float(slowd[i]) if not np.isnan(slowd[i]) else float('nan')
        
        return {
            "values": {
                "k": k_dict,
                "d": d_dict
            },
            "info": {
                "description": f"Stochastic Oscillator (K:{k_period}, D:{d_period})",
                "formula": "%K = 100 * ((C - L{k_period}) / (H{k_period} - L{k_period}))\n%D = {d_period}-period SMA of %K",
                "interpretation": "Momentum indicator comparing closing price to price range over time",
                "typical_range": "0-100",
                "overbought": "80+",
                "oversold": "20-"
            }
        }
    
    def _calculate_macd(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Moving Average Convergence Divergence using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        fast_period = parameters.get("fast_period", 12)
        slow_period = parameters.get("slow_period", 26)
        signal_period = parameters.get("signal_period", 9)
        source = parameters.get("source", "close")
        
        # Get source data
        source_data = self.preprocess_source_data(df, source)
        
        # Calculate MACD using TA-Lib
        macd_line, signal_line, histogram = talib.MACD(
            source_data.values,
            fastperiod=fast_period,
            slowperiod=slow_period,
            signalperiod=signal_period
        )
        
        # Convert to dictionaries with timestamps as keys
        macd_dict = {}
        signal_dict = {}
        histogram_dict = {}
        for i, timestamp in enumerate(df.index):
            macd_dict[str(timestamp)] = float(macd_line[i]) if not np.isnan(macd_line[i]) else float('nan')
            signal_dict[str(timestamp)] = float(signal_line[i]) if not np.isnan(signal_line[i]) else float('nan')
            histogram_dict[str(timestamp)] = float(histogram[i]) if not np.isnan(histogram[i]) else float('nan')
        
        return {
            "values": {
                "macd": macd_dict,
                "signal": signal_dict,
                "histogram": histogram_dict
            },
            "info": {
                "description": f"MACD ({fast_period},{slow_period},{signal_period})",
                "formula": f"MACD Line = EMA({fast_period}) - EMA({slow_period})\nSignal Line = EMA({signal_period}) of MACD Line\nHistogram = MACD Line - Signal Line",
                "interpretation": "Trend-following momentum indicator showing relationship between two EMAs"
            }
        }
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Bollinger Bands using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 20)
        std_dev = parameters.get("std_dev", 2.0)
        source = parameters.get("source", "close")
        
        # Get source data
        source_data = self.preprocess_source_data(df, source)
        
        # Calculate Bollinger Bands using TA-Lib
        upper, middle, lower = talib.BBANDS(
            source_data.values,
            timeperiod=period,
            nbdevup=std_dev,
            nbdevdn=std_dev,
            matype=0  # Simple Moving Average
        )
        
        # Convert to dictionaries with timestamps as keys
        upper_dict = {}
        middle_dict = {}
        lower_dict = {}
        for i, timestamp in enumerate(df.index):
            upper_dict[str(timestamp)] = float(upper[i]) if not np.isnan(upper[i]) else float('nan')
            middle_dict[str(timestamp)] = float(middle[i]) if not np.isnan(middle[i]) else float('nan')
            lower_dict[str(timestamp)] = float(lower[i]) if not np.isnan(lower[i]) else float('nan')
        
        return {
            "values": {
                "upper": upper_dict,
                "middle": middle_dict,
                "lower": lower_dict
            },
            "info": {
                "description": f"Bollinger Bands ({period} periods, {std_dev} std dev)",
                "formula": f"Middle Band = {period}-period SMA\nUpper Band = Middle Band + ({std_dev} * StdDev)\nLower Band = Middle Band - ({std_dev} * StdDev)",
                "interpretation": "Volatility indicator that creates bands around a moving average"
            }
        }
    
    def _calculate_atr(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Average True Range using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        
        # Calculate ATR using TA-Lib
        atr = talib.ATR(
            df["high"].values,
            df["low"].values,
            df["close"].values,
            timeperiod=period
        )
        
        # Convert to dictionary with timestamps as keys
        result_dict = {}
        for i, timestamp in enumerate(df.index):
            result_dict[str(timestamp)] = float(atr[i]) if not np.isnan(atr[i]) else float('nan')
        
        return {
            "values": result_dict,
            "info": {
                "description": f"Average True Range ({period} periods)",
                "formula": "ATR = EMA of True Range, where True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))",
                "interpretation": "Volatility indicator showing average range of price movement"
            }
        }
    
    def _calculate_obv(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate On-Balance Volume using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        # Calculate OBV using TA-Lib
        obv = talib.OBV(df["close"].values, df["volume"].values)
        
        # Convert to dictionary with timestamps as keys
        result_dict = {}
        for i, timestamp in enumerate(df.index):
            result_dict[str(timestamp)] = float(obv[i]) if not np.isnan(obv[i]) else float('nan')
        
        return {
            "values": result_dict,
            "info": {
                "description": "On-Balance Volume",
                "formula": "OBV = OBV[prev] + volume (if close > close[prev]) or OBV[prev] - volume (if close < close[prev])",
                "interpretation": "Volume indicator that shows buying/selling pressure"
            }
        }
    
    def _calculate_adx(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Average Directional Index using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        
        # Calculate ADX using TA-Lib
        adx = talib.ADX(
            df["high"].values,
            df["low"].values,
            df["close"].values,
            timeperiod=period
        )
        
        # Calculate +DI and -DI
        plus_di = talib.PLUS_DI(
            df["high"].values,
            df["low"].values,
            df["close"].values,
            timeperiod=period
        )
        
        minus_di = talib.MINUS_DI(
            df["high"].values,
            df["low"].values,
            df["close"].values,
            timeperiod=period
        )
        
        # Convert to dictionaries with timestamps as keys
        adx_dict = {}
        plus_di_dict = {}
        minus_di_dict = {}
        for i, timestamp in enumerate(df.index):
            adx_dict[str(timestamp)] = float(adx[i]) if not np.isnan(adx[i]) else float('nan')
            plus_di_dict[str(timestamp)] = float(plus_di[i]) if not np.isnan(plus_di[i]) else float('nan')
            minus_di_dict[str(timestamp)] = float(minus_di[i]) if not np.isnan(minus_di[i]) else float('nan')
        
        return {
            "values": {
                "adx": adx_dict,
                "plus_di": plus_di_dict,
                "minus_di": minus_di_dict
            },
            "info": {
                "description": f"Average Directional Index ({period} periods)",
                "formula": "ADX = 100 * EMA((+DI - -DI) / (+DI + -DI))",
                "interpretation": "Trend strength indicator, values above 25 indicate strong trend"
            }
        }
    
    # Implement other indicators similarly...
    
    def _calculate_mfi(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Money Flow Index using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        
        # Calculate MFI using TA-Lib
        mfi = talib.MFI(
            df["high"].values,
            df["low"].values,
            df["close"].values,
            df["volume"].values,
            timeperiod=period
        )
        
        # Convert to dictionary with timestamps as keys
        result_dict = {}
        for i, timestamp in enumerate(df.index):
            result_dict[str(timestamp)] = float(mfi[i]) if not np.isnan(mfi[i]) else float('nan')
        
        return {
            "values": result_dict,
            "info": {
                "description": f"Money Flow Index ({period} periods)",
                "formula": "MFI = 100 - (100 / (1 + Money Flow Ratio))",
                "interpretation": "Momentum indicator that incorporates volume, similar to RSI",
                "typical_range": "0-100",
                "overbought": "80+",
                "oversold": "20-"
            }
        }
    
    def _calculate_cci(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Commodity Channel Index using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        
        # Calculate CCI using TA-Lib
        cci = talib.CCI(
            df["high"].values,
            df["low"].values,
            df["close"].values,
            timeperiod=period
        )
        
        # Convert to dictionary with timestamps as keys
        result_dict = {}
        for i, timestamp in enumerate(df.index):
            result_dict[str(timestamp)] = float(cci[i]) if not np.isnan(cci[i]) else float('nan')
        
        return {
            "values": result_dict,
            "info": {
                "description": f"Commodity Channel Index ({period} periods)",
                "formula": "CCI = (Typical Price - SMA of Typical Price) / (0.015 * Mean Deviation)",
                "interpretation": "Momentum oscillator to identify cyclical trends",
                "typical_range": "-100 to +100",
                "overbought": "+100",
                "oversold": "-100"
            }
        }
    
    def _calculate_roc(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Rate of Change using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 10)
        source = parameters.get("source", "close")
        
        # Get source data
        source_data = self.preprocess_source_data(df, source)
        
        # Calculate ROC using TA-Lib
        roc = talib.ROC(source_data.values, timeperiod=period)
        
        # Convert to dictionary with timestamps as keys
        result_dict = {}
        for i, timestamp in enumerate(df.index):
            result_dict[str(timestamp)] = float(roc[i]) if not np.isnan(roc[i]) else float('nan')
        
        return {
            "values": result_dict,
            "info": {
                "description": f"Rate of Change ({period} periods)",
                "formula": f"ROC = ((Price / Price {period} periods ago) - 1) * 100",
                "interpretation": "Momentum oscillator that measures the percentage change in price"
            }
        }
    
    # Additional indicators that weren't in our original implementation but are provided by TA-Lib
    
    def _calculate_vwap(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Volume-Weighted Average Price.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        # VWAP is not directly provided by TA-Lib, so we implement it manually
        # VWAP = ∑(Price * Volume) / ∑(Volume)
        
        # Calculate typical price
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        
        # Calculate VWAP
        cumulative_tp_vol = (typical_price * df["volume"]).cumsum()
        cumulative_vol = df["volume"].cumsum()
        vwap = cumulative_tp_vol / cumulative_vol
        
        # Convert to dictionary with timestamps as keys
        result_dict = {}
        for i, timestamp in enumerate(df.index):
            result_dict[str(timestamp)] = float(vwap.iloc[i]) if not pd.isna(vwap.iloc[i]) else float('nan')
        
        return {
            "values": result_dict,
            "info": {
                "description": "Volume-Weighted Average Price",
                "formula": "VWAP = ∑(Price * Volume) / ∑(Volume)",
                "interpretation": "Shows average price weighted by volume, often used as an intraday indicator"
            }
        }
    
    def _calculate_ichimoku(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Ichimoku Cloud indicators.
        
        TA-Lib doesn't have Ichimoku built-in, so we implement it manually.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        try:
            # Get parameters
            tenkan_period = parameters.get("tenkan_period", 9)
            kijun_period = parameters.get("kijun_period", 26)
            senkou_span_b_period = parameters.get("senkou_span_b_period", 52)
            displacement = parameters.get("displacement", 26)
            
            # Calculate components
            
            # Tenkan-sen (Conversion Line): (highest high + lowest low) / 2 for tenkan_period
            high_values = df["high"].rolling(window=tenkan_period).max()
            low_values = df["low"].rolling(window=tenkan_period).min()
            tenkan_sen = (high_values + low_values) / 2
            
            # Kijun-sen (Base Line): (highest high + lowest low) / 2 for kijun_period
            high_values = df["high"].rolling(window=kijun_period).max()
            low_values = df["low"].rolling(window=kijun_period).min()
            kijun_sen = (high_values + low_values) / 2
            
            # Senkou Span A (Leading Span A): (Tenkan-sen + Kijun-sen) / 2 displaced forward displacement periods
            senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
            
            # Senkou Span B (Leading Span B): (highest high + lowest low) / 2 for senkou_span_b_period, displaced forward displacement periods
            high_values = df["high"].rolling(window=senkou_span_b_period).max()
            low_values = df["low"].rolling(window=senkou_span_b_period).min()
            senkou_span_b = ((high_values + low_values) / 2).shift(displacement)
            
            # Chikou Span (Lagging Span): Current closing price displaced backward displacement periods
            chikou_span = df["close"].shift(-displacement)
            
            # Convert results to dictionaries
            result = {
                "values": {
                    "tenkan_sen": {},
                    "kijun_sen": {},
                    "senkou_span_a": {},
                    "senkou_span_b": {},
                    "chikou_span": {}
                }
            }
            
            for i, timestamp in enumerate(df.index):
                ts_str = str(timestamp)
                
                # Tenkan-sen
                if i >= tenkan_period - 1:
                    result["values"]["tenkan_sen"][ts_str] = float(tenkan_sen.iloc[i]) if not pd.isna(tenkan_sen.iloc[i]) else float('nan')
                else:
                    result["values"]["tenkan_sen"][ts_str] = float('nan')
                    
                # Kijun-sen
                if i >= kijun_period - 1:
                    result["values"]["kijun_sen"][ts_str] = float(kijun_sen.iloc[i]) if not pd.isna(kijun_sen.iloc[i]) else float('nan')
                else:
                    result["values"]["kijun_sen"][ts_str] = float('nan')
                    
                # Senkou Span A
                if i < len(senkou_span_a) and i >= kijun_period - 1:
                    result["values"]["senkou_span_a"][ts_str] = float(senkou_span_a.iloc[i]) if not pd.isna(senkou_span_a.iloc[i]) else float('nan')
                else:
                    result["values"]["senkou_span_a"][ts_str] = float('nan')
                    
                # Senkou Span B
                if i < len(senkou_span_b) and i >= senkou_span_b_period - 1:
                    result["values"]["senkou_span_b"][ts_str] = float(senkou_span_b.iloc[i]) if not pd.isna(senkou_span_b.iloc[i]) else float('nan')
                else:
                    result["values"]["senkou_span_b"][ts_str] = float('nan')
                    
                # Chikou Span
                if i < len(df.index) - displacement:
                    result["values"]["chikou_span"][ts_str] = float(chikou_span.iloc[i]) if not pd.isna(chikou_span.iloc[i]) else float('nan')
                else:
                    result["values"]["chikou_span"][ts_str] = float('nan')
            
            result["info"] = {
                "description": "Ichimoku Cloud",
                "formula": "Multiple components that work together to provide support/resistance, momentum, and trend direction",
                "interpretation": "Complex indicator showing multiple aspects of market conditions"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating Ichimoku indicator: {e}")
            return {
                "values": {
                    "tenkan_sen": {},
                    "kijun_sen": {},
                    "senkou_span_a": {},
                    "senkou_span_b": {},
                    "chikou_span": {}
                },
                "info": {
                    "description": "Ichimoku Cloud",
                    "formula": "Multiple components that work together to provide support/resistance, momentum, and trend direction",
                    "interpretation": "Complex indicator showing multiple aspects of market conditions"
                }
            }
    
    def _calculate_supertrend(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Supertrend indicator.
        
        Supertrend isn't provided by TA-Lib, so we implement it manually based on ATR from TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 10)
        multiplier = parameters.get("multiplier", 3.0)
        
        # Calculate ATR using TA-Lib
        atr = talib.ATR(
            df["high"].values,
            df["low"].values,
            df["close"].values,
            timeperiod=period
        )
        
        # Calculate basic upper and lower bands
        hl2 = (df["high"] + df["low"]) / 2
        basic_upper_band = hl2 + (multiplier * atr)
        basic_lower_band = hl2 - (multiplier * atr)
        
        # Initialize final bands and trend
        final_upper_band = np.zeros_like(atr)
        final_lower_band = np.zeros_like(atr)
        supertrend = np.zeros_like(atr)
        trend = np.zeros_like(atr)
        
        # Calculate Supertrend
        for i in range(1, len(df)):
            # Upper band
            if basic_upper_band[i] < final_upper_band[i-1] or df["close"].iloc[i-1] > final_upper_band[i-1]:
                final_upper_band[i] = basic_upper_band[i]
            else:
                final_upper_band[i] = final_upper_band[i-1]
                
            # Lower band
            if basic_lower_band[i] > final_lower_band[i-1] or df["close"].iloc[i-1] < final_lower_band[i-1]:
                final_lower_band[i] = basic_lower_band[i]
            else:
                final_lower_band[i] = final_lower_band[i-1]
                
            # Supertrend
            if supertrend[i-1] == final_upper_band[i-1] and df["close"].iloc[i] <= final_upper_band[i]:
                supertrend[i] = final_upper_band[i]
                trend[i] = -1  # Downtrend
            elif supertrend[i-1] == final_upper_band[i-1] and df["close"].iloc[i] > final_upper_band[i]:
                supertrend[i] = final_lower_band[i]
                trend[i] = 1  # Uptrend
            elif supertrend[i-1] == final_lower_band[i-1] and df["close"].iloc[i] >= final_lower_band[i]:
                supertrend[i] = final_lower_band[i]
                trend[i] = 1  # Uptrend
            elif supertrend[i-1] == final_lower_band[i-1] and df["close"].iloc[i] < final_lower_band[i]:
                supertrend[i] = final_upper_band[i]
                trend[i] = -1  # Downtrend
        
        # Convert to dictionaries with timestamps as keys
        supertrend_dict = {}
        trend_dict = {}
        for i, timestamp in enumerate(df.index):
            supertrend_dict[str(timestamp)] = float(supertrend[i]) if not np.isnan(supertrend[i]) else float('nan')
            trend_dict[str(timestamp)] = int(trend[i]) if not np.isnan(trend[i]) else 0
        
        return {
            "values": {
                "supertrend": supertrend_dict,
                "trend": trend_dict
            },
            "info": {
                "description": f"Supertrend ({period} periods, {multiplier}x multiplier)",
                "formula": "Based on ATR bands: Upper = (High+Low)/2 + (Multiplier * ATR), Lower = (High+Low)/2 - (Multiplier * ATR)",
                "interpretation": "Trend following indicator, trend=-1 for downtrend, trend=1 for uptrend"
            }
        }
    
    def _calculate_keltner_channel(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Keltner Channel using TA-Lib components.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 20)
        multiplier = parameters.get("multiplier", 2.0)
        
        # Calculate EMA (middle line) using TA-Lib
        middle = talib.EMA(df["close"].values, timeperiod=period)
        
        # Calculate ATR using TA-Lib
        atr = talib.ATR(
            df["high"].values,
            df["low"].values,
            df["close"].values,
            timeperiod=period
        )
        
        # Calculate upper and lower bands
        upper = middle + (multiplier * atr)
        lower = middle - (multiplier * atr)
        
        # Convert to dictionaries with timestamps as keys
        upper_dict = {}
        middle_dict = {}
        lower_dict = {}
        for i, timestamp in enumerate(df.index):
            upper_dict[str(timestamp)] = float(upper[i]) if not np.isnan(upper[i]) else float('nan')
            middle_dict[str(timestamp)] = float(middle[i]) if not np.isnan(middle[i]) else float('nan')
            lower_dict[str(timestamp)] = float(lower[i]) if not np.isnan(lower[i]) else float('nan')
        
        return {
            "values": {
                "upper": upper_dict,
                "middle": middle_dict,
                "lower": lower_dict
            },
            "info": {
                "description": f"Keltner Channel ({period} periods, {multiplier}x multiplier)",
                "formula": f"Middle Line = EMA({period})\nUpper Band = Middle Line + ({multiplier} * ATR({period}))\nLower Band = Middle Line - ({multiplier} * ATR({period}))",
                "interpretation": "Volatility-based indicator similar to Bollinger Bands but using ATR instead of standard deviation"
            }
        }
    
    def _calculate_cmf(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Chaikin Money Flow.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 20)
        
        # Calculate Money Flow Multiplier
        high = df["high"]
        low = df["low"]
        close = df["close"]
        volume = df["volume"]
        
        money_flow_multiplier = ((close - low) - (high - close)) / (high - low)
        money_flow_multiplier = money_flow_multiplier.replace([np.inf, -np.inf], 0)
        
        # Calculate Money Flow Volume
        money_flow_volume = money_flow_multiplier * volume
        
        # Calculate Chaikin Money Flow
        cmf = money_flow_volume.rolling(window=period).sum() / volume.rolling(window=period).sum()
        
        # Convert to dictionary with timestamps as keys
        result_dict = {}
        for i, timestamp in enumerate(df.index):
            result_dict[str(timestamp)] = float(cmf.iloc[i]) if not pd.isna(cmf.iloc[i]) else float('nan')
        
        return {
            "values": result_dict,
            "info": {
                "description": f"Chaikin Money Flow ({period} periods)",
                "formula": "CMF = Sum(Money Flow Volume) / Sum(Volume)",
                "interpretation": "Volume indicator that measures buying and selling pressure",
                "typical_range": "-1 to +1"
            }
        }
    
    def _calculate_trix(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate TRIX indicator using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        source = parameters.get("source", "close")
        
        # Get source data
        source_data = self.preprocess_source_data(df, source)
        
        # Calculate TRIX using TA-Lib
        trix = talib.TRIX(source_data.values, timeperiod=period)
        
        # Convert to dictionary with timestamps as keys
        result_dict = {}
        for i, timestamp in enumerate(df.index):
            result_dict[str(timestamp)] = float(trix[i]) if not np.isnan(trix[i]) else float('nan')
        
        return {
            "values": result_dict,
            "info": {
                "description": f"Triple Exponential Average Oscillator ({period} periods)",
                "formula": "TRIX = (EMA(EMA(EMA(price))) / EMA(EMA(EMA(price)[previous])) - 1) * 100",
                "interpretation": "Momentum oscillator that filters out small price movements",
                "typical_range": "Centered around 0"
            }
        }
    
    def _calculate_engulfing(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Bullish/Bearish Engulfing patterns using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        # Calculate Engulfing patterns using TA-Lib
        bullish = talib.CDLENGULFING(
            df["open"].values,
            df["high"].values,
            df["low"].values,
            df["close"].values
        )
        
        # TA-Lib returns 0 for no pattern, 100 for bullish engulfing, -100 for bearish engulfing
        # We'll convert this to a more readable format:
        # 1 for bullish engulfing, -1 for bearish engulfing, 0 for no pattern
        pattern = bullish / 100
        
        # Convert to dictionary with timestamps as keys
        result_dict = {}
        for i, timestamp in enumerate(df.index):
            result_dict[str(timestamp)] = int(pattern[i])
        
        return {
            "values": result_dict,
            "info": {
                "description": "Engulfing Candlestick Pattern",
                "formula": "Bullish: Current candle's body completely engulfs previous bearish candle's body\nBearish: Current candle's body completely engulfs previous bullish candle's body",
                "interpretation": "1=Bullish Engulfing, -1=Bearish Engulfing, 0=No Pattern"
            }
        }
    
    def _calculate_doji(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Doji candlestick pattern using TA-Lib.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        # Calculate Doji pattern using TA-Lib
        doji = talib.CDLDOJI(
            df["open"].values,
            df["high"].values,
            df["low"].values,
            df["close"].values
        )
        
        # TA-Lib returns 0 for no pattern, 100 for doji
        # Convert to binary: 1 for doji, 0 for no pattern
        pattern = doji / 100
        
        # Convert to dictionary with timestamps as keys
        result_dict = {}
        for i, timestamp in enumerate(df.index):
            result_dict[str(timestamp)] = int(pattern[i])
        
        return {
            "values": result_dict,
            "info": {
                "description": "Doji Candlestick Pattern",
                "formula": "Open price approximately equals Close price",
                "interpretation": "1=Doji pattern detected, 0=No pattern",
                "significance": "Indicates indecision in the market, often signals potential reversal when appears after extended trend"
            }
        }