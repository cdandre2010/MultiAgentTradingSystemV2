"""
Data/Feature Agent for market data processing and feature generation.

This agent is responsible for retrieving market data, calculating indicators,
generating features for strategies, and validating data availability.
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional, Union, Any, Set, Coroutine
from datetime import datetime

from .base import Agent
from ..services.indicators import IndicatorService
from ..services.data_availability import DataAvailabilityService
from ..services.data_retrieval import DataRetrievalService
from ..models.market_data import OHLCV, OHLCVPoint, MarketDataRequest
from ..models.strategy import DataConfig, DataSource, DataSourceType
from ..database.influxdb import InfluxDBClient

logger = logging.getLogger(__name__)


class DataFeatureAgent(Agent):
    """
    Agent responsible for market data processing, indicator calculation,
    and feature generation for trading strategies.
    
    This agent handles retrieval of market data, calculation of technical
    indicators, preparation of strategy data, and visualization of market data.
    """
    
    def __init__(self, indicator_service=None, data_availability_service=None, 
                data_retrieval_service=None):
        """
        Initialize the agent.
        
        Args:
            indicator_service: Service for calculating indicators
            data_availability_service: Service for checking data availability
            data_retrieval_service: Service for retrieving market data
        """
        super().__init__(name="data_feature")
        
        # Create InfluxDB client if needed for services
        influxdb_client = None
        if data_availability_service is None or data_retrieval_service is None:
            influxdb_client = InfluxDBClient()
        
        # Initialize services with defaults if not provided
        self.indicator_service = indicator_service or IndicatorService()
        self.data_availability_service = data_availability_service or DataAvailabilityService(
            influxdb_client=influxdb_client
        )
        self.data_retrieval_service = data_retrieval_service or DataRetrievalService(
            influxdb_client=influxdb_client,
            indicator_service=self.indicator_service
        )
        
    def run_async(self, coroutine: Coroutine) -> Any:
        """
        Run an async coroutine in the current thread.
        
        Args:
            coroutine: The coroutine to run
            
        Returns:
            The result of the coroutine
        """
        try:
            # Create a new event loop for this thread if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            # Run the coroutine and return the result
            if loop.is_running():
                # If loop is already running, use run_coroutine_threadsafe
                future = asyncio.run_coroutine_threadsafe(coroutine, loop)
                return future.result()
            else:
                # If loop is not running, use run_until_complete
                return loop.run_until_complete(coroutine)
        except Exception as e:
            logger.error(f"Error running async function: {e}")
            raise
    
    def process(self, message: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming message.
        
        Args:
            message: The message to process
            state: Current conversation state
            
        Returns:
            Response message
        """
        if not self.validate_message(message):
            logger.warning("Invalid message format")
            return self.create_message(
                recipient=message.get("sender", "unknown"),
                message_type="error",
                content={"error": "Invalid message format"}
            )
        
        # Log the incoming message
        self.log_message(message)
        
        # Extract message content and type
        content = message.get("content", {})
        message_type = content.get("type", "") if isinstance(content, dict) else ""
        message_data = content.get("data", {}) if isinstance(content, dict) else {}
        
        # Process message based on type
        response_content = None
        
        if message_type == "calculate_indicator":
            response_content = self._handle_calculate_indicator(message_data)
        elif message_type == "get_market_data":
            response_content = self._handle_get_market_data(message_data)
        elif message_type == "prepare_strategy_data":
            response_content = self._handle_prepare_strategy_data(message_data)
        elif message_type == "check_data_availability":
            response_content = self._handle_check_data_availability(message_data)
        elif message_type == "create_visualization":
            response_content = self._handle_create_visualization(message_data)
        else:
            response_content = {
                "type": "error",
                "error": f"Unknown message type: {message_type}"
            }
        
        # Create and return the response message
        response = self.create_message(
            recipient=message.get("sender", "unknown"),
            message_type="response" if "error" not in response_content else "error",
            content=response_content,
            context=message.get("context", {})
        )
        
        # Log the outgoing message
        self.log_message(response, direction="sent")
        
        return response
    
    def _handle_calculate_indicator(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle calculate_indicator message.
        
        Args:
            data: Message data with indicator parameters
            
        Returns:
            Indicator calculation result
        """
        try:
            # Extract parameters from message
            indicator_type = data.get("indicator")
            parameters = data.get("parameters", {})
            instrument = data.get("instrument")
            timeframe = data.get("timeframe")
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            sources = data.get("sources", [{"type": "influxdb", "priority": 1}])
            
            # Validate required parameters
            if not all([indicator_type, instrument, timeframe, start_date, end_date]):
                return {
                    "type": "error",
                    "error": "Missing required parameters"
                }
            
            # Get market data
            market_data_request = {
                "instrument": instrument,
                "timeframe": timeframe,
                "start_date": start_date,
                "end_date": end_date,
                "sources": sources
            }
            
            market_data_result = self._handle_get_market_data(market_data_request)
            
            if "error" in market_data_result:
                return market_data_result
            
            ohlcv_data = market_data_result.get("data", {}).get("ohlcv")
            
            if not ohlcv_data:
                return {
                    "type": "error",
                    "error": "Failed to retrieve market data"
                }
            
            # Calculate indicator
            indicator_result = self.indicator_service.calculate_indicator(
                indicator_type=indicator_type,
                ohlcv_data=ohlcv_data,
                parameters=parameters
            )
            
            if "error" in indicator_result:
                return {
                    "type": "error",
                    "error": f"Failed to calculate indicator: {indicator_result['error']}"
                }
            
            return {
                "type": "indicator_result",
                "data": indicator_result
            }
            
        except Exception as e:
            logger.error(f"Error calculating indicator: {e}")
            return {
                "type": "error",
                "error": f"Error calculating indicator: {str(e)}"
            }
    
    def _handle_get_market_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get_market_data message.
        
        Args:
            data: Message data with market data request parameters
            
        Returns:
            Market data retrieval result
        """
        try:
            # Extract parameters from message
            instrument = data.get("instrument")
            timeframe = data.get("timeframe")
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            sources = data.get("sources", [{"type": "influxdb", "priority": 1}])
            
            # Validate required parameters
            if not all([instrument, timeframe, start_date, end_date]):
                return {
                    "type": "error",
                    "error": "Missing required parameters"
                }
            
            # Convert sources to proper DataSource objects
            data_sources = []
            for source in sources:
                source_type = source.get("type")
                priority = source.get("priority", 1)
                
                if not source_type:
                    continue
                    
                try:
                    # Try to convert to enum if string provided
                    if isinstance(source_type, str):
                        source_type = DataSourceType(source_type)
                except ValueError:
                    # If not a valid enum value, keep as string
                    pass
                
                data_sources.append(DataSource(
                    type=source_type,
                    priority=priority
                ))
            
            # Get market data (run async function synchronously if it's async)
            get_ohlcv = self.data_retrieval_service.get_ohlcv
            if asyncio.iscoroutinefunction(get_ohlcv):
                ohlcv_data = self.run_async(
                    get_ohlcv(
                        data_sources=data_sources,
                        instrument=instrument,
                        timeframe=timeframe,
                        start_date=start_date,
                        end_date=end_date
                    )
                )
            else:
                ohlcv_data = get_ohlcv(
                    data_sources=data_sources,
                    instrument=instrument,
                    timeframe=timeframe,
                    start_date=start_date,
                    end_date=end_date
                )
            
            if not ohlcv_data:
                return {
                    "type": "error",
                    "error": "Failed to retrieve market data"
                }
            
            return {
                "type": "market_data_result",
                "data": {
                    "ohlcv": ohlcv_data,
                    "metadata": {
                        "instrument": instrument,
                        "timeframe": timeframe,
                        "start_date": start_date,
                        "end_date": end_date,
                        "source": ohlcv_data.source,
                        "data_points": len(ohlcv_data.data)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error retrieving market data: {e}")
            return {
                "type": "error",
                "error": f"Error retrieving market data: {str(e)}"
            }
    
    def _handle_prepare_strategy_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle prepare_strategy_data message.
        
        Args:
            data: Message data with strategy data preparation parameters
            
        Returns:
            Strategy data preparation result
        """
        try:
            # Extract parameters from message
            strategy_id = data.get("strategy_id")
            data_config_dict = data.get("data_config", {})
            indicators = data.get("indicators", [])
            
            # Validate required parameters
            if not all([strategy_id, data_config_dict]):
                return {
                    "type": "error",
                    "error": "Missing required parameters"
                }
            
            # Create DataConfig object from dictionary
            try:
                data_config = DataConfig.model_validate(data_config_dict)
            except Exception as e:
                logger.error(f"Invalid data configuration: {e}")
                return {
                    "type": "error",
                    "error": f"Invalid data configuration: {str(e)}"
                }
            
            # Validate the data configuration
            validation = self._validate_data_for_strategy(strategy_id, data_config)
            
            if not validation.get("is_valid", False):
                return {
                    "type": "error",
                    "error": "Data validation failed",
                    "details": validation
                }
            
            # Get market data for the strategy (handle async if needed)
            get_data_for_strategy = self.data_retrieval_service.get_data_for_strategy
            if asyncio.iscoroutinefunction(get_data_for_strategy):
                market_data = self.run_async(get_data_for_strategy(data_config))
            else:
                market_data = get_data_for_strategy(data_config)
            
            if "error" in market_data:
                return {
                    "type": "error",
                    "error": f"Failed to retrieve market data: {market_data['error']}"
                }
            
            # Calculate indicators if requested (handle async if needed)
            if indicators:
                get_data_with_indicators = self.data_retrieval_service.get_data_with_indicators
                if asyncio.iscoroutinefunction(get_data_with_indicators):
                    indicator_data = self.run_async(get_data_with_indicators(
                        ohlcv_data=market_data.get("data"),
                        indicators_config=indicators
                    ))
                else:
                    indicator_data = get_data_with_indicators(
                        ohlcv_data=market_data.get("data"),
                        indicators_config=indicators
                    )
                
                if "error" in indicator_data:
                    return {
                        "type": "error",
                        "error": f"Failed to calculate indicators: {indicator_data['error']}"
                    }
            else:
                indicator_data = {"indicators": {}}
            
            # Create snapshot for backtesting audit if needed (handle async if needed)
            create_backtest_snapshot = self.data_retrieval_service.create_backtest_snapshot
            if asyncio.iscoroutinefunction(create_backtest_snapshot):
                snapshot_id = self.run_async(create_backtest_snapshot(
                    data_config=data_config,
                    strategy_id=strategy_id
                ))
            else:
                snapshot_id = create_backtest_snapshot(
                    data_config=data_config,
                    strategy_id=strategy_id
                )
            
            return {
                "type": "strategy_data_result",
                "data": {
                    "market_data": market_data.get("data"),
                    "indicators": indicator_data.get("indicators", {}),
                    "metadata": market_data.get("metadata", {}),
                    "snapshot_id": snapshot_id
                }
            }
            
        except Exception as e:
            logger.error(f"Error preparing strategy data: {e}")
            return {
                "type": "error",
                "error": f"Error preparing strategy data: {str(e)}"
            }
    
    def _handle_check_data_availability(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle check_data_availability message.
        
        Args:
            data: Message data with data availability check parameters
            
        Returns:
            Data availability check result
        """
        try:
            # Extract parameters from message
            instrument = data.get("instrument")
            timeframe = data.get("timeframe")
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            sources = data.get("sources", [{"type": "influxdb", "priority": 1}])
            
            # Validate required parameters
            if not all([instrument, timeframe, start_date, end_date]):
                return {
                    "type": "error",
                    "error": "Missing required parameters"
                }
            
            # Create DataConfig object for availability check
            data_config = DataConfig(
                instrument=instrument,
                frequency=timeframe,
                sources=[
                    DataSource(
                        type=source.get("type"),
                        priority=source.get("priority", 1)
                    )
                    for source in sources
                ],
                backtest_range={
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            
            # Check data availability (run async function synchronously)
            availability = self.run_async(
                self.data_availability_service.check_data_requirements(data_config)
            )
            
            return {
                "type": "data_availability_result",
                "data": {
                    "availability": availability,
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
            
        except Exception as e:
            logger.error(f"Error checking data availability: {e}")
            return {
                "type": "error",
                "error": f"Error checking data availability: {str(e)}"
            }
    
    def _handle_create_visualization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle create_visualization message.
        
        Args:
            data: Message data with visualization parameters
            
        Returns:
            Visualization data
        """
        try:
            # Extract parameters from message
            visualization_type = data.get("visualization_type", "candlestick")
            instrument = data.get("instrument")
            timeframe = data.get("timeframe")
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            indicators = data.get("indicators", [])
            
            # Validate required parameters
            if not all([instrument, timeframe, start_date, end_date]):
                return {
                    "type": "error",
                    "error": "Missing required parameters"
                }
            
            # Get market data
            market_data_request = {
                "instrument": instrument,
                "timeframe": timeframe,
                "start_date": start_date,
                "end_date": end_date
            }
            
            market_data_result = self._handle_get_market_data(market_data_request)
            
            if "error" in market_data_result:
                return market_data_result
            
            ohlcv_data = market_data_result.get("data", {}).get("ohlcv")
            
            if not ohlcv_data:
                return {
                    "type": "error",
                    "error": "Failed to retrieve market data for visualization"
                }
            
            # Format OHLCV data for visualization
            formatted_ohlcv = self._format_ohlcv_for_visualization(ohlcv_data)
            
            # Calculate and format indicators if requested
            formatted_indicators = {}
            
            if indicators:
                indicator_results = self.indicator_service.calculate_multiple_indicators(
                    ohlcv_data=ohlcv_data,
                    indicators_config=indicators
                )
                
                for name, data in indicator_results.items():
                    formatted_indicators[name] = self._format_indicator_for_visualization(data)
            
            # Create visualization data structure
            visualization_data = {
                "type": visualization_type,
                "instrument": instrument,
                "timeframe": timeframe,
                "ohlcv": formatted_ohlcv,
                "indicators": formatted_indicators,
                "start_date": start_date,
                "end_date": end_date
            }
            
            return {
                "type": "visualization_result",
                "data": {
                    "data": visualization_data,
                    "format": "json"
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating visualization: {e}")
            return {
                "type": "error",
                "error": f"Error creating visualization: {str(e)}"
            }
    
    def _validate_data_for_strategy(self, strategy_id: str, data_config: DataConfig) -> Dict[str, Any]:
        """
        Validate data availability for a strategy.
        
        Args:
            strategy_id: ID of the strategy
            data_config: Data configuration for the strategy
            
        Returns:
            Validation result with availability information
        """
        try:
            # Check data availability (run async function synchronously)
            availability = self.run_async(
                self.data_availability_service.check_data_requirements(data_config)
            )
            
            overall = availability.get("overall", {})
            is_complete = overall.get("is_complete", False)
            highest_availability = overall.get("highest_availability", 0)
            
            issues = []
            recommendations = []
            
            # Check for issues
            if not is_complete:
                issues.append("Incomplete data for the requested time range")
                recommendations.append("Adjust the date range or add more data sources")
                
            if highest_availability < 90:
                issues.append(f"Low data availability ({highest_availability:.1f}%)")
                recommendations.append("Add more data sources or choose a different time range")
            
            return {
                "is_valid": is_complete and highest_availability >= 90,
                "availability": availability,
                "issues": issues,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error validating data for strategy: {e}")
            return {
                "is_valid": False,
                "issues": [f"Error validating data: {str(e)}"],
                "recommendations": ["Check data configuration parameters"]
            }
    
    def _format_ohlcv_for_visualization(self, ohlcv_data: OHLCV) -> Dict[str, Any]:
        """
        Format OHLCV data for visualization.
        
        Args:
            ohlcv_data: OHLCV data to format
            
        Returns:
            Formatted data for visualization
        """
        timestamps = []
        opens = []
        highs = []
        lows = []
        closes = []
        volumes = []
        
        for point in ohlcv_data.data:
            timestamps.append(point.timestamp.isoformat())
            opens.append(float(point.open))
            highs.append(float(point.high))
            lows.append(float(point.low))
            closes.append(float(point.close))
            volumes.append(float(point.volume))
        
        return {
            "timestamps": timestamps,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes
        }
    
    def _format_indicator_for_visualization(self, indicator_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format indicator data for visualization.
        
        Args:
            indicator_data: Indicator data to format
            
        Returns:
            Formatted data for visualization
        """
        values_dict = indicator_data.get("values", {})
        
        # If the values are nested (like in Bollinger Bands), handle each component
        if isinstance(next(iter(values_dict.values()), None), dict):
            components = {}
            for component_name, component_values in values_dict.items():
                timestamps = sorted(component_values.keys())
                values = [component_values[ts] for ts in timestamps]
                components[component_name] = {
                    "timestamps": timestamps,
                    "values": values
                }
                
            return {
                "components": components,
                "metadata": indicator_data.get("metadata", {})
            }
        else:
            # For simple indicators with single values
            timestamps = sorted(values_dict.keys())
            values = [values_dict[ts] for ts in timestamps]
            
            return {
                "timestamps": timestamps,
                "values": values,
                "metadata": indicator_data.get("metadata", {})
            }