#!/usr/bin/env python3
"""
Test script for DataFeatureAgent functionality.

This script tests basic functionality of the DataFeatureAgent including:
- Market data retrieval
- Indicator calculation
- Data availability checking
- Visualization data preparation
"""

import sys
import json
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(".")

from src.agents.data_feature_agent import DataFeatureAgent
from src.services.indicators import IndicatorService
from src.database.influxdb import InfluxDBClient
from src.database.connection import get_database_connection
from src.services.data_availability import DataAvailabilityService
from src.services.data_retrieval import DataRetrievalService


def test_agent():
    """Run basic tests for DataFeatureAgent."""
    logger.info("Initializing services...")
    
    # Initialize services
    try:
        influxdb_client = InfluxDBClient()
        indicator_service = IndicatorService()
        data_availability_service = DataAvailabilityService(influxdb_client=influxdb_client)
        data_retrieval_service = DataRetrievalService(
            influxdb_client=influxdb_client,
            indicator_service=indicator_service
        )
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        return
        
    # Initialize agent
    logger.info("Initializing DataFeatureAgent...")
    agent = DataFeatureAgent(
        indicator_service=indicator_service,
        data_availability_service=data_availability_service,
        data_retrieval_service=data_retrieval_service
    )
    
    # Test parameters
    instrument = "BTCUSDT"
    timeframe = "1h"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Format dates as ISO strings
    start_date_str = start_date.isoformat()
    end_date_str = end_date.isoformat()
    
    # Test 1: Get market data
    logger.info("Test 1: Get market data")
    message = {
        "message_id": "test_1",
        "sender": "test_script",
        "timestamp": datetime.now().isoformat(),
        "recipient": "data_feature",
        "message_type": "request",
        "content": {
            "type": "get_market_data",
            "data": {
                "instrument": instrument,
                "timeframe": timeframe,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "sources": [
                    {"type": "influxdb", "priority": 1},
                    {"type": "binance", "priority": 2}
                ]
            }
        }
    }
    
    response = agent.process(message, {})
    
    # Check response
    if response["content"].get("type") == "market_data_result":
        logger.info("Market data retrieval successful")
        data_points = response["content"].get("data", {}).get("metadata", {}).get("data_points", 0)
        logger.info(f"Retrieved {data_points} data points")
    else:
        logger.error(f"Market data retrieval failed: {response['content'].get('error', 'Unknown error')}")
    
    # Test 2: Calculate indicator
    logger.info("Test 2: Calculate indicator")
    message = {
        "message_id": "test_2",
        "sender": "test_script",
        "timestamp": datetime.now().isoformat(),
        "recipient": "data_feature",
        "message_type": "request",
        "content": {
            "type": "calculate_indicator",
            "data": {
                "indicator": "rsi",
                "parameters": {"period": 14},
                "instrument": instrument,
                "timeframe": timeframe,
                "start_date": start_date_str,
                "end_date": end_date_str
            }
        }
    }
    
    response = agent.process(message, {})
    
    # Check response
    if response["content"].get("type") == "indicator_result":
        logger.info("Indicator calculation successful")
        values = response["content"].get("data", {}).get("values", {})
        logger.info(f"Calculated indicator with {len(values)} values")
    else:
        logger.error(f"Indicator calculation failed: {response['content'].get('error', 'Unknown error')}")
    
    # Test 3: Check data availability
    logger.info("Test 3: Check data availability")
    message = {
        "message_id": "test_3",
        "sender": "test_script",
        "timestamp": datetime.now().isoformat(),
        "recipient": "data_feature",
        "message_type": "request",
        "content": {
            "type": "check_data_availability",
            "data": {
                "instrument": instrument,
                "timeframe": timeframe,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "sources": [
                    {"type": "influxdb", "priority": 1},
                    {"type": "binance", "priority": 2}
                ]
            }
        }
    }
    
    response = agent.process(message, {})
    
    # Check response
    if response["content"].get("type") == "data_availability_result":
        logger.info("Data availability check successful")
        availability = response["content"].get("data", {}).get("availability", {}).get("overall", {})
        logger.info(f"Data availability: {availability.get('highest_availability', 0)}%")
        logger.info(f"Is complete: {availability.get('is_complete', False)}")
    else:
        logger.error(f"Data availability check failed: {response['content'].get('error', 'Unknown error')}")
    
    # Test 4: Create visualization
    logger.info("Test 4: Create visualization")
    message = {
        "message_id": "test_4",
        "sender": "test_script",
        "timestamp": datetime.now().isoformat(),
        "recipient": "data_feature",
        "message_type": "request",
        "content": {
            "type": "create_visualization",
            "data": {
                "visualization_type": "candlestick",
                "instrument": instrument,
                "timeframe": timeframe,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "indicators": [
                    {"type": "sma", "parameters": {"period": 14}, "name": "SMA"},
                    {"type": "rsi", "parameters": {"period": 14}, "name": "RSI"}
                ]
            }
        }
    }
    
    response = agent.process(message, {})
    
    # Check response
    if response["content"].get("type") == "visualization_result":
        logger.info("Visualization creation successful")
        viz_data = response["content"].get("data", {}).get("data", {})
        logger.info(f"Visualization type: {viz_data.get('type')}")
        logger.info(f"OHLCV data points: {len(viz_data.get('ohlcv', {}).get('timestamps', []))}")
        logger.info(f"Included indicators: {list(viz_data.get('indicators', {}).keys())}")
    else:
        logger.error(f"Visualization creation failed: {response['content'].get('error', 'Unknown error')}")
    
    logger.info("All tests completed")


def test_master_agent_integration():
    """Test integration with MasterAgent."""
    from src.agents.master_agent import MasterAgent
    
    logger.info("Testing MasterAgent integration with DataFeatureAgent...")
    
    # Initialize master agent
    master = MasterAgent()
    
    # Create a message for testing
    message = {
        "message_id": "test_master_1",
        "sender": "user",
        "timestamp": datetime.now().isoformat(),
        "recipient": "master_agent",
        "message_type": "request",
        "content": "Calculate the RSI indicator for Bitcoin hourly data from the past week"
    }
    
    # Process through master agent
    response = master.process(message, {})
    
    # Log results
    if response["message_type"] == "error":
        logger.error(f"MasterAgent integration test failed: {response['content'].get('error')}")
    else:
        logger.info("MasterAgent routing test successful")
        logger.info(f"Response type: {response['message_type']}")
        
    # Try a message that shouldn't go to the data agent
    message = {
        "message_id": "test_master_2",
        "sender": "user",
        "timestamp": datetime.now().isoformat(),
        "recipient": "master_agent",
        "message_type": "request",
        "content": "Tell me about trading strategies in general"
    }
    
    # Process through master agent
    response = master.process(message, {})
    
    # Log results
    if response["message_type"] == "error":
        logger.error(f"MasterAgent general routing test result: {response['content'].get('error')}")
    else:
        logger.info("MasterAgent general routing test: message routed elsewhere")
        logger.info(f"Response type: {response['message_type']}")


if __name__ == "__main__":
    # Run the basic agent test
    test_agent()
    
    # Run the master agent integration test
    test_master_agent_integration()