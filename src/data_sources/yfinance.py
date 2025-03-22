"""YFinance data source connector for retrieving market data."""

import logging
import aiohttp
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any

from .base import DataSourceConnector
from ..models.market_data import OHLCV, OHLCVPoint, DataPointSource

logger = logging.getLogger(__name__)


class YFinanceConnector(DataSourceConnector):
    """Connector for retrieving market data from Yahoo Finance using yfinance library."""
    
    # Yahoo Finance timeframe mapping (internal timeframe to Yahoo interval)
    TIMEFRAME_MAP = {
        '1m': '1m',
        '2m': '2m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '60m': '60m',
        '1h': '60m',
        '90m': '90m',
        '1d': '1d',
        '5d': '5d',
        '1wk': '1wk',
        '1mo': '1mo',
        '3mo': '3mo'
    }
    
    def _initialize(self):
        """Initialize the Yahoo Finance connector."""
        self.max_retries = self.config.get('max_retries', 3)
        self.use_async = self.config.get('use_async', True)
    
    def get_source_type(self) -> DataPointSource:
        """Get the source type for this connector."""
        return DataPointSource.YAHOO  # We'll still use YAHOO enum value for consistency
    
    async def fetch_ohlcv(self, 
                        instrument: str,
                        timeframe: str,
                        start_date: Union[datetime, str],
                        end_date: Union[datetime, str]) -> OHLCV:
        """Fetch OHLCV data from Yahoo Finance."""
        # Convert dates to standard format for Yahoo Finance
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
            
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        
        # Map internal timeframe to Yahoo Finance interval
        interval = self.TIMEFRAME_MAP.get(timeframe)
        if not interval:
            # Try to find a close match or use a default
            if timeframe == '4h':
                interval = '60m'  # Use hourly data for 4h timeframe
            elif timeframe == '1w':
                interval = '1wk'
            elif timeframe.endswith('d'):
                interval = '1d'
            elif timeframe.endswith('h'):
                interval = '60m'
            elif timeframe.endswith('m'):
                interval = '1m'
            else:
                raise ValueError(f"Unsupported timeframe: {timeframe}")
                
        try:
            # Using yfinance library for data fetching
            # Note: yfinance is synchronous, so we're not using async here
            # For real async implementation, we'd need to use ThreadPoolExecutor
            ticker_data = yf.download(
                tickers=instrument,
                start=start_date,
                end=end_date + timedelta(days=1),  # Include end date
                interval=interval,
                auto_adjust=True,  # Adjust for splits and dividends
                progress=False
            )
            
            # Convert to OHLCV format
            ohlcv_data = self._convert_to_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                df=ticker_data
            )
            
            # Cache the data to InfluxDB if enabled
            if not ticker_data.empty and self.cache_to_influxdb:
                await self._cache_to_influxdb(
                    instrument=instrument,
                    timeframe=timeframe,
                    data=[point.dict() for point in ohlcv_data.data],
                    is_adjusted=True  # Yahoo Finance data is adjusted
                )
            
            return ohlcv_data
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV data from Yahoo Finance: {e}")
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
                for pattern, yahoo_tf in [
                    ('d', '1d'), ('h', '60m'), ('m', '1m'), ('w', '1wk'), ('mo', '1mo')
                ]:
                    if timeframe.endswith(pattern):
                        match_found = True
                        break
                
                if not match_found:
                    return {
                        "available": False,
                        "message": f"Timeframe {timeframe} not supported by Yahoo Finance"
                    }
            
            # Try to fetch a small amount of recent data to verify
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)  # Look back a week
            
            ohlcv = await self.fetch_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "available": len(ohlcv.data) > 0,
                "message": f"Data available for {instrument}/{timeframe}" 
                          if len(ohlcv.data) > 0 else 
                          f"No data found for {instrument}/{timeframe}",
                "data_points": len(ohlcv.data)
            }
            
        except Exception as e:
            logger.error(f"Error checking data availability on Yahoo Finance: {e}")
            return {
                "available": False,
                "message": f"Error checking availability: {str(e)}"
            }
    
    def get_supported_timeframes(self) -> List[str]:
        """Get the list of timeframes supported by Yahoo Finance."""
        return list(self.TIMEFRAME_MAP.keys())
    
    def get_supported_instruments(self) -> List[str]:
        """
        Get a list of popular instruments supported by Yahoo Finance.
        
        Note: Yahoo Finance doesn't have a convenient API to list all available symbols.
        This method returns a list of popular symbols as an example.
        """
        # Common stock symbols from major indices
        popular_symbols = [
            # US Indices
            "^GSPC", "^DJI", "^IXIC", "^RUT",
            # Popular US stocks
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "BRK-B", "JNJ",
            # Cryptocurrencies
            "BTC-USD", "ETH-USD", "XRP-USD",
            # Forex pairs
            "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCAD=X",
            # Commodities
            "GC=F", "SI=F", "CL=F"
        ]
        
        return popular_symbols
    
    def _convert_to_ohlcv(self,
                        instrument: str,
                        timeframe: str,
                        df: pd.DataFrame) -> OHLCV:
        """Convert Yahoo Finance data to OHLCV format."""
        data_points = []
        
        if df.empty:
            return OHLCV(
                instrument=instrument,
                timeframe=timeframe,
                source=self.get_source_type(),
                data=[]
            )
        
        # Handle multi-level column structure if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(0)
        
        # Ensure expected columns exist
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_columns):
            logger.error(f"Missing required columns in Yahoo Finance data: {df.columns}")
            return OHLCV(
                instrument=instrument,
                timeframe=timeframe,
                source=self.get_source_type(),
                data=[]
            )
        
        # Convert DataFrame to OHLCV points
        for timestamp, row in df.iterrows():
            # Yahoo Finance returns timestamps as pandas Timestamp objects
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
                source_id=f"yahoo_{int(dt.timestamp())}"
            ))
        
        return OHLCV(
            instrument=instrument,
            timeframe=timeframe,
            source=self.get_source_type(),
            is_adjusted=True,  # Yahoo Finance data is adjusted
            data=data_points
        )