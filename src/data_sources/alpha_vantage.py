"""Alpha Vantage data source connector for retrieving market data."""

import logging
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

from .base import DataSourceConnector
from ..models.market_data import OHLCV, OHLCVPoint, DataPointSource

logger = logging.getLogger(__name__)


class AlphaVantageConnector(DataSourceConnector):
    """Connector for retrieving market data from Alpha Vantage."""
    
    # Alpha Vantage API base URL
    BASE_URL = 'https://www.alphavantage.co/query'
    
    # Timeframe mapping: internal timeframe to Alpha Vantage interval
    TIMEFRAME_MAP = {
        '1m': '1min',
        '5m': '5min',
        '15m': '15min',
        '30m': '30min',
        '60m': '60min',
        '1h': '60min',
        '1d': 'daily',
        '1w': 'weekly',
        '1mo': 'monthly'
    }
    
    def _initialize(self):
        """Initialize the Alpha Vantage connector."""
        self.api_key = self.config.get('api_key')
        if not self.api_key:
            raise ValueError("API key is required for Alpha Vantage connector")
            
        self.output_size = self.config.get('output_size', 'full')  # 'compact' or 'full'
        self.max_retries = self.config.get('max_retries', 3)
    
    def get_source_type(self) -> DataPointSource:
        """Get the source type for this connector."""
        return DataPointSource.ALPHA_VANTAGE
    
    async def fetch_ohlcv(self, 
                        instrument: str,
                        timeframe: str,
                        start_date: Union[datetime, str],
                        end_date: Union[datetime, str]) -> OHLCV:
        """Fetch OHLCV data from Alpha Vantage."""
        # Convert dates to standard format if they're strings
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
            
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        
        # Map internal timeframe to Alpha Vantage interval
        interval = self.TIMEFRAME_MAP.get(timeframe)
        if not interval:
            # Try to find a close match
            if timeframe.endswith('d'):
                interval = 'daily'
            elif timeframe.endswith('h'):
                interval = '60min'
            elif timeframe.endswith('m'):
                interval = '1min'
            else:
                raise ValueError(f"Unsupported timeframe: {timeframe}")
                
        try:
            # Fetch data from Alpha Vantage
            if interval in ['daily', 'weekly', 'monthly']:
                # For daily, weekly, or monthly data
                function = f"TIME_SERIES_{interval.upper()}"
                raw_data = await self._make_request(
                    function=function,
                    symbol=instrument,
                    outputsize=self.output_size
                )
                
                # Parse the response
                time_series_key = f"Time Series ({interval.capitalize()})"
                if interval == 'daily':
                    time_series_key = "Time Series (Daily)"
                elif interval == 'weekly':
                    time_series_key = "Weekly Time Series"
                elif interval == 'monthly':
                    time_series_key = "Monthly Time Series"
                    
                df = self._parse_time_series(raw_data, time_series_key)
            else:
                # For intraday data
                function = "TIME_SERIES_INTRADAY"
                raw_data = await self._make_request(
                    function=function,
                    symbol=instrument,
                    interval=interval,
                    outputsize=self.output_size
                )
                
                # Parse the response
                time_series_key = f"Time Series ({interval})"
                df = self._parse_time_series(raw_data, time_series_key)
            
            # Filter by date range
            if not df.empty:
                df = df.loc[(df.index >= start_date) & (df.index <= end_date)]
            
            # Convert to OHLCV format
            ohlcv_data = self._convert_to_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                df=df
            )
            
            # Cache the data to InfluxDB if enabled
            if not df.empty and self.cache_to_influxdb:
                await self._cache_to_influxdb(
                    instrument=instrument,
                    timeframe=timeframe,
                    data=[point.dict() for point in ohlcv_data.data],
                    is_adjusted=False
                )
            
            return ohlcv_data
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV data from Alpha Vantage: {e}")
            return OHLCV(
                instrument=instrument,
                timeframe=timeframe,
                source=self.get_source_type(),
                data=[]
            )
    
    async def check_availability(self,
                              instrument: str,
                              timeframe: str) -> Dict[str, Any]:
        """Check if data is available for the specified instrument and timeframe."""
        try:
            # Verify the timeframe is supported
            if timeframe not in self.get_supported_timeframes():
                # Try to find a close match
                match_found = False
                for pattern, alpha_tf in [
                    ('d', 'daily'), ('h', '60min'), ('m', '1min')
                ]:
                    if timeframe.endswith(pattern):
                        match_found = True
                        break
                
                if not match_found:
                    return {
                        "available": False,
                        "message": f"Timeframe {timeframe} not supported by Alpha Vantage"
                    }
            
            # Try to fetch a small amount of recent data to verify
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)  # Look back a week
            
            # Use compact output size for faster check
            original_output_size = self.output_size
            self.output_size = 'compact'
            
            ohlcv = await self.fetch_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            # Restore original output size
            self.output_size = original_output_size
            
            return {
                "available": len(ohlcv.data) > 0,
                "message": f"Data available for {instrument}/{timeframe}" 
                          if len(ohlcv.data) > 0 else 
                          f"No data found for {instrument}/{timeframe}",
                "data_points": len(ohlcv.data)
            }
            
        except Exception as e:
            logger.error(f"Error checking data availability on Alpha Vantage: {e}")
            return {
                "available": False,
                "message": f"Error checking availability: {str(e)}"
            }
    
    def get_supported_timeframes(self) -> List[str]:
        """Get the list of timeframes supported by Alpha Vantage."""
        return list(self.TIMEFRAME_MAP.keys())
    
    def get_supported_instruments(self) -> List[str]:
        """
        Get a list of common instruments supported by Alpha Vantage.
        
        Note: Alpha Vantage doesn't have a convenient API to list all available symbols.
        This method returns a list of common symbols as an example.
        """
        # Common stock symbols from major indices and forex pairs
        common_symbols = [
            # US Stocks
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "BRK.B", "JNJ",
            # Indices
            "SPY", "QQQ", "DIA",
            # Forex
            "EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD",
            # Cryptocurrencies
            "BTC", "ETH", "XRP"
        ]
        
        return common_symbols
    
    async def _make_request(self, function: str, symbol: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the Alpha Vantage API."""
        # Prepare request parameters
        params = {
            'function': function,
            'symbol': symbol,
            'apikey': self.api_key,
            **kwargs
        }
        
        for retry in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.BASE_URL, params=params) as response:
                        if response.status != 200:
                            logger.error(f"Error fetching data from Alpha Vantage: {response.status}")
                            continue
                        
                        data = await response.json()
                        
                        # Check for error messages in the response
                        if "Error Message" in data:
                            logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                            raise ValueError(data["Error Message"])
                            
                        # Check for API call frequency warning
                        if "Note" in data and "call frequency" in data["Note"]:
                            logger.warning(f"Alpha Vantage API frequency warning: {data['Note']}")
                        
                        return data
                        
            except Exception as e:
                logger.error(f"Error in request to Alpha Vantage (retry {retry+1}/{self.max_retries}): {e}")
                if retry == self.max_retries - 1:
                    raise
        
        raise RuntimeError("Failed to fetch data from Alpha Vantage after multiple retries")
    
    def _parse_time_series(self, data: Dict[str, Any], time_series_key: str) -> pd.DataFrame:
        """Parse Alpha Vantage time series data into a pandas DataFrame."""
        if not data or time_series_key not in data:
            logger.error(f"Missing time series data in Alpha Vantage response: {data.keys()}")
            return pd.DataFrame()
            
        time_series = data[time_series_key]
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(time_series, orient='index')
        
        # Rename columns
        column_mapping = {
            '1. open': 'Open',
            '2. high': 'High',
            '3. low': 'Low',
            '4. close': 'Close',
            '5. volume': 'Volume'
        }
        df = df.rename(columns=column_mapping)
        
        # Convert columns to numeric
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col])
        
        # Convert index to datetime
        df.index = pd.to_datetime(df.index)
        
        # Sort by date
        df = df.sort_index()
        
        return df
    
    def _convert_to_ohlcv(self,
                        instrument: str,
                        timeframe: str,
                        df: pd.DataFrame) -> OHLCV:
        """Convert Alpha Vantage data to OHLCV format."""
        data_points = []
        
        if df.empty:
            return OHLCV(
                instrument=instrument,
                timeframe=timeframe,
                source=self.get_source_type(),
                data=[]
            )
        
        # Ensure expected columns exist
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"Missing required columns in Alpha Vantage data: {df.columns}")
            return OHLCV(
                instrument=instrument,
                timeframe=timeframe,
                source=self.get_source_type(),
                data=[]
            )
        
        # Convert DataFrame to OHLCV points
        for timestamp, row in df.iterrows():
            # Alpha Vantage returns timestamps as pandas Timestamp objects
            if hasattr(timestamp, 'to_pydatetime'):
                dt = timestamp.to_pydatetime()
            else:
                dt = timestamp
                
            data_points.append(OHLCVPoint(
                timestamp=dt,
                open=float(row['Open']),
                high=float(row['High']),
                low=float(row['Low']),
                close=float(row['Close']),
                volume=float(row['Volume']),
                source_id=f"alphavantage_{int(dt.timestamp())}"
            ))
        
        return OHLCV(
            instrument=instrument,
            timeframe=timeframe,
            source=self.get_source_type(),
            data=data_points
        )