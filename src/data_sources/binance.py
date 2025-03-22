"""Binance data source connector for retrieving market data."""

import logging
import aiohttp
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urlencode

from .base import DataSourceConnector
from ..models.market_data import OHLCV, OHLCVPoint, DataPointSource

logger = logging.getLogger(__name__)


class BinanceConnector(DataSourceConnector):
    """Connector for retrieving market data from Binance."""
    
    # Binance API endpoints
    BASE_URL = 'https://api.binance.com'
    KLINES_ENDPOINT = '/api/v3/klines'
    EXCHANGE_INFO_ENDPOINT = '/api/v3/exchangeInfo'
    
    # Timeframe mapping: internal timeframe to Binance interval
    TIMEFRAME_MAP = {
        '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
        '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h',
        '12h': '12h', '1d': '1d', '3d': '3d', '1w': '1w', '1M': '1M'
    }
    
    def _initialize(self):
        """Initialize the Binance connector."""
        self.api_key = self.config.get('api_key')
        self.api_secret = self.config.get('api_secret')
        self.use_testnet = self.config.get('use_testnet', False)
        
        if self.use_testnet:
            self.BASE_URL = 'https://testnet.binance.vision'
            
        self._supported_symbols = None
        
    def get_source_type(self) -> DataPointSource:
        """Get the source type for this connector."""
        return DataPointSource.BINANCE
    
    async def fetch_ohlcv(self, 
                        instrument: str,
                        timeframe: str,
                        start_date: Union[datetime, str],
                        end_date: Union[datetime, str]) -> OHLCV:
        """Fetch OHLCV data from Binance."""
        # Convert dates to millisecond timestamps
        if isinstance(start_date, datetime):
            start_timestamp = int(start_date.timestamp() * 1000)
        else:
            start_timestamp = int(datetime.fromisoformat(start_date).timestamp() * 1000)
            
        if isinstance(end_date, datetime):
            end_timestamp = int(end_date.timestamp() * 1000)
        else:
            end_timestamp = int(datetime.fromisoformat(end_date).timestamp() * 1000)
        
        # Map internal timeframe to Binance interval
        interval = self.TIMEFRAME_MAP.get(timeframe)
        if not interval:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        # Prepare for chunked requests (Binance has a limit of 1000 candles per request)
        all_candles = []
        current_start = start_timestamp
        
        try:
            while current_start < end_timestamp:
                # Fetch a chunk of data
                candles = await self._fetch_klines(
                    symbol=instrument,
                    interval=interval,
                    start_time=current_start,
                    end_time=end_timestamp,
                    limit=1000
                )
                
                if not candles:
                    break
                
                all_candles.extend(candles)
                
                # Update the start time for the next chunk
                if candles:
                    last_timestamp = candles[-1][0]
                    current_start = last_timestamp + 1
                else:
                    break
            
            # Convert candles to OHLCV format
            ohlcv_data = self._convert_to_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                candles=all_candles
            )
            
            # Cache the data to InfluxDB if enabled
            if all_candles and self.cache_to_influxdb:
                await self._cache_to_influxdb(
                    instrument=instrument,
                    timeframe=timeframe,
                    data=[point.dict() for point in ohlcv_data.data],
                    is_adjusted=False
                )
            
            return ohlcv_data
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV data from Binance: {e}")
            return OHLCV(
                instrument=instrument,
                timeframe=timeframe,
                source=self.get_source_type(),
                data=[]
            )
    
    async def check_availability(self, instrument: str, timeframe: str) -> Dict[str, Any]:
        """Check if data is available for the specified instrument and timeframe."""
        try:
            supported_instruments = await self.get_supported_instruments_async()
            if instrument not in supported_instruments:
                return {
                    "available": False,
                    "message": f"Instrument {instrument} not available on Binance"
                }
            
            if timeframe not in self.get_supported_timeframes():
                return {
                    "available": False,
                    "message": f"Timeframe {timeframe} not supported by Binance"
                }
            
            # Try to fetch a small amount of recent data to verify
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            
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
            logger.error(f"Error checking data availability on Binance: {e}")
            return {
                "available": False,
                "message": f"Error checking availability: {str(e)}"
            }
    
    def get_supported_timeframes(self) -> List[str]:
        """Get the list of timeframes supported by Binance."""
        return list(self.TIMEFRAME_MAP.keys())
    
    def get_supported_instruments(self) -> List[str]:
        """Get the list of instruments supported by Binance."""
        import requests
        
        if self._supported_symbols is not None:
            return self._supported_symbols
        
        try:
            response = requests.get(f"{self.BASE_URL}{self.EXCHANGE_INFO_ENDPOINT}")
            response.raise_for_status()
            data = response.json()
            
            symbols = [symbol['symbol'] for symbol in data['symbols'] 
                      if symbol['status'] == 'TRADING']
            self._supported_symbols = symbols
            
            return symbols
            
        except Exception as e:
            logger.error(f"Error fetching supported instruments from Binance: {e}")
            return []
    
    async def get_supported_instruments_async(self) -> List[str]:
        """Get the list of instruments supported by Binance (async version)."""
        if self._supported_symbols is not None:
            return self._supported_symbols
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}{self.EXCHANGE_INFO_ENDPOINT}"
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Error fetching exchange info: {response.status}")
                        return []
                    
                    data = await response.json()
                    
                    symbols = [symbol['symbol'] for symbol in data['symbols'] 
                              if symbol['status'] == 'TRADING']
                    self._supported_symbols = symbols
                    
                    return symbols
                    
        except Exception as e:
            logger.error(f"Error fetching supported instruments from Binance: {e}")
            return []
    
    async def _fetch_klines(self, symbol: str, interval: str, 
                          start_time: int, end_time: int, limit: int = 1000) -> List[List]:
        """Fetch klines (candlestick data) from Binance API."""
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_time,
            'endTime': end_time,
            'limit': limit
        }
        
        if self.api_key:
            params['timestamp'] = int(time.time() * 1000)
            query_string = urlencode(params)
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            params['signature'] = signature
            headers = {'X-MBX-APIKEY': self.api_key}
        else:
            headers = {}
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}{self.KLINES_ENDPOINT}"
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"Error fetching klines: {response.status}")
                        return []
                    
                    return await response.json()
                    
        except Exception as e:
            logger.error(f"Error fetching klines from Binance: {e}")
            return []
    
    def _convert_to_ohlcv(self, instrument: str, timeframe: str, candles: List[List]) -> OHLCV:
        """Convert Binance candles to OHLCV format."""
        data_points = []
        
        for candle in candles:
            timestamp = datetime.fromtimestamp(candle[0] / 1000)  # Convert ms to seconds
            
            data_points.append(OHLCVPoint(
                timestamp=timestamp,
                open=float(candle[1]),
                high=float(candle[2]),
                low=float(candle[3]),
                close=float(candle[4]),
                volume=float(candle[5]),
                source_id=f"binance_{candle[0]}"
            ))
        
        return OHLCV(
            instrument=instrument,
            timeframe=timeframe,
            source=self.get_source_type(),
            data=data_points
        )