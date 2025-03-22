#!/usr/bin/env python
"""
Test script for data source connectors.

This script demonstrates how to use the data source connectors
to fetch market data from various sources.
"""

import asyncio
import logging
import argparse
import sys
import os
from datetime import datetime, timedelta

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_sources.base import DataSourceConnector
from src.data_sources.binance import BinanceConnector
from src.data_sources.yfinance import YFinanceConnector 
from src.data_sources.alpha_vantage import AlphaVantageConnector
from src.data_sources.csv import CSVConnector
from src.database.influxdb import InfluxDBClient

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_connectors")

async def test_binance_connector():
    """Test the Binance connector."""
    logger.info("Testing Binance connector...")
    
    # Set up configuration
    config = {
        "use_testnet": True,  # Use testnet for testing
        "api_key": "",  # Optional: API key for authenticated requests
        "api_secret": ""  # Optional: API secret for authenticated requests
    }
    
    # Create the connector
    connector = BinanceConnector(config=config, cache_to_influxdb=False)
    
    # Define test parameters
    instrument = "ETHUSDT"
    timeframe = "15m"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # Last 7 days
    
    # Check availability
    availability = await connector.check_availability(instrument, timeframe)
    logger.info(f"Availability: {availability}")
    
    if availability.get("available", False):
        # Fetch data
        data = await connector.fetch_ohlcv(
            instrument=instrument,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"Retrieved {len(data.data) if data.data else 0} data points")
        
        # Print first few data points
        if data.data:
            for i, point in enumerate(data.data[:5]):
                logger.info(f"Data point {i+1}: {point}")
    else:
        logger.warning("Binance data not available")
    
    return availability.get("available", False)

async def test_yfinance_connector():
    """Test the YFinance connector."""
    logger.info("Testing YFinance connector...")
    
    # Set up configuration
    config = {
        "use_async": True  # Use async requests if possible
    }
    
    # Create the connector
    connector = YFinanceConnector(config=config, cache_to_influxdb=False)
    
    # Define test parameters
    instrument = "AAPL"
    timeframe = "1d"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # Last 30 days
    
    # Check availability
    availability = await connector.check_availability(instrument, timeframe)
    logger.info(f"Availability: {availability}")
    
    if availability.get("available", False):
        # Fetch data
        data = await connector.fetch_ohlcv(
            instrument=instrument,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"Retrieved {len(data.data) if data.data else 0} data points")
        
        # Print first few data points
        if data.data:
            for i, point in enumerate(data.data[:5]):
                logger.info(f"Data point {i+1}: {point}")
    else:
        logger.warning("YFinance data not available")
    
    return availability.get("available", False)

async def test_alpha_vantage_connector(api_key):
    """Test the Alpha Vantage connector."""
    logger.info("Testing Alpha Vantage connector...")
    
    # Try to get API key from environment if not provided
    if not api_key:
        api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")

    if not api_key:
        logger.error("Alpha Vantage API key is required")
        return False
    
    # Set up configuration
    config = {
        "api_key": api_key,
        "output_size": "compact"  # Use compact output for faster testing
    }
    
    # Create the connector
    connector = AlphaVantageConnector(config=config, cache_to_influxdb=False)
    
    # Define test parameters
    instrument = "MSFT"
    timeframe = "1d"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)  # Last 30 days
    
    # Check availability
    availability = await connector.check_availability(instrument, timeframe)
    logger.info(f"Availability: {availability}")
    
    if availability.get("available", False):
        # Fetch data
        data = await connector.fetch_ohlcv(
            instrument=instrument,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"Retrieved {len(data.data) if data.data else 0} data points")
        
        # Print first few data points
        if data.data:
            for i, point in enumerate(data.data[:5]):
                logger.info(f"Data point {i+1}: {point}")
    else:
        logger.warning("Alpha Vantage data not available")
    
    return availability.get("available", False)

async def test_csv_connector(data_dir):
    """Test the CSV connector."""
    logger.info("Testing CSV connector...")
    
    # Set up configuration
    config = {
        "data_dir": data_dir or "./data/csv",
    }
    
    # Create the connector
    connector = CSVConnector(config=config, cache_to_influxdb=False)
    
    # Try to get supported instruments and timeframes
    instruments = connector.get_supported_instruments()
    timeframes = connector.get_supported_timeframes()
    
    logger.info(f"Supported instruments: {instruments}")
    logger.info(f"Supported timeframes: {timeframes}")
    
    if not instruments or not timeframes:
        logger.warning(f"No CSV files found in {config['data_dir']}")
        return False
    
    # Use the first available instrument and timeframe
    instrument = instruments[0] if instruments else "BTC"
    timeframe = timeframes[0] if timeframes else "1d"
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)  # Last year
    
    # Check availability
    availability = await connector.check_availability(instrument, timeframe)
    logger.info(f"Availability: {availability}")
    
    if availability.get("available", False):
        # Fetch data
        data = await connector.fetch_ohlcv(
            instrument=instrument,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"Retrieved {len(data.data) if data.data else 0} data points")
        
        # Print first few data points
        if data.data:
            for i, point in enumerate(data.data[:5]):
                logger.info(f"Data point {i+1}: {point}")
    else:
        logger.warning("CSV data not available")
    
    return availability.get("available", False)

async def main():
    """Main function to run the tests."""
    parser = argparse.ArgumentParser(description="Test data source connectors")
    parser.add_argument("--binance", action="store_true", help="Test Binance connector")
    parser.add_argument("--yfinance", action="store_true", help="Test YFinance connector")
    parser.add_argument("--alphavantage", action="store_true", help="Test Alpha Vantage connector")
    parser.add_argument("--csv", action="store_true", help="Test CSV connector")
    parser.add_argument("--all", action="store_true", help="Test all connectors")
    parser.add_argument("--av-key", help="Alpha Vantage API key")
    parser.add_argument("--csv-dir", help="Directory for CSV files")
    parser.add_argument("--symbol", help="Custom symbol to test with")
    parser.add_argument("--timeframe", help="Custom timeframe to test with")
    
    args = parser.parse_args()
    
    # If no specific connector is selected, test all
    if not (args.binance or args.yfinance or args.alphavantage or args.csv):
        args.all = True
    
    results = {}
    
    if args.all or args.binance:
        results["binance"] = await test_binance_connector()
    
    if args.all or args.yfinance:
        results["yfinance"] = await test_yfinance_connector()
    
    if args.all or args.alphavantage:
        results["alphavantage"] = await test_alpha_vantage_connector(args.av_key)
    
    if args.all or args.csv:
        results["csv"] = await test_csv_connector(args.csv_dir)
    
    logger.info("===== Test Results =====")
    for connector, success in results.items():
        logger.info(f"{connector}: {'SUCCESS' if success else 'FAILED'}")

if __name__ == "__main__":
    asyncio.run(main())