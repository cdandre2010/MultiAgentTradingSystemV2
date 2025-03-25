#!/usr/bin/env python3
"""
Test script for the Indicator Calculation Service.

This script tests the functionality of the IndicatorService by calculating 
various indicators and measuring performance metrics.
"""

import sys
import os
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add parent directory to path to import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.indicators import IndicatorService, IndicatorType, IndicatorCategory
from src.models.market_data import OHLCV, OHLCVPoint


def generate_sample_data(days=100, volatility=1.0, trend=0.1):
    """Generate sample OHLCV data for testing."""
    base_time = datetime.now() - timedelta(days=days)
    data = []
    
    # Start price
    price = 100
    
    for i in range(days):
        # Add trend component
        trend_component = i * trend
        
        # Add random component (with specified volatility)
        random_component = np.random.normal(0, volatility)
        
        # Calculate price
        current_price = price + trend_component + random_component
        
        # Calculate OHLCV values
        timestamp = base_time + timedelta(days=i)
        high = current_price + abs(random_component) * 0.5
        low = current_price - abs(random_component) * 0.5
        open_price = current_price - random_component * 0.2
        close_price = current_price
        volume = 1000 + random_component * 100
        
        # Create data point
        data.append(OHLCVPoint(
            timestamp=timestamp,
            open=open_price,
            high=high,
            low=low,
            close=close_price,
            volume=max(100, volume)  # Ensure volume is positive
        ))
    
    return OHLCV(
        instrument="TEST",
        timeframe="1d",
        source="test",
        data=data
    )


def test_indicator_service():
    """Test the IndicatorService functionality."""
    print("Testing IndicatorService...")
    
    # Generate sample data
    ohlcv_data = generate_sample_data(days=200, volatility=2.0, trend=0.05)
    print(f"Generated {len(ohlcv_data.data)} days of sample data")
    
    # Create indicator service
    service = IndicatorService(cache_enabled=True, optimize=True, validate_params=True)
    
    # Test individual indicator calculation
    print("\nTesting individual indicator calculation...")
    indicators_to_test = [
        ("sma", {"period": 20}),
        ("ema", {"period": 20}),
        ("rsi", {"period": 14}),
        ("bollinger_bands", {"period": 20, "std_dev": 2.0}),
        ("macd", {"fast_period": 12, "slow_period": 26, "signal_period": 9}),
    ]
    
    for indicator_type, params in indicators_to_test:
        start_time = time.time()
        result = service.calculate_indicator(indicator_type, ohlcv_data, params)
        elapsed = time.time() - start_time
        
        if "error" in result:
            print(f"Error calculating {indicator_type}: {result['error']}")
        else:
            print(f"Calculated {indicator_type} in {elapsed:.4f} seconds")
    
    # Test batch calculation
    print("\nTesting batch indicator calculation...")
    indicators_config = [
        {"type": "sma", "parameters": {"period": 20}, "name": "SMA20"},
        {"type": "ema", "parameters": {"period": 20}, "name": "EMA20"},
        {"type": "rsi", "parameters": {"period": 14}, "name": "RSI14"},
        {"type": "bollinger_bands", "parameters": {"period": 20, "std_dev": 2.0}, "name": "BB20"},
        {"type": "macd", "parameters": {"fast_period": 12, "slow_period": 26, "signal_period": 9}, "name": "MACD"}
    ]
    
    start_time = time.time()
    batch_result = service.calculate_multiple_indicators(ohlcv_data, indicators_config)
    elapsed = time.time() - start_time
    
    print(f"Calculated {len(indicators_config)} indicators in batch in {elapsed:.4f} seconds")
    
    # Test cache performance
    print("\nTesting cache performance...")
    
    # First calculation (not cached)
    start_time = time.time()
    service.calculate_indicator("bollinger_bands", ohlcv_data, {"period": 20, "std_dev": 2.0})
    first_time = time.time() - start_time
    
    # Second calculation (should be cached)
    start_time = time.time()
    service.calculate_indicator("bollinger_bands", ohlcv_data, {"period": 20, "std_dev": 2.0})
    cached_time = time.time() - start_time
    
    print(f"First calculation: {first_time:.4f} seconds")
    print(f"Cached calculation: {cached_time:.4f} seconds")
    if cached_time > 0:
        print(f"Speedup: {first_time/cached_time:.1f}x")
    else:
        print("Cached calculation was too fast to measure")


if __name__ == "__main__":
    test_indicator_service()