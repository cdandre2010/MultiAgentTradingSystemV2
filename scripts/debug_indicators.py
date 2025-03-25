#!/usr/bin/env python3
"""
Debug script for the Indicator Calculation Service.
This script tests the most basic functionality of the service.
"""

import sys
import os

# Add parent directory to path to import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.indicators import IndicatorService
from src.models.market_data import OHLCV, OHLCVPoint
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def generate_sample_data(days=10):
    """Generate sample OHLCV data for testing."""
    base_time = datetime.now() - timedelta(days=days)
    data = []
    
    # Start price
    price = 100
    
    for i in range(days):
        # Simple price
        current_price = 100 + i
        
        # Calculate OHLCV values
        timestamp = base_time + timedelta(days=i)
        high = current_price + 1
        low = current_price - 1
        open_price = current_price - 0.5
        close_price = current_price
        volume = 1000
        
        # Create data point
        data.append(OHLCVPoint(
            timestamp=timestamp,
            open=float(open_price),
            high=float(high),
            low=float(low),
            close=float(close_price),
            volume=float(volume)
        ))
    
    return OHLCV(
        instrument="TEST",
        timeframe="1d",
        source="test",
        data=data
    )

def test_basic_indicators():
    """Test basic indicator calculations."""
    # Generate simple data
    ohlcv_data = generate_sample_data(days=10)
    print(f"Generated {len(ohlcv_data.data)} days of sample data")
    
    # Create indicator service
    service = IndicatorService(cache_enabled=False)
    
    # Test SMA calculation
    try:
        print("\nTesting SMA calculation...")
        sma_result = service.calculate_indicator("sma", ohlcv_data, {"period": 3})
        if "values" in sma_result:
            print("SMA calculation successful!")
            print(f"First few SMA values: {list(sma_result['values'].items())[:3]}")
        else:
            print(f"Error in SMA result: {sma_result}")
    except Exception as e:
        print(f"Error during SMA calculation: {e}")
    
    # Test EMA calculation
    try:
        print("\nTesting EMA calculation...")
        ema_result = service.calculate_indicator("ema", ohlcv_data, {"period": 3})
        if "values" in ema_result:
            print("EMA calculation successful!")
            print(f"First few EMA values: {list(ema_result['values'].items())[:3]}")
        else:
            print(f"Error in EMA result: {ema_result}")
    except Exception as e:
        print(f"Error during EMA calculation: {e}")
    
    # Test RSI calculation
    try:
        print("\nTesting RSI calculation...")
        rsi_result = service.calculate_indicator("rsi", ohlcv_data, {"period": 3})
        if "values" in rsi_result:
            print("RSI calculation successful!")
            print(f"First few RSI values: {list(rsi_result['values'].items())[:3]}")
        else:
            print(f"Error in RSI result: {rsi_result}")
    except Exception as e:
        print(f"Error during RSI calculation: {e}")
        
    # Test Bollinger Bands calculation
    try:
        print("\nTesting Bollinger Bands calculation...")
        bb_result = service.calculate_indicator("bollinger_bands", ohlcv_data, {"period": 3, "std_dev": 2.0})
        if "values" in bb_result:
            print("Bollinger Bands calculation successful!")
            print(f"Band types: {list(bb_result['values'].keys())}")
            if "upper" in bb_result["values"]:
                print(f"First few upper band values: {list(bb_result['values']['upper'].items())[:3]}")
        else:
            print(f"Error in Bollinger Bands result: {bb_result}")
    except Exception as e:
        print(f"Error during Bollinger Bands calculation: {e}")
    
    # Test batch calculation
    try:
        print("\nTesting batch calculation...")
        batch_config = [
            {"type": "sma", "parameters": {"period": 3}, "name": "SMA3"},
            {"type": "ema", "parameters": {"period": 3}, "name": "EMA3"},
            {"type": "rsi", "parameters": {"period": 3}, "name": "RSI3"}
        ]
        batch_result = service.calculate_multiple_indicators(ohlcv_data, batch_config)
        if "results" in batch_result:
            print("Batch calculation successful!")
            print(f"Indicators calculated: {list(batch_result['results'].keys())}")
        else:
            print(f"Error in batch result: {batch_result}")
    except Exception as e:
        print(f"Error during batch calculation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_indicators()