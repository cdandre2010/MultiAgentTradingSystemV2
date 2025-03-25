#!/usr/bin/env python

"""
Indicator Service Demo

This script demonstrates the use of the TA-Lib based IndicatorService
for calculating various technical indicators on sample OHLCV data.
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.indicators import IndicatorService
from src.models.market_data import OHLCV, OHLCVPoint


def generate_sample_data(days=100):
    """Generate sample OHLCV data with a trend and oscillation."""
    base_time = datetime(2023, 1, 1)
    data = []
    
    # Generate price data with a trend and some oscillation
    for i in range(days):
        # Add trend component
        trend = i * 0.5
        
        # Add oscillation component (sine wave)
        oscillation = 5 * np.sin(i / 10)
        
        # Combine trend and oscillation for realistic price movement
        price = 100 + trend + oscillation
        
        # Vary the high-low range
        high_low_range = 2 + abs(oscillation) / 2
        
        timestamp = base_time + timedelta(days=i)
        data.append(OHLCVPoint(
            timestamp=timestamp,
            open=price - 0.5,
            high=price + high_low_range,
            low=price - high_low_range,
            close=price,
            volume=1000 + 200 * abs(oscillation)  # Volume correlates with volatility
        ))
    
    return OHLCV(
        instrument="EXAMPLE",
        timeframe="1d",
        source="demo",
        data=data
    )


def plot_indicator(ohlcv_data, indicator_data, title):
    """Plot the OHLCV data and indicator together."""
    # Convert OHLCV data to DataFrame
    df = pd.DataFrame([
        {
            "timestamp": p.timestamp,
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "close": p.close,
            "volume": p.volume
        }
        for p in ohlcv_data.data
    ])
    df.set_index("timestamp", inplace=True)
    
    # Create a new figure
    plt.figure(figsize=(12, 8))
    
    # Plot price data
    ax1 = plt.subplot(2, 1, 1)
    ax1.plot(df.index, df["close"], label="Close Price")
    ax1.set_title(f"Price and {title}")
    ax1.legend()
    ax1.grid(True)
    
    # Plot indicator
    ax2 = plt.subplot(2, 1, 2, sharex=ax1)
    
    # Check if indicator is a dictionary of values or a dictionary with nested dictionaries
    if "values" in indicator_data and isinstance(indicator_data["values"], dict):
        if all(isinstance(v, dict) for v in indicator_data["values"].values()):
            # Handle multi-component indicators like MACD, Bollinger Bands
            for component, values in indicator_data["values"].items():
                # Convert dictionary to list aligned with timestamps
                component_values = []
                for timestamp in df.index:
                    ts_str = str(timestamp)
                    if ts_str in values:
                        component_values.append(values[ts_str])
                    else:
                        component_values.append(np.nan)
                
                ax2.plot(df.index, component_values, label=component)
        else:
            # Single component indicator with timestamp:value mapping
            indicator_values = []
            for timestamp in df.index:
                ts_str = str(timestamp)
                if ts_str in indicator_data["values"]:
                    indicator_values.append(indicator_data["values"][ts_str])
                else:
                    indicator_values.append(np.nan)
            
            ax2.plot(df.index, indicator_values, label=title)
    
    ax2.set_title(title)
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig(f"examples/output/{title.lower().replace(' ', '_')}.png")
    print(f"Saved plot to examples/output/{title.lower().replace(' ', '_')}.png")


def main():
    """Run the indicator service demo."""
    print("Indicator Service Demo")
    print("=====================")
    
    # Ensure output directory exists
    os.makedirs("examples/output", exist_ok=True)
    
    # Generate sample data
    ohlcv_data = generate_sample_data()
    print(f"Generated {len(ohlcv_data.data)} days of sample data")
    
    # Create indicator service
    service = IndicatorService()
    
    # Calculate and plot different indicators
    
    # Moving Average
    sma_result = service.calculate_indicator("sma", ohlcv_data, {"period": 20})
    plot_indicator(ohlcv_data, sma_result, "Simple Moving Average (20)")
    
    # Bollinger Bands
    bb_result = service.calculate_indicator("bollinger_bands", ohlcv_data, {"period": 20, "std_dev": 2.0})
    plot_indicator(ohlcv_data, bb_result, "Bollinger Bands")
    
    # RSI
    rsi_result = service.calculate_indicator("rsi", ohlcv_data, {"period": 14})
    plot_indicator(ohlcv_data, rsi_result, "Relative Strength Index")
    
    # MACD
    macd_result = service.calculate_indicator("macd", ohlcv_data, {})
    plot_indicator(ohlcv_data, macd_result, "MACD")
    
    # Calculate multiple indicators at once
    indicators_config = [
        {"type": "sma", "parameters": {"period": 10}, "name": "SMA10"},
        {"type": "sma", "parameters": {"period": 20}, "name": "SMA20"},
        {"type": "sma", "parameters": {"period": 50}, "name": "SMA50"},
    ]
    
    multi_results = service.calculate_multiple_indicators(ohlcv_data, indicators_config)
    print("\nCalculated multiple indicators with a single call:")
    for name, result in multi_results.items():
        if "error" not in result:
            print(f"- {name}: {result['metadata']['indicator_type']}")
            
    print("\nDemo complete! Check the output directory for plots.")


if __name__ == "__main__":
    main()