"""
On-demand indicator calculation service.

This module provides services for calculating technical indicators on-demand
based on raw OHLCV data, with support for various indicator types and parameters.
It includes optimized calculation functions, parameter validation, and caching
for improved performance.
"""

import logging
import numpy as np
import pandas as pd
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
                "default_params": {"period": 20, "std_dev": 2, "source": "close"},
                "param_validation": {
                    "period": {"type": int, "min": 1, "max": 500},
                    "std_dev": {"type": float, "min": 0.1, "max": 10},
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
            shared_intermediates = {}
            calculation_order = self._optimize_calculation_order(indicators_config)
            
            # Convert data to DataFrame once for all calculations
            df = self._convert_to_dataframe(ohlcv_data)
            
            # Calculate each indicator in optimized order
            for config in calculation_order:
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
                        # Pass shared intermediate values if supported
                        result = indicator_func(df, merged_params)
                        
                        # Store potential intermediate values for reuse
                        self._store_intermediate_values(shared_intermediates, indicator_type, merged_params, result, df)
                        
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
            
            # Add batch metadata
            batch_metadata = {
                "batch_size": len(indicators_config),
                "successful_calculations": len([r for r in results.values() if "error" not in r]),
                "batch_calculation_time": datetime.now().isoformat(),
            }
            
            return {
                "results": results,
                "batch_metadata": batch_metadata
            }
        
        except Exception as e:
            logger.error(f"Error in batch calculation: {e}")
            return {"error": str(e)}
    
    def _optimize_calculation_order(self, indicators_config: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Optimize the order of indicator calculations to maximize intermediate result reuse.
        
        Args:
            indicators_config: List of indicator configurations
            
        Returns:
            Reordered list of indicator configurations
        """
        # Define dependency graph for indicators
        # Some indicators can reuse calculations from others
        dependencies = {
            "ema": [],  # No dependencies
            "sma": [],  # No dependencies
            "wma": [],  # No dependencies
            "dema": ["ema"],  # Depends on EMA
            "tema": ["ema"],  # Depends on EMA
            "macd": ["ema"],  # Depends on EMA
            "bollinger_bands": ["sma"],  # Depends on SMA
            "rsi": [],  # No dependencies
            "stochastic": [],  # No dependencies
            "atr": [],  # No dependencies
            "adx": ["atr"],  # Depends on ATR
            "supertrend": ["atr"],  # Depends on ATR
            "trix": ["ema"],  # Depends on EMA
        }
        
        # Count the number of indicators that depend on each type
        dependency_count = {}
        for config in indicators_config:
            indicator_type = config.get("type", "").lower()
            dependency_count[indicator_type] = dependency_count.get(indicator_type, 0) + 1
            
        # Assign priority based on dependencies
        # Higher priority = calculate earlier
        prioritized_config = []
        for config in indicators_config:
            indicator_type = config.get("type", "").lower()
            
            # Calculate priority based on:
            # 1. How many other indicators depend on this one
            # 2. How many dependencies this indicator has
            dependency_priority = sum([dependency_count.get(dep, 0) for dep in dependencies.get(indicator_type, [])])
            priority = dependency_priority
            
            prioritized_config.append((config, priority))
            
        # Sort by priority (highest first)
        prioritized_config.sort(key=lambda x: x[1], reverse=True)
        
        # Return just the configurations
        return [config for config, _ in prioritized_config]
    
    def _store_intermediate_values(self, shared_intermediates: Dict[str, Any], 
                                 indicator_type: str, parameters: Dict[str, Any], 
                                 result: Dict[str, Any], df: pd.DataFrame):
        """
        Store intermediate calculation values that can be reused.
        
        Args:
            shared_intermediates: Dictionary to store intermediate values
            indicator_type: Type of the calculated indicator
            parameters: Parameters used for calculation
            result: Result of the calculation
            df: DataFrame with OHLCV data
        """
        # Store ATR values
        if indicator_type == "atr":
            period = parameters.get("period", 14)
            key = f"atr_{period}"
            if "values" in result:
                # Make a copy to avoid modifying the original
                shared_intermediates[key] = result["values"].copy()
        
        # Store EMA values
        elif indicator_type == "ema":
            period = parameters.get("period", 14)
            source = parameters.get("source", "close")
            key = f"ema_{period}_{source}"
            if "values" in result:
                # Make a copy to avoid modifying the original
                shared_intermediates[key] = result["values"].copy()
        
        # Store SMA values
        elif indicator_type == "sma":
            period = parameters.get("period", 14)
            source = parameters.get("source", "close")
            key = f"sma_{period}_{source}"
            if "values" in result:
                # Make a copy to avoid modifying the original
                shared_intermediates[key] = result["values"].copy()
    
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
        
        # Create DataFrame
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
                if not isinstance(param_value, expected_type):
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
            "data_points": ohlcv_data.count
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
    
    # Indicator calculation functions
    
    def _calculate_sma(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Simple Moving Average.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        source = parameters.get("source", "close")
        
        if source not in df.columns:
            raise ValueError(f"Source column '{source}' not found in data")
        
        # Manual SMA calculation to avoid Series hashability issues
        source_data = df[source].values  # NumPy array
        result_dict = {}
        
        # Calculate SMA for each period
        for i in range(len(df)):
            timestamp = str(df.index[i])
            
            if i < period - 1:
                # Not enough data points yet, include NaN values for initial periods
                # to match pandas behavior and test expectations
                result_dict[timestamp] = float('nan')
            else:
                # Calculate average of window
                window = source_data[max(0, i - period + 1):i + 1]
                sma_value = sum(window) / len(window)
                result_dict[timestamp] = float(sma_value)
        
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
        Calculate Exponential Moving Average.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        source = parameters.get("source", "close")
        
        if source not in df.columns:
            raise ValueError(f"Source column '{source}' not found in data")
        
        # Manual EMA calculation to avoid Series hashability issues
        source_data = df[source].values  # NumPy array
        result_dict = {}
        
        # EMA = Price * k + EMA(previous) * (1 - k)
        # where k = 2 / (period + 1)
        k = 2 / (period + 1)
        
        # Initialize EMA with SMA for the first period
        ema_value = None
        
        # Calculate EMA for each period
        for i in range(len(df)):
            timestamp = str(df.index[i])
            
            if i < period - 1:
                # Not enough data points yet, include NaN values for initial periods
                # to match pandas behavior and test expectations
                result_dict[timestamp] = float('nan')
                continue
                
            current_price = source_data[i]
            
            if ema_value is None:
                # First value is simple average
                ema_value = sum(source_data[i-period+1:i+1]) / period
            else:
                # EMA formula
                ema_value = current_price * k + ema_value * (1 - k)
            
            # Store result with timestamp as key
            result_dict[timestamp] = float(ema_value)
        
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
        Calculate Weighted Moving Average.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        source = parameters.get("source", "close")
        
        if source not in df.columns:
            raise ValueError(f"Source column '{source}' not found in data")
        
        # Manual WMA calculation to avoid Series hashability issues
        source_data = df[source].values  # NumPy array
        result_dict = {}
        
        # Define weights (more weight to recent data)
        weights = np.arange(1, period + 1)
        weights_sum = weights.sum()
        
        # Calculate WMA for each period
        for i in range(len(df)):
            timestamp = str(df.index[i])
            
            if i < period - 1:
                # Not enough data points yet, include NaN values for initial periods
                result_dict[timestamp] = float('nan')
            else:
                # Get window and calculate weighted average
                window = source_data[i-period+1:i+1]
                # Multiply each price by its weight and sum
                wma_value = np.sum(window * weights) / weights_sum
                result_dict[timestamp] = float(wma_value)
        
        return {
            "values": result_dict,
            "info": {
                "description": f"Weighted Moving Average ({period} periods)",
                "formula": "WMA = sum(price * weight) / sum(weights)",
                "interpretation": "Trend following indicator that assigns more weight to recent data"
            }
        }
    
    def _calculate_rsi(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Relative Strength Index.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        source = parameters.get("source", "close")
        
        if source not in df.columns:
            raise ValueError(f"Source column '{source}' not found in data")
        
        # Manual RSI calculation to avoid Series hashability issues
        source_data = df[source].values  # NumPy array
        result_dict = {}
        
        # First pass: calculate price changes
        deltas = [0]
        for i in range(1, len(source_data)):
            deltas.append(source_data[i] - source_data[i-1])
        
        # Second pass: calculate gains and losses
        gains = []
        losses = []
        for delta in deltas:
            if delta > 0:
                gains.append(delta)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(delta))
        
        # Calculate RSI for each period
        for i in range(period, len(df)):
            # Calculate average gain and loss
            avg_gain = sum(gains[i-period+1:i+1]) / period
            avg_loss = sum(losses[i-period+1:i+1]) / period
            
            # Calculate RS and RSI
            if avg_loss == 0:
                rsi_value = 100
            else:
                rs = avg_gain / avg_loss
                rsi_value = 100 - (100 / (1 + rs))
            
            # Store result with timestamp as key
            timestamp = str(df.index[i])
            result_dict[timestamp] = float(rsi_value)
        
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
        Calculate Stochastic Oscillator.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        k_period = parameters.get("k_period", 14)
        d_period = parameters.get("d_period", 3)
        
        # Manual Stochastic Oscillator calculation to avoid Series hashability issues
        close_data = df['close'].values
        high_data = df['high'].values
        low_data = df['low'].values
        
        k_dict = {}
        d_dict = {}
        k_values = []
        
        # Calculate %K for each period
        for i in range(len(df)):
            timestamp = str(df.index[i])
            
            if i < k_period - 1:
                # Not enough data points yet
                k_dict[timestamp] = float('nan')
                d_dict[timestamp] = float('nan')
                continue
            
            # Get window for calculation
            window_low = low_data[i-k_period+1:i+1]
            window_high = high_data[i-k_period+1:i+1]
            
            # Calculate %K: 100 * (close - lowest low) / (highest high - lowest low)
            low_min = np.min(window_low)
            high_max = np.max(window_high)
            
            # Handle potential division by zero
            if high_max == low_min:
                k_value = 100.0  # If range is zero, stochastic is 100%
            else:
                k_value = 100 * ((close_data[i] - low_min) / (high_max - low_min))
            
            k_dict[timestamp] = float(k_value)
            k_values.append(k_value)
            
            # Calculate %D: d_period-SMA of %K
            if i >= k_period + d_period - 2:
                d_value = sum(k_values[-d_period:]) / d_period
                d_dict[timestamp] = float(d_value)
            else:
                d_dict[timestamp] = float('nan')
        
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
        Calculate Moving Average Convergence Divergence.
        
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
        
        if source not in df.columns:
            raise ValueError(f"Source column '{source}' not found in data")
        
        # Manual MACD calculation to avoid Series hashability issues
        source_data = df[source].values  # NumPy array
        macd_dict = {}
        signal_dict = {}
        histogram_dict = {}
        
        # Calculate fast EMA and slow EMA
        k_fast = 2 / (fast_period + 1)
        k_slow = 2 / (slow_period + 1)
        k_signal = 2 / (signal_period + 1)
        
        fast_ema_value = None
        slow_ema_value = None
        
        # First pass: calculate fast and slow EMAs and MACD line
        macd_values = []  # Store MACD values for signal line calculation
        
        for i in range(len(df)):
            timestamp = str(df.index[i])
            current_price = source_data[i]
            
            # Calculate fast EMA
            if i < fast_period - 1:
                # Not enough data points yet
                continue
            elif fast_ema_value is None:
                # First value is simple average
                fast_ema_value = sum(source_data[:fast_period]) / fast_period
            else:
                # EMA formula
                fast_ema_value = current_price * k_fast + fast_ema_value * (1 - k_fast)
            
            # Calculate slow EMA
            if i < slow_period - 1:
                # Not enough data points yet
                continue
            elif slow_ema_value is None:
                # First value is simple average
                slow_ema_value = sum(source_data[:slow_period]) / slow_period
            else:
                # EMA formula
                slow_ema_value = current_price * k_slow + slow_ema_value * (1 - k_slow)
            
            # Calculate MACD line
            if i >= slow_period - 1:
                macd_value = fast_ema_value - slow_ema_value
                macd_dict[timestamp] = float(macd_value)
                macd_values.append(macd_value)
            else:
                macd_dict[timestamp] = float('nan')
        
        # Second pass: calculate signal line and histogram
        signal_value = None
        
        for i in range(slow_period - 1, len(df)):
            timestamp = str(df.index[i])
            idx = i - (slow_period - 1)  # Index into macd_values
            
            # Calculate signal line (EMA of MACD)
            if idx < signal_period - 1:
                signal_dict[timestamp] = float('nan')
                histogram_dict[timestamp] = float('nan')
                continue
            elif signal_value is None:
                # First value is simple average
                signal_value = sum(macd_values[:signal_period]) / signal_period
            else:
                # EMA formula
                signal_value = macd_values[idx] * k_signal + signal_value * (1 - k_signal)
            
            signal_dict[timestamp] = float(signal_value)
            
            # Calculate histogram
            histogram_dict[timestamp] = float(macd_dict[timestamp] - signal_value)
        
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
        Calculate Bollinger Bands.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 20)
        std_dev = float(parameters.get("std_dev", 2))
        source = parameters.get("source", "close")
        
        if source not in df.columns:
            raise ValueError(f"Source column '{source}' not found in data")
        
        # Manual Bollinger Bands calculation to avoid Series hashability issues
        source_data = df[source].values  # NumPy array
        upper_dict = {}
        middle_dict = {}
        lower_dict = {}
        
        # Calculate for each period
        for i in range(period-1, len(df)):
            # Get window
            window = source_data[i-period+1:i+1]
            
            # Calculate middle band (SMA)
            middle = sum(window) / period
            
            # Calculate standard deviation
            squared_diff = [(x - middle) ** 2 for x in window]
            variance = sum(squared_diff) / period
            std = variance ** 0.5
            
            # Calculate upper and lower bands
            upper = middle + (std * std_dev)
            lower = middle - (std * std_dev)
            
            # Store results with timestamp as key
            timestamp = str(df.index[i])
            upper_dict[timestamp] = float(upper)
            middle_dict[timestamp] = float(middle)
            lower_dict[timestamp] = float(lower)
        
        return {
            "values": {
                "upper": upper_dict,
                "middle": middle_dict,
                "lower": lower_dict
            },
            "info": {
                "description": f"Bollinger Bands ({period},{std_dev})",
                "formula": f"Middle Band = SMA({period})\nUpper Band = SMA({period}) + ({std_dev} * StdDev)\nLower Band = SMA({period}) - ({std_dev} * StdDev)",
                "interpretation": "Volatility indicator that creates bands around a moving average"
            }
        }
    
    def _calculate_atr(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Average True Range.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        
        # Calculate True Range
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # Calculate ATR
        atr = true_range.rolling(window=period).mean()
        
        # Convert Series to dictionary with string keys
        values_dict = {str(idx): val for idx, val in atr.to_dict().items()}
        
        return {
            "values": values_dict,
            "info": {
                "description": f"Average True Range ({period} periods)",
                "formula": f"TR = max(high-low, abs(high-prev_close), abs(low-prev_close))\nATR = SMA({period}) of TR",
                "interpretation": "Volatility indicator showing average range of price movement"
            }
        }
    
    def _calculate_obv(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate On-Balance Volume.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        # Calculate price change direction
        price_change = df['close'].diff()
        
        # Create volume with direction
        volume_direction = pd.Series(0, index=df.index)
        volume_direction[price_change > 0] = df['volume'][price_change > 0]
        volume_direction[price_change < 0] = -df['volume'][price_change < 0]
        
        # Calculate OBV
        obv = volume_direction.cumsum()
        
        # Convert Series to dictionary with string keys
        values_dict = {str(idx): val for idx, val in obv.to_dict().items()}
        
        return {
            "values": values_dict,
            "info": {
                "description": "On-Balance Volume",
                "formula": "OBV += volume when close > prev_close\nOBV -= volume when close < prev_close",
                "interpretation": "Volume indicator that shows buying/selling pressure by adding volume on up days and subtracting it on down days"
            }
        }
    
    def _calculate_vwap(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Volume-Weighted Average Price.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        # Calculate typical price
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        
        # Calculate volume * typical price
        vol_tp = typical_price * df['volume']
        
        # Calculate VWAP
        vol_cumsum = df['volume'].cumsum()
        vol_tp_cumsum = vol_tp.cumsum()
        
        vwap = vol_tp_cumsum / vol_cumsum
        
        # Convert Series to dictionary with string keys
        values_dict = {str(idx): val for idx, val in vwap.to_dict().items()}
        
        return {
            "values": values_dict,
            "info": {
                "description": "Volume-Weighted Average Price",
                "formula": "VWAP = ∑(Typical Price * Volume) / ∑(Volume)",
                "interpretation": "Shows average price weighted by volume, often used as a benchmark by institutional traders"
            }
        }
    
    def _calculate_adx(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Average Directional Index.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        
        # Calculate +DM, -DM
        plus_dm = df['high'].diff()
        minus_dm = df['low'].diff(-1).abs()
        
        plus_dm[plus_dm < 0] = 0
        plus_dm[(df['high'].shift() >= df['high']) | (df['low'].shift() <= df['low'])] = 0
        
        minus_dm[minus_dm < 0] = 0
        minus_dm[(df['low'].shift() <= df['low']) | (df['high'].shift() >= df['high'])] = 0
        
        # Calculate TR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # Calculate smoothed values
        tr14 = tr.rolling(window=period).sum()
        plus_dm14 = plus_dm.rolling(window=period).sum()
        minus_dm14 = minus_dm.rolling(window=period).sum()
        
        # Calculate +DI, -DI
        plus_di = 100 * (plus_dm14 / tr14)
        minus_di = 100 * (minus_dm14 / tr14)
        
        # Calculate DX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        
        # Calculate ADX
        adx = dx.rolling(window=period).mean()
        
        return {
            "values": {
                "adx": adx.to_dict(),
                "plus_di": plus_di.to_dict(),
                "minus_di": minus_di.to_dict()
            },
            "info": {
                "description": f"Average Directional Index ({period} periods)",
                "formula": "ADX = SMA(DX, period) where DX = 100 * abs(+DI - -DI) / (+DI + -DI)",
                "interpretation": "Trend strength indicator (ADX > 25 indicates strong trend)",
                "typical_range": "0-100"
            }
        }
    
    def _calculate_ichimoku(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Ichimoku Cloud.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        tenkan_period = parameters.get("tenkan_period", 9)
        kijun_period = parameters.get("kijun_period", 26)
        senkou_span_b_period = parameters.get("senkou_span_b_period", 52)
        displacement = parameters.get("displacement", 26)
        
        # Calculate Tenkan-sen (Conversion Line)
        tenkan_high = df['high'].rolling(window=tenkan_period).max()
        tenkan_low = df['low'].rolling(window=tenkan_period).min()
        tenkan_sen = (tenkan_high + tenkan_low) / 2
        
        # Calculate Kijun-sen (Base Line)
        kijun_high = df['high'].rolling(window=kijun_period).max()
        kijun_low = df['low'].rolling(window=kijun_period).min()
        kijun_sen = (kijun_high + kijun_low) / 2
        
        # Calculate Senkou Span A (Leading Span A)
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)
        
        # Calculate Senkou Span B (Leading Span B)
        senkou_high = df['high'].rolling(window=senkou_span_b_period).max()
        senkou_low = df['low'].rolling(window=senkou_span_b_period).min()
        senkou_span_b = ((senkou_high + senkou_low) / 2).shift(displacement)
        
        # Calculate Chikou Span (Lagging Span)
        chikou_span = df['close'].shift(-displacement)
        
        return {
            "values": {
                "tenkan_sen": tenkan_sen.to_dict(),
                "kijun_sen": kijun_sen.to_dict(),
                "senkou_span_a": senkou_span_a.to_dict(),
                "senkou_span_b": senkou_span_b.to_dict(),
                "chikou_span": chikou_span.to_dict()
            },
            "info": {
                "description": f"Ichimoku Cloud ({tenkan_period},{kijun_period},{senkou_span_b_period},{displacement})",
                "interpretation": "Comprehensive indicator showing support/resistance, momentum, and trend direction",
                "components": {
                    "tenkan_sen": "Conversion Line - short-term trend",
                    "kijun_sen": "Base Line - medium-term trend",
                    "senkou_span_a": "Leading Span A - first cloud boundary",
                    "senkou_span_b": "Leading Span B - second cloud boundary",
                    "chikou_span": "Lagging Span - used for confirmation"
                }
            }
        }
    
    def _calculate_dema(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Double Exponential Moving Average.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        source = parameters.get("source", "close")
        
        if source not in df.columns:
            raise ValueError(f"Source column '{source}' not found in data")
        
        # Manual DEMA calculation to avoid Series hashability issues
        source_data = df[source].values  # NumPy array
        result_dict = {}
        
        # Calculate EMA1 first (similar to _calculate_ema method)
        ema1_values = {}
        ema_value = None
        k = 2 / (period + 1)
        
        for i in range(len(df)):
            timestamp = str(df.index[i])
            
            if i < period - 1:
                # Not enough data points for EMA1 yet
                continue
                
            current_price = source_data[i]
            
            if ema_value is None:
                # First value is simple average
                ema_value = sum(source_data[:period]) / period
            else:
                # EMA formula
                ema_value = current_price * k + ema_value * (1 - k)
            
            # Store EMA1 value
            ema1_values[i] = ema_value
            
        # Calculate EMA2 (EMA of EMA1)
        ema2_values = {}
        ema2_value = None
        
        for i in range(period - 1, len(df)):
            if i < 2 * period - 2:
                # Not enough EMA1 values for EMA2 yet
                continue
                
            if ema2_value is None:
                # First EMA2 value is average of first 'period' EMA1 values
                ema2_value = sum([ema1_values[j] for j in range(period - 1, 2 * period - 1)]) / period
            else:
                # EMA2 formula
                ema2_value = ema1_values[i] * k + ema2_value * (1 - k)
                
            # Calculate DEMA and store with timestamp
            timestamp = str(df.index[i])
            dema_value = 2 * ema1_values[i] - ema2_value
            result_dict[timestamp] = float(dema_value)
        
        return {
            "values": result_dict,
            "info": {
                "description": f"Double Exponential Moving Average ({period} periods)",
                "formula": f"DEMA = 2 * EMA(Price, {period}) - EMA(EMA(Price, {period}), {period})",
                "interpretation": "Trend following indicator with reduced lag compared to EMA"
            }
        }
    
    def _calculate_tema(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Triple Exponential Moving Average.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        source = parameters.get("source", "close")
        
        if source not in df.columns:
            raise ValueError(f"Source column '{source}' not found in data")
        
        # Manual TEMA calculation to avoid Series hashability issues
        source_data = df[source].values  # NumPy array
        result_dict = {}
        
        # For TEMA, we need triple-smoothed EMA, which requires more data points
        # Add NaN values for periods without enough data
        for i in range(len(df)):
            timestamp = str(df.index[i])
            # TEMA requires at least 3*period-2 data points
            if i < 3*period-2:
                result_dict[timestamp] = float('nan')
                continue
                
            # Calculate EMA1
            ema1 = self._calculate_single_ema(source_data[i-3*period+2:i+1], period)
            
            # Calculate EMA2 (EMA of EMA1)
            ema_data = []
            for j in range(period):
                ema_data.append(self._calculate_single_ema(source_data[i-3*period+2+j:i-period+1+j], period))
            ema2 = self._calculate_single_ema(np.array(ema_data), period)
            
            # Calculate EMA3 (EMA of EMA2)
            ema2_data = []
            for j in range(period):
                ema1_data = []
                for k in range(period):
                    ema1_data.append(self._calculate_single_ema(source_data[i-3*period+2+j+k:i-period+1+j+k], period))
                ema2_data.append(self._calculate_single_ema(np.array(ema1_data), period))
            ema3 = self._calculate_single_ema(np.array(ema2_data), period)
            
            # Calculate TEMA = 3 * EMA1 - 3 * EMA2 + EMA3
            tema_value = 3 * ema1 - 3 * ema2 + ema3
            result_dict[timestamp] = float(tema_value)
        
        return {
            "values": result_dict,
            "info": {
                "description": f"Triple Exponential Moving Average ({period} periods)",
                "formula": f"TEMA = 3 * EMA1 - 3 * EMA2 + EMA3",
                "interpretation": "Trend following indicator with minimal lag"
            }
        }
        
    def _calculate_single_ema(self, data: np.ndarray, period: int) -> float:
        """
        Calculate a single EMA value for an array of data.
        Helper function for calculating EMA components in other indicators.
        
        Args:
            data: NumPy array of price data
            period: EMA period
            
        Returns:
            EMA value as float
        """
        if len(data) < period:
            return float('nan')
            
        # If exactly enough data for SMA, return simple average
        if len(data) == period:
            return float(np.mean(data[-period:]))
            
        # Otherwise calculate EMA with smoothing factor
        k = 2 / (period + 1)
        
        # Start with SMA for first period
        ema = np.mean(data[:period])
        
        # Calculate EMA for remaining data
        for i in range(period, len(data)):
            ema = data[i] * k + ema * (1 - k)
            
        return float(ema)
    
    def _calculate_trix(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Triple Exponential Average Oscillator (TRIX).
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        signal_period = parameters.get("signal_period", 9)
        source = parameters.get("source", "close")
        
        # Get source data
        price = self.preprocess_source_data(df, source)
        
        # Calculate first EMA
        ema1 = price.ewm(span=period, adjust=False).mean()
        
        # Calculate EMA of first EMA
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        
        # Calculate EMA of second EMA
        ema3 = ema2.ewm(span=period, adjust=False).mean()
        
        # Calculate percent rate of change of EMA3
        trix = ema3.pct_change(1) * 100
        
        # Calculate signal line
        signal = trix.ewm(span=signal_period, adjust=False).mean()
        
        # Calculate histogram
        histogram = trix - signal
        
        # Convert Series to dictionary with string keys
        trix_dict = {str(idx): val for idx, val in trix.to_dict().items()}
        signal_dict = {str(idx): val for idx, val in signal.to_dict().items()}
        histogram_dict = {str(idx): val for idx, val in histogram.to_dict().items()}
        
        return {
            "values": {
                "trix": trix_dict,
                "signal": signal_dict,
                "histogram": histogram_dict
            },
            "info": {
                "description": f"Triple Exponential Average ({period} periods, {signal_period} signal)",
                "formula": f"TRIX = 1-period % change of triple smoothed EMA",
                "interpretation": "Momentum oscillator showing rate of change of triple-smoothed moving average",
                "typical_range": "Centered at 0",
                "signals": "Positive: bullish, Negative: bearish, Zero crossovers: possible trend changes"
            }
        }
    
    def _calculate_supertrend(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Supertrend indicator.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 10)
        multiplier = parameters.get("multiplier", 3)
        
        # Calculate ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        # Calculate basic upper and lower bands
        hl2 = (df['high'] + df['low']) / 2
        
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)
        
        # Initialize Supertrend columns
        supertrend = pd.Series(0.0, index=df.index)
        trend = pd.Series(1, index=df.index)  # 1 = uptrend, -1 = downtrend
        
        # Calculate Supertrend
        for i in range(1, len(df)):
            if df['close'].iloc[i] > upper_band.iloc[i-1]:
                trend.iloc[i] = 1
            elif df['close'].iloc[i] < lower_band.iloc[i-1]:
                trend.iloc[i] = -1
            else:
                trend.iloc[i] = trend.iloc[i-1]
                
                if trend.iloc[i] == 1 and lower_band.iloc[i] < lower_band.iloc[i-1]:
                    lower_band.iloc[i] = lower_band.iloc[i-1]
                if trend.iloc[i] == -1 and upper_band.iloc[i] > upper_band.iloc[i-1]:
                    upper_band.iloc[i] = upper_band.iloc[i-1]
            
            if trend.iloc[i] == 1:
                supertrend.iloc[i] = lower_band.iloc[i]
            else:
                supertrend.iloc[i] = upper_band.iloc[i]
        
        # Convert Series to dictionary with string keys
        supertrend_dict = {str(idx): val for idx, val in supertrend.to_dict().items()}
        upper_dict = {str(idx): val for idx, val in upper_band.to_dict().items()}
        lower_dict = {str(idx): val for idx, val in lower_band.to_dict().items()}
        trend_dict = {str(idx): val for idx, val in trend.to_dict().items()}
        
        return {
            "values": {
                "supertrend": supertrend_dict,
                "upper_band": upper_dict,
                "lower_band": lower_dict,
                "trend": trend_dict
            },
            "info": {
                "description": f"Supertrend ({period} periods, {multiplier}x multiplier)",
                "formula": "Complex calculation based on ATR and price",
                "interpretation": "Trend-following indicator with clear buy/sell signals",
                "signals": "Price above Supertrend: uptrend (buy), Price below Supertrend: downtrend (sell)"
            }
        }
    
    def _calculate_mfi(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Money Flow Index.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 14)
        
        # Calculate typical price
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        
        # Calculate raw money flow
        raw_money_flow = typical_price * df['volume']
        
        # Get money flow direction
        direction = np.where(typical_price > typical_price.shift(1), 1, -1)
        
        # Separate positive and negative money flow
        positive_flow = pd.Series(np.where(direction > 0, raw_money_flow, 0), index=df.index)
        negative_flow = pd.Series(np.where(direction < 0, raw_money_flow, 0), index=df.index)
        
        # Sum positive and negative money flow over the period
        positive_sum = positive_flow.rolling(window=period).sum()
        negative_sum = negative_flow.rolling(window=period).sum()
        
        # Calculate money flow ratio and MFI
        money_flow_ratio = np.where(negative_sum != 0, positive_sum / negative_sum, 100)
        mfi = 100 - (100 / (1 + money_flow_ratio))
        
        mfi_series = pd.Series(mfi, index=df.index)
        
        # Convert Series to dictionary with string keys
        values_dict = {str(idx): val for idx, val in mfi_series.to_dict().items()}
        
        return {
            "values": values_dict,
            "info": {
                "description": f"Money Flow Index ({period} periods)",
                "formula": "MFI = 100 - (100 / (1 + Money Flow Ratio))",
                "interpretation": "Volume-weighted RSI, measuring buying/selling pressure",
                "typical_range": "0-100",
                "overbought": "80+",
                "oversold": "20-"
            }
        }
    
    def _calculate_cci(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Commodity Channel Index.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 20)
        constant = parameters.get("constant", 0.015)
        
        # Calculate typical price
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        
        # Calculate SMA of typical price
        sma_tp = typical_price.rolling(window=period).mean()
        
        # Calculate mean deviation
        mean_deviation = np.abs(typical_price - sma_tp).rolling(window=period).mean()
        
        # Calculate CCI
        cci = (typical_price - sma_tp) / (constant * mean_deviation)
        
        # Convert Series to dictionary with string keys
        values_dict = {str(idx): val for idx, val in cci.to_dict().items()}
        
        return {
            "values": values_dict,
            "info": {
                "description": f"Commodity Channel Index ({period} periods)",
                "formula": "CCI = (TP - SMA(TP)) / (constant * Mean Deviation)",
                "interpretation": "Momentum oscillator for identifying cyclical trends",
                "typical_range": "±100",
                "overbought": "100+",
                "oversold": "-100-"
            }
        }
    
    def _calculate_roc(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Rate of Change.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        period = parameters.get("period", 12)
        source = parameters.get("source", "close")
        
        # Get source data
        price = self.preprocess_source_data(df, source)
        
        # Calculate ROC
        roc = ((price / price.shift(period)) - 1) * 100
        
        # Convert Series to dictionary with string keys
        values_dict = {str(idx): val for idx, val in roc.to_dict().items()}
        
        return {
            "values": values_dict,
            "info": {
                "description": f"Rate of Change ({period} periods)",
                "formula": f"ROC = ((Price / Price(t-{period})) - 1) * 100",
                "interpretation": "Momentum oscillator showing percentage price change",
                "typical_range": "Centered at 0",
                "signals": "Positive: bullish, Negative: bearish, Zero crossovers: possible trend changes"
            }
        }
    
    def _calculate_keltner_channel(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Keltner Channel.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        ema_period = parameters.get("ema_period", 20)
        atr_period = parameters.get("atr_period", 10)
        multiplier = parameters.get("multiplier", 2)
        source = parameters.get("source", "close")
        
        # Get source data
        price = self.preprocess_source_data(df, source)
        
        # Calculate the middle band (EMA)
        middle_band = price.ewm(span=ema_period, adjust=False).mean()
        
        # Calculate True Range
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=atr_period).mean()
        
        # Calculate upper and lower bands
        upper_band = middle_band + (multiplier * atr)
        lower_band = middle_band - (multiplier * atr)
        
        return {
            "values": {
                "upper": upper_band.to_dict(),
                "middle": middle_band.to_dict(),
                "lower": lower_band.to_dict()
            },
            "info": {
                "description": f"Keltner Channel (EMA: {ema_period}, ATR: {atr_period}, Mult: {multiplier})",
                "formula": f"Middle = EMA({ema_period}), Upper/Lower = Middle ± {multiplier} * ATR({atr_period})",
                "interpretation": "Volatility-based bands using ATR instead of standard deviation",
                "signals": "Price above upper band: overbought, Price below lower band: oversold"
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
        high_low = df['high'] - df['low']
        close_low = df['close'] - df['low']
        high_close = df['high'] - df['close']
        
        # Avoid division by zero
        high_low = high_low.replace(0, np.nan)
        
        money_flow_multiplier = ((close_low - high_close) / high_low).fillna(0)
        
        # Calculate Money Flow Volume
        money_flow_volume = money_flow_multiplier * df['volume']
        
        # Calculate Chaikin Money Flow
        cmf = money_flow_volume.rolling(window=period).sum() / df['volume'].rolling(window=period).sum()
        
        # Convert Series to dictionary with string keys
        values_dict = {str(idx): val for idx, val in cmf.to_dict().items()}
        
        return {
            "values": values_dict,
            "info": {
                "description": f"Chaikin Money Flow ({period} periods)",
                "formula": f"CMF = Sum(MFV, {period}) / Sum(Volume, {period})",
                "interpretation": "Volume-weighted indicator of buying/selling pressure",
                "typical_range": "-1 to +1",
                "signals": "Positive: buying pressure, Negative: selling pressure"
            }
        }
    
    def _calculate_engulfing(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect bullish and bearish engulfing patterns.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        # Create empty series for results
        bullish_engulfing = pd.Series(0, index=df.index)
        bearish_engulfing = pd.Series(0, index=df.index)
        
        # Calculate body sizes
        body_sizes = abs(df['close'] - df['open'])
        
        # Detect bullish engulfing patterns
        for i in range(1, len(df)):
            if (df['close'].iloc[i-1] < df['open'].iloc[i-1] and  # Previous day is bearish
                df['close'].iloc[i] > df['open'].iloc[i] and  # Current day is bullish
                df['close'].iloc[i] > df['open'].iloc[i-1] and  # Current close is above previous open
                df['open'].iloc[i] < df['close'].iloc[i-1] and  # Current open is below previous close
                body_sizes.iloc[i] > body_sizes.iloc[i-1]):  # Current body is larger
                bullish_engulfing.iloc[i] = 1
        
        # Detect bearish engulfing patterns
        for i in range(1, len(df)):
            if (df['close'].iloc[i-1] > df['open'].iloc[i-1] and  # Previous day is bullish
                df['close'].iloc[i] < df['open'].iloc[i] and  # Current day is bearish
                df['close'].iloc[i] < df['open'].iloc[i-1] and  # Current close is below previous open
                df['open'].iloc[i] > df['close'].iloc[i-1] and  # Current open is above previous close
                body_sizes.iloc[i] > body_sizes.iloc[i-1]):  # Current body is larger
                bearish_engulfing.iloc[i] = 1
        
        return {
            "values": {
                "bullish_engulfing": bullish_engulfing.to_dict(),
                "bearish_engulfing": bearish_engulfing.to_dict()
            },
            "info": {
                "description": "Engulfing Candlestick Pattern",
                "interpretation": "Pattern showing potential reversal signals",
                "signals": {
                    "bullish_engulfing": "Bullish reversal pattern after downtrend",
                    "bearish_engulfing": "Bearish reversal pattern after uptrend"
                }
            }
        }
    
    def _calculate_doji(self, df: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect doji candlestick patterns.
        
        Args:
            df: DataFrame with OHLCV data
            parameters: Parameters for calculation
            
        Returns:
            Dict with indicator values and metadata
        """
        doji_threshold = parameters.get("doji_threshold", 0.1)  # % of candle range
        
        # Calculate body size as percentage of full range
        full_range = df['high'] - df['low']
        body_size = abs(df['close'] - df['open'])
        body_percent = body_size / full_range
        
        # Identify doji patterns
        doji = (body_percent < doji_threshold).astype(int)
        
        return {
            "values": doji.to_dict(),
            "info": {
                "description": f"Doji Pattern (threshold: {doji_threshold})",
                "interpretation": "Candlestick with very small body, indicating indecision",
                "signals": "Potential for reversal, especially after strong trend"
            }
        }