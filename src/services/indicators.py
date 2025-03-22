"""
On-demand indicator calculation service.

This module provides services for calculating technical indicators on-demand
based on raw OHLCV data, with support for various indicator types and parameters.
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Callable
import hashlib
import json

from ..models.market_data import OHLCV, OHLCVPoint

logger = logging.getLogger(__name__)


class IndicatorService:
    """
    Service for on-demand calculation of technical indicators.
    
    This service provides methods for calculating various technical indicators
    based on raw OHLCV data, with support for parameter customization.
    """
    
    def __init__(self, cache_enabled: bool = True, max_cache_size: int = 100):
        """
        Initialize the service.
        
        Args:
            cache_enabled: Whether to enable in-memory caching
            max_cache_size: Maximum number of cached calculations
        """
        self._cache_enabled = cache_enabled
        self._max_cache_size = max_cache_size
        self._cache = {}
        self._cache_keys = []  # Used for LRU cache management
    
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
        # Check cache first if enabled
        if self._cache_enabled:
            cache_key = self._generate_cache_key(indicator_type, ohlcv_data, parameters)
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
        
        try:
            result = indicator_func(df, parameters)
            
            # Add indicator metadata
            result["metadata"] = {
                "indicator_type": indicator_type,
                "parameters": parameters,
                "instrument": ohlcv_data.instrument,
                "timeframe": ohlcv_data.timeframe,
                "calculation_time": datetime.now().isoformat(),
                "data_points": len(ohlcv_data.data),
                "data_start": ohlcv_data.start_date.isoformat() if ohlcv_data.start_date else None,
                "data_end": ohlcv_data.end_date.isoformat() if ohlcv_data.end_date else None
            }
            
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
        
        Args:
            ohlcv_data: The OHLCV data
            indicators_config: List of indicator configurations
            
        Returns:
            Dict containing all calculated indicators
        """
        results = {}
        df = self._convert_to_dataframe(ohlcv_data)  # Convert once for all calculations
        
        for config in indicators_config:
            indicator_type = config.get("type")
            parameters = config.get("parameters", {})
            name = config.get("name", indicator_type)
            
            if not indicator_type:
                logger.warning("Missing indicator type in configuration")
                continue
            
            # Check cache first if enabled
            cache_hit = False
            if self._cache_enabled:
                cache_key = self._generate_cache_key(indicator_type, ohlcv_data, parameters)
                if cache_key in self._cache:
                    results[name] = self._cache[cache_key]
                    # Update cache order for LRU
                    self._cache_keys.remove(cache_key)
                    self._cache_keys.append(cache_key)
                    cache_hit = True
            
            if not cache_hit:
                # Calculate the indicator
                indicator_func = self._get_indicator_function(indicator_type)
                if indicator_func is None:
                    logger.error(f"Unknown indicator type: {indicator_type}")
                    results[name] = {"error": f"Unknown indicator type: {indicator_type}"}
                    continue
                
                try:
                    result = indicator_func(df, parameters)
                    
                    # Add indicator metadata
                    result["metadata"] = {
                        "indicator_type": indicator_type,
                        "parameters": parameters,
                        "instrument": ohlcv_data.instrument,
                        "timeframe": ohlcv_data.timeframe,
                        "calculation_time": datetime.now().isoformat(),
                        "data_points": len(ohlcv_data.data),
                        "data_start": ohlcv_data.start_date.isoformat() if ohlcv_data.start_date else None,
                        "data_end": ohlcv_data.end_date.isoformat() if ohlcv_data.end_date else None
                    }
                    
                    results[name] = result
                    
                    # Cache the result if enabled
                    if self._cache_enabled:
                        cache_key = self._generate_cache_key(indicator_type, ohlcv_data, parameters)
                        self._add_to_cache(cache_key, result)
                        
                except Exception as e:
                    logger.error(f"Error calculating {indicator_type}: {e}")
                    results[name] = {"error": str(e)}
        
        return results
    
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
                "open": p.open,
                "high": p.high,
                "low": p.low,
                "close": p.close,
                "volume": p.volume
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
    
    def _get_indicator_function(self, indicator_type: str) -> Optional[Callable]:
        """
        Get the calculation function for an indicator type.
        
        Args:
            indicator_type: The type of indicator
            
        Returns:
            Callable function for calculating the indicator, or None if not supported
        """
        indicator_map = {
            # Moving Averages
            "sma": self._calculate_sma,
            "ema": self._calculate_ema,
            "wma": self._calculate_wma,
            
            # Oscillators
            "rsi": self._calculate_rsi,
            "stochastic": self._calculate_stochastic,
            "macd": self._calculate_macd,
            
            # Volatility
            "bollinger_bands": self._calculate_bollinger_bands,
            "atr": self._calculate_atr,
            
            # Volume
            "obv": self._calculate_obv,
            "vwap": self._calculate_vwap,
            
            # Trend
            "adx": self._calculate_adx,
            "ichimoku": self._calculate_ichimoku,
        }
        
        return indicator_map.get(indicator_type.lower())
    
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
        key_data = {
            "type": indicator_type,
            "parameters": parameters,
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
        
        values = df[source].rolling(window=period).mean()
        
        return {
            "values": values.to_dict(),
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
        
        values = df[source].ewm(span=period, adjust=False).mean()
        
        return {
            "values": values.to_dict(),
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
        
        weights = np.arange(1, period + 1)
        values = df[source].rolling(window=period).apply(
            lambda x: np.sum(weights * x) / weights.sum(), raw=True
        )
        
        return {
            "values": values.to_dict(),
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
        
        # Calculate price changes
        delta = df[source].diff()
        
        # Create gain (up) and loss (down) DataFrames
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate average gain and loss
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Handle edge cases
        rsi = rsi.replace([np.inf, -np.inf], np.nan).fillna(50)
        
        return {
            "values": rsi.to_dict(),
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
        
        # Calculate %K
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        
        k = 100 * ((df['close'] - low_min) / (high_max - low_min))
        
        # Calculate %D
        d = k.rolling(window=d_period).mean()
        
        return {
            "values": {
                "k": k.to_dict(),
                "d": d.to_dict()
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
        
        # Calculate EMAs
        fast_ema = df[source].ewm(span=fast_period, adjust=False).mean()
        slow_ema = df[source].ewm(span=slow_period, adjust=False).mean()
        
        # Calculate MACD line
        macd_line = fast_ema - slow_ema
        
        # Calculate signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        return {
            "values": {
                "macd": macd_line.to_dict(),
                "signal": signal_line.to_dict(),
                "histogram": histogram.to_dict()
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
        std_dev = parameters.get("std_dev", 2)
        source = parameters.get("source", "close")
        
        if source not in df.columns:
            raise ValueError(f"Source column '{source}' not found in data")
        
        # Calculate middle band (SMA)
        middle_band = df[source].rolling(window=period).mean()
        
        # Calculate standard deviation
        std = df[source].rolling(window=period).std()
        
        # Calculate upper and lower bands
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        
        return {
            "values": {
                "upper": upper_band.to_dict(),
                "middle": middle_band.to_dict(),
                "lower": lower_band.to_dict()
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
        
        return {
            "values": atr.to_dict(),
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
        
        return {
            "values": obv.to_dict(),
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
        
        return {
            "values": vwap.to_dict(),
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