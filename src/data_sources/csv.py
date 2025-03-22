"""CSV data source connector."""

import logging
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

from .base import DataSourceConnector
from ..models.market_data import OHLCV, OHLCVPoint, DataPointSource

logger = logging.getLogger(__name__)


class CSVConnector(DataSourceConnector):
    """Connector for retrieving market data from local CSV files."""
    
    def _initialize(self):
        """Initialize the CSV connector."""
        self.data_dir = self.config.get('data_dir', './data/csv')
        self.timestamp_column = self.config.get('timestamp_column', 'timestamp')
        self.open_column = self.config.get('open_column', 'open')
        self.high_column = self.config.get('high_column', 'high')
        self.low_column = self.config.get('low_column', 'low')
        self.close_column = self.config.get('close_column', 'close')
        self.volume_column = self.config.get('volume_column', 'volume')
        self.timeframe_pattern = self.config.get('timeframe_pattern', '{instrument}_{timeframe}.csv')
    
    def get_source_type(self) -> DataPointSource:
        """Get the source type for this connector."""
        return DataPointSource.CSV
    
    async def fetch_ohlcv(self, 
                        instrument: str,
                        timeframe: str,
                        start_date: Union[datetime, str],
                        end_date: Union[datetime, str]) -> OHLCV:
        """Fetch OHLCV data from a CSV file."""
        # Convert dates to datetime if they're strings
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        
        try:
            file_path = self._find_csv_file(instrument, timeframe)
            if not file_path or not os.path.exists(file_path):
                logger.error(f"CSV file not found for {instrument}/{timeframe}")
                return OHLCV(instrument=instrument, timeframe=timeframe, source=self.get_source_type(), data=[])
            
            # Read the CSV file into a DataFrame
            df = pd.read_csv(file_path)
            df[self.timestamp_column] = pd.to_datetime(df[self.timestamp_column])
            
            # Filter by date range
            df = df[(df[self.timestamp_column] >= start_date) & (df[self.timestamp_column] <= end_date)]
            
            # Convert to OHLCV format
            ohlcv_data = self._convert_to_ohlcv(instrument, timeframe, df)
            
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
            logger.error(f"Error fetching OHLCV data from CSV: {e}")
            return OHLCV(instrument=instrument, timeframe=timeframe, source=self.get_source_type(), data=[])
    
    async def check_availability(self, instrument: str, timeframe: str) -> Dict[str, Any]:
        """Check if data is available for the specified instrument and timeframe."""
        try:
            file_path = self._find_csv_file(instrument, timeframe)
            if not file_path or not os.path.exists(file_path):
                return {"available": False, "message": f"CSV file not found for {instrument}/{timeframe}"}
            
            # Check if the file has data
            df = pd.read_csv(file_path, nrows=5)  # Just read a few rows to check
            if df.empty:
                return {"available": False, "message": f"CSV file is empty for {instrument}/{timeframe}"}
            
            # Check required columns
            required_columns = [self.timestamp_column, self.open_column, self.high_column, 
                              self.low_column, self.close_column, self.volume_column]
            
            if not all(col in df.columns for col in required_columns):
                missing_cols = [col for col in required_columns if col not in df.columns]
                return {
                    "available": False,
                    "message": f"CSV file is missing required columns: {missing_cols}"
                }
            
            return {"available": True, "message": f"Data available for {instrument}/{timeframe}"}
            
        except Exception as e:
            logger.error(f"Error checking data availability in CSV: {e}")
            return {"available": False, "message": f"Error checking availability: {str(e)}"}
    
    def get_supported_timeframes(self) -> List[str]:
        """Get the list of timeframes supported by CSV files."""
        try:
            if not os.path.exists(self.data_dir):
                return []
            timeframes = set()
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.csv'):
                    parts = filename.split('_')
                    if len(parts) >= 2:
                        timeframe = parts[-1].replace('.csv', '')
                        timeframes.add(timeframe)
            return list(timeframes)
        except Exception as e:
            logger.error(f"Error getting supported timeframes from CSV: {e}")
            return []
    
    def get_supported_instruments(self) -> List[str]:
        """Get the list of instruments supported by CSV files."""
        try:
            if not os.path.exists(self.data_dir):
                return []
            instruments = set()
            for filename in os.listdir(self.data_dir):
                if filename.endswith('.csv'):
                    parts = filename.split('_')
                    if len(parts) >= 2:
                        instrument = '_'.join(parts[:-1])
                        instruments.add(instrument)
            return list(instruments)
        except Exception as e:
            logger.error(f"Error getting supported instruments from CSV: {e}")
            return []
    
    def _find_csv_file(self, instrument: str, timeframe: str) -> Optional[str]:
        """Find the appropriate CSV file for the instrument and timeframe."""
        if not os.path.exists(self.data_dir):
            logger.error(f"Data directory {self.data_dir} does not exist")
            return None
        
        filename = self.timeframe_pattern.format(instrument=instrument, timeframe=timeframe)
        file_path = os.path.join(self.data_dir, filename)
        
        if os.path.exists(file_path):
            return file_path
        
        # Look for alternative CSV files
        for file in os.listdir(self.data_dir):
            if file.startswith(f"{instrument}_") and file.endswith('.csv'):
                logger.warning(f"Using alternative CSV file: {file}")
                return os.path.join(self.data_dir, file)
        
        logger.error(f"No CSV file found for {instrument}/{timeframe}")
        return None
    
    def _convert_to_ohlcv(self, instrument: str, timeframe: str, df: pd.DataFrame) -> OHLCV:
        """Convert CSV data to OHLCV format."""
        data_points = []
        
        if df.empty:
            return OHLCV(instrument=instrument, timeframe=timeframe, source=self.get_source_type(), data=[])
        
        for _, row in df.iterrows():
            timestamp = row[self.timestamp_column]
            if hasattr(timestamp, 'to_pydatetime'):
                dt = timestamp.to_pydatetime()
            else:
                dt = timestamp
                
            data_points.append(OHLCVPoint(
                timestamp=dt,
                open=float(row[self.open_column]),
                high=float(row[self.high_column]),
                low=float(row[self.low_column]),
                close=float(row[self.close_column]),
                volume=float(row[self.volume_column]),
                source_id=f"csv_{int(dt.timestamp())}"
            ))
        
        return OHLCV(
            instrument=instrument,
            timeframe=timeframe,
            source=self.get_source_type(),
            data=data_points
        )