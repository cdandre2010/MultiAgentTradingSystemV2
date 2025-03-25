"""
Unit tests for the IndicatorService module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.services.indicators import IndicatorService
from src.models.market_data import OHLCV, OHLCVPoint


@pytest.fixture
def sample_ohlcv_data():
    """
    Generate sample OHLCV data for testing.
    
    Returns a combination of trending and oscillating price data
    to properly test various indicator types.
    """
    # Create sample data with 60 data points
    base_time = datetime(2023, 1, 1)
    data = []
    
    # Generate price data with a trend and some oscillation
    for i in range(60):
        # Add trend component
        trend = i * 0.5
        
        # Add oscillation component (sine wave)
        oscillation = 5 * np.sin(i / 5)
        
        # Combine trend and oscillation for realistic price movement
        price = 100 + trend + oscillation
        
        # Vary the high-low range
        high_low_range = 2 + abs(oscillation) / 2
        
        timestamp = base_time + timedelta(hours=i)
        data.append(OHLCVPoint(
            timestamp=timestamp,
            open=price - 0.5,
            high=price + high_low_range,
            low=price - high_low_range,
            close=price,
            volume=1000 + 200 * abs(oscillation)  # Volume correlates with volatility
        ))
    
    return OHLCV(
        instrument="AAPL",
        timeframe="1h",
        source="test",
        data=data
    )


class TestIndicatorService:
    """Tests for the IndicatorService class."""
    
    def test_initialization(self):
        """Test service initialization."""
        service = IndicatorService()
        assert service._cache_enabled is True
        assert service._max_cache_size == 100
        assert service._cache == {}
        assert service._cache_keys == []
        
        service = IndicatorService(cache_enabled=False, max_cache_size=50)
        assert service._cache_enabled is False
        assert service._max_cache_size == 50
    
    def test_convert_to_dataframe(self, sample_ohlcv_data):
        """Test conversion of OHLCV data to pandas DataFrame."""
        service = IndicatorService()
        df = service._convert_to_dataframe(sample_ohlcv_data)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(sample_ohlcv_data.data)
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert df.index.name == "timestamp"
    
    def test_moving_averages(self, sample_ohlcv_data):
        """Test calculation of moving average indicators."""
        service = IndicatorService()
        
        # Test SMA
        sma_result = service.calculate_indicator("sma", sample_ohlcv_data, {"period": 10})
        assert "values" in sma_result
        assert "info" in sma_result
        assert len(sma_result["values"]) == len(sample_ohlcv_data.data)
        
        # Test EMA
        ema_result = service.calculate_indicator("ema", sample_ohlcv_data, {"period": 10})
        assert "values" in ema_result
        assert "info" in ema_result
        assert len(ema_result["values"]) == len(sample_ohlcv_data.data)
        
        # Test WMA
        wma_result = service.calculate_indicator("wma", sample_ohlcv_data, {"period": 10})
        assert "values" in wma_result
        assert "info" in wma_result
        assert len(wma_result["values"]) == len(sample_ohlcv_data.data)
        
        # Check calculation correctness for SMA - manually calculate to avoid Series hashability issues
        df = service._convert_to_dataframe(sample_ohlcv_data)
        close_data = df["close"].values
        timestamps = [str(idx) for idx in df.index]
        expected_sma = {}
        
        # Calculate expected SMA manually
        period = 10
        for i in range(len(close_data)):
            timestamp = timestamps[i]
            if i < period - 1:
                expected_sma[timestamp] = float('nan')
            else:
                window = close_data[i - period + 1:i + 1]
                sma_value = sum(window) / period
                expected_sma[timestamp] = float(sma_value)
                
        actual_sma = sma_result["values"]
        
        # Compare SMA values (allow small floating point differences)
        for k in expected_sma:
            if pd.isna(expected_sma[k]):
                assert k not in actual_sma or pd.isna(actual_sma[k])
            else:
                assert abs(expected_sma[k] - actual_sma[k]) < 1e-10
    
    def test_oscillators(self, sample_ohlcv_data):
        """Test calculation of oscillator indicators."""
        service = IndicatorService()
        
        # Test RSI
        rsi_result = service.calculate_indicator("rsi", sample_ohlcv_data, {"period": 14})
        assert "values" in rsi_result
        assert "info" in rsi_result
        
        # Test Stochastic
        stoch_result = service.calculate_indicator("stochastic", sample_ohlcv_data, {"k_period": 14, "d_period": 3})
        assert "values" in stoch_result
        assert "k" in stoch_result["values"]
        assert "d" in stoch_result["values"]
        
        # Test MACD
        macd_result = service.calculate_indicator("macd", sample_ohlcv_data, {"fast_period": 12, "slow_period": 26, "signal_period": 9})
        assert "values" in macd_result
        assert "macd" in macd_result["values"]
        assert "signal" in macd_result["values"]
        assert "histogram" in macd_result["values"]
    
    def test_volatility_indicators(self, sample_ohlcv_data):
        """Test calculation of volatility indicators."""
        service = IndicatorService()
        
        # Test Bollinger Bands
        bb_result = service.calculate_indicator("bollinger_bands", sample_ohlcv_data, {"period": 20, "std_dev": 2.0})
        assert "values" in bb_result
        assert "upper" in bb_result["values"]
        assert "middle" in bb_result["values"]
        assert "lower" in bb_result["values"]
        
        # Test ATR
        atr_result = service.calculate_indicator("atr", sample_ohlcv_data, {"period": 14})
        assert "values" in atr_result
        assert "info" in atr_result
    
    def test_volume_indicators(self, sample_ohlcv_data):
        """Test calculation of volume indicators."""
        service = IndicatorService()
        
        # Test OBV
        obv_result = service.calculate_indicator("obv", sample_ohlcv_data, {})
        assert "values" in obv_result
        assert "info" in obv_result
        
        # Test VWAP
        vwap_result = service.calculate_indicator("vwap", sample_ohlcv_data, {})
        assert "values" in vwap_result
        assert "info" in vwap_result
    
    def test_trend_indicators(self, sample_ohlcv_data):
        """Test calculation of trend indicators."""
        service = IndicatorService()
        
        # Test ADX
        adx_result = service.calculate_indicator("adx", sample_ohlcv_data, {"period": 14})
        assert "values" in adx_result
        assert "adx" in adx_result["values"]
        assert "plus_di" in adx_result["values"]
        assert "minus_di" in adx_result["values"]
        
        # Test Ichimoku
        ichimoku_result = service.calculate_indicator("ichimoku", sample_ohlcv_data, {})
        assert "values" in ichimoku_result
        assert "tenkan_sen" in ichimoku_result["values"]
        assert "kijun_sen" in ichimoku_result["values"]
        assert "senkou_span_a" in ichimoku_result["values"]
        assert "senkou_span_b" in ichimoku_result["values"]
        assert "chikou_span" in ichimoku_result["values"]
    
    def test_calculate_multiple_indicators(self, sample_ohlcv_data):
        """Test calculation of multiple indicators at once."""
        service = IndicatorService()
        
        indicators_config = [
            {"type": "sma", "parameters": {"period": 10}, "name": "SMA10"},
            {"type": "rsi", "parameters": {"period": 14}, "name": "RSI"},
            {"type": "bollinger_bands", "parameters": {"period": 20}, "name": "BB"}
        ]
        
        results = service.calculate_multiple_indicators(sample_ohlcv_data, indicators_config)
        
        assert "SMA10" in results
        assert "RSI" in results
        assert "BB" in results
        assert "values" in results["SMA10"]
        assert "values" in results["RSI"]
        assert "values" in results["BB"]
        assert "metadata" in results["SMA10"]
    
    def test_caching(self, sample_ohlcv_data):
        """Test that indicator calculations are cached properly."""
        service = IndicatorService(cache_enabled=True, max_cache_size=10)
        
        # Calculate indicator
        service.calculate_indicator("sma", sample_ohlcv_data, {"period": 10})
        
        # Check that cache contains the result
        assert len(service._cache) == 1
        assert len(service._cache_keys) == 1
        
        # Calculate same indicator again (should use cache)
        with patch.object(service, '_calculate_sma') as mock_calculate:
            service.calculate_indicator("sma", sample_ohlcv_data, {"period": 10})
            # Function should not be called again
            mock_calculate.assert_not_called()
        
        # Calculate different indicator (different parameters)
        service.calculate_indicator("sma", sample_ohlcv_data, {"period": 20})
        
        # Check that cache contains both results
        assert len(service._cache) == 2
        assert len(service._cache_keys) == 2
        
        # Clear cache
        service.clear_cache()
        
        # Check that cache is empty
        assert len(service._cache) == 0
        assert len(service._cache_keys) == 0
    
    def test_cache_limit(self, sample_ohlcv_data):
        """Test that cache size is limited properly."""
        service = IndicatorService(cache_enabled=True, max_cache_size=3)
        
        # Fill cache with 4 different calculations
        for i in range(4):
            period = 10 + i
            # Calculate indicator
            service.calculate_indicator("sma", sample_ohlcv_data, {"period": period})
        
        # Cache should only contain 3 items (the most recent)
        assert len(service._cache) == 3
        assert len(service._cache_keys) == 3
        
        # Test a few more calculations to ensure cache management works consistently
        for i in range(3):
            period = 20 + i
            service.calculate_indicator("sma", sample_ohlcv_data, {"period": period})
        
        # Cache should still contain only 3 items
        assert len(service._cache) == 3
        assert len(service._cache_keys) == 3
    
    def test_error_handling(self, sample_ohlcv_data):
        """Test error handling in indicator calculations."""
        service = IndicatorService()
        
        # Test unknown indicator
        result = service.calculate_indicator("unknown_indicator", sample_ohlcv_data, {})
        assert "error" in result
        
        # Test missing source column
        result = service.calculate_indicator("sma", sample_ohlcv_data, {"source": "nonexistent_column"})
        assert "error" in result
        
        # Test with invalid parameters - validation catches this now
        result = service.calculate_indicator("sma", sample_ohlcv_data, {"period": "not_a_number"})
        assert "error" in result
    
    def test_indicator_info(self, sample_ohlcv_data):
        """Test that indicator results include proper metadata and info."""
        service = IndicatorService()
        
        result = service.calculate_indicator("rsi", sample_ohlcv_data, {"period": 14})
        
        assert "info" in result
        assert "description" in result["info"]
        assert "formula" in result["info"]
        assert "interpretation" in result["info"]
        assert "typical_range" in result["info"]
        
        assert "metadata" in result
        assert "indicator_type" in result["metadata"]
        assert "parameters" in result["metadata"]
        assert "instrument" in result["metadata"]
        assert "timeframe" in result["metadata"]
        assert "data_points" in result["metadata"]