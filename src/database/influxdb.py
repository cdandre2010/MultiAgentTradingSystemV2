"""
InfluxDB client for market data with versioning and audit capabilities.

This module provides a client for interacting with InfluxDB to store and retrieve
market data with support for versioning, data snapshots, and integrity verification.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
import uuid
import json
import hashlib

from influxdb_client import InfluxDBClient as BaseInfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

logger = logging.getLogger(__name__)

class InfluxDBClient:
    """
    Client for interacting with InfluxDB with version awareness and data integrity features.
    
    This client provides methods for storing, retrieving, and managing market data
    in InfluxDB with support for versioning, data snapshots, and integrity verification.
    """
    
    def __init__(self, url: str, token: str, org: str, bucket: str = "market_data"):
        """
        Initialize the InfluxDB client.
        
        Args:
            url: The URL of the InfluxDB instance
            token: The authentication token
            org: The organization name
            bucket: The bucket name for market data (default: "market_data")
        """
        self.client = BaseInfluxDBClient(url=url, token=token, org=org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        self.delete_api = self.client.delete_api()
        self.bucket = bucket
        self.org = org
        
        # Additional buckets for metadata
        self.audit_bucket = "data_audit"
        
        logger.info(f"InfluxDB client initialized for {bucket} bucket in {org} organization")
        
    def health_check(self) -> bool:
        """
        Check if the InfluxDB connection is healthy.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            health = self.client.health()
            return health.status == "pass"
        except Exception as e:
            logger.error(f"InfluxDB health check failed: {e}")
            return False
    
    def write_ohlcv(self, 
                   instrument: str, 
                   timeframe: str, 
                   data: List[Dict[str, Any]], 
                   source: str, 
                   version: str = "latest", 
                   is_adjusted: bool = False) -> bool:
        """
        Write OHLCV data to InfluxDB with versioning metadata.
        
        Args:
            instrument: The instrument symbol (e.g., "BTCUSDT")
            timeframe: The timeframe (e.g., "1m", "1h", "1d")
            data: List of OHLCV data points
            source: The data source (e.g., "binance", "yahoo")
            version: The version tag (default: "latest")
            is_adjusted: Whether the data is adjusted for corporate actions
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            points = []
            
            for point in data:
                # Ensure timestamp is in the correct format
                if isinstance(point.get("timestamp"), datetime):
                    timestamp = point["timestamp"]
                elif isinstance(point.get("timestamp"), str):
                    timestamp = datetime.fromisoformat(point["timestamp"])
                else:
                    timestamp = datetime.fromtimestamp(point["timestamp"]/1000) if "timestamp" in point else datetime.now()
                
                # Create the data point with tags and fields
                point_data = {
                    "measurement": "market_data",
                    "tags": {
                        "instrument": instrument,
                        "timeframe": timeframe,
                        "source": source,
                        "version": version,
                        "is_adjusted": str(is_adjusted).lower()  # InfluxDB tags must be strings
                    },
                    "time": timestamp,
                    "fields": {
                        "open": float(point.get("open", 0)),
                        "high": float(point.get("high", 0)),
                        "low": float(point.get("low", 0)),
                        "close": float(point.get("close", 0)),
                        "volume": float(point.get("volume", 0))
                    }
                }
                
                # Add optional fields if present
                if "adjustment_factor" in point:
                    point_data["fields"]["adjustment_factor"] = float(point["adjustment_factor"])
                if "source_id" in point:
                    point_data["fields"]["source_id"] = str(point["source_id"])
                
                points.append(point_data)
            
            # Write the data points to InfluxDB
            self.write_api.write(bucket=self.bucket, record=points)
            
            logger.info(f"Wrote {len(data)} data points for {instrument}/{timeframe} from {source} with version {version}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing OHLCV data: {e}")
            return False
    
    def query_ohlcv(self, 
                   instrument: str, 
                   timeframe: str, 
                   start_date: Union[datetime, str], 
                   end_date: Union[datetime, str], 
                   version: str = "latest") -> List[Dict[str, Any]]:
        """
        Query OHLCV data from InfluxDB with version support.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            start_date: The start date
            end_date: The end date
            version: The version tag (default: "latest")
            
        Returns:
            List of OHLCV data points
        """
        try:
            # Convert dates to ISO format if they are datetime objects
            start_date_str = start_date.isoformat() if isinstance(start_date, datetime) else start_date
            end_date_str = end_date.isoformat() if isinstance(end_date, datetime) else end_date
            
            # Construct the Flux query
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {start_date_str}, stop: {end_date_str})
                |> filter(fn: (r) => r["_measurement"] == "market_data")
                |> filter(fn: (r) => r["instrument"] == "{instrument}")
                |> filter(fn: (r) => r["timeframe"] == "{timeframe}")
                |> filter(fn: (r) => r["version"] == "{version}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            # Execute the query
            tables = self.query_api.query(query, org=self.org)
            
            # Convert the results to a list of dictionaries
            results = []
            for table in tables:
                for record in table.records:
                    # Create a dictionary with all the fields
                    point = {
                        "timestamp": record.get_time(),
                        "open": record.get_value("open"),
                        "high": record.get_value("high"),
                        "low": record.get_value("low"),
                        "close": record.get_value("close"),
                        "volume": record.get_value("volume")
                    }
                    
                    # Add optional fields if present
                    if record.get_value("adjustment_factor") is not None:
                        point["adjustment_factor"] = record.get_value("adjustment_factor")
                    if record.get_value("source_id") is not None:
                        point["source_id"] = record.get_value("source_id")
                    
                    results.append(point)
            
            logger.info(f"Retrieved {len(results)} data points for {instrument}/{timeframe} with version {version}")
            return results
            
        except Exception as e:
            logger.error(f"Error querying OHLCV data: {e}")
            return []
    
    def create_snapshot(self, 
                       instrument: str, 
                       timeframe: str, 
                       start_date: Union[datetime, str], 
                       end_date: Union[datetime, str], 
                       snapshot_id: Optional[str] = None, 
                       strategy_id: Optional[str] = None,
                       purpose: str = "backtest") -> str:
        """
        Create a point-in-time snapshot of data for audit purposes.
        
        This function creates a new version of the data by copying the latest version
        to a new version with a unique snapshot ID. It also records metadata about
        the snapshot for audit purposes.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            start_date: The start date
            end_date: The end date
            snapshot_id: Optional snapshot ID (generated if None)
            strategy_id: Optional strategy ID for tracking
            purpose: The purpose of the snapshot (default: "backtest")
            
        Returns:
            str: The snapshot ID
        """
        # Generate a snapshot ID if not provided
        if snapshot_id is None:
            snapshot_id = f"snapshot_{uuid.uuid4()}"
        
        try:
            # Query the latest data
            data = self.query_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                version="latest"
            )
            
            if not data:
                logger.warning(f"No data found to create snapshot for {instrument}/{timeframe}")
                return ""
            
            # Create a data hash for integrity verification
            data_str = json.dumps(data, default=str, sort_keys=True)
            data_hash = hashlib.sha256(data_str.encode()).hexdigest()
            
            # Write the data with the new snapshot version
            success = self.write_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                data=data,
                source="snapshot",
                version=snapshot_id,
                is_adjusted=any("adjustment_factor" in point for point in data)
            )
            
            if not success:
                logger.error(f"Failed to create snapshot {snapshot_id} for {instrument}/{timeframe}")
                return ""
            
            # Record snapshot metadata
            audit_point = {
                "measurement": "data_audit",
                "tags": {
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "snapshot_id": snapshot_id,
                    "strategy_id": strategy_id or "none"
                },
                "time": datetime.now(),
                "fields": {
                    "source_versions": json.dumps({"latest": True}),
                    "created_by": "system",  # TODO: Add user ID when available
                    "purpose": purpose,
                    "data_hash": data_hash,
                    "data_points": len(data),
                    "start_date": start_date.isoformat() if isinstance(start_date, datetime) else start_date,
                    "end_date": end_date.isoformat() if isinstance(end_date, datetime) else end_date
                }
            }
            
            self.write_api.write(bucket=self.audit_bucket, record=audit_point)
            
            logger.info(f"Created snapshot {snapshot_id} for {instrument}/{timeframe} with {len(data)} data points")
            return snapshot_id
            
        except Exception as e:
            logger.error(f"Error creating snapshot: {e}")
            return ""
    
    def check_for_adjustments(self, 
                             instrument: str, 
                             timeframe: str, 
                             reference_date: Optional[Union[datetime, str]] = None) -> Dict[str, Any]:
        """
        Check if data has been adjusted since reference date.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            reference_date: The reference date (default: 30 days ago)
            
        Returns:
            Dict containing adjustment information
        """
        try:
            # Set default reference date if not provided
            if reference_date is None:
                reference_date = datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) - timedelta(days=30)
            
            # Convert date to ISO format if it's a datetime object
            reference_date_str = reference_date.isoformat() if isinstance(reference_date, datetime) else reference_date
            
            # Query for data points with adjustment factors
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {reference_date_str})
                |> filter(fn: (r) => r["_measurement"] == "market_data")
                |> filter(fn: (r) => r["instrument"] == "{instrument}")
                |> filter(fn: (r) => r["timeframe"] == "{timeframe}")
                |> filter(fn: (r) => r["version"] == "latest")
                |> filter(fn: (r) => r["is_adjusted"] == "true")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            tables = self.query_api.query(query, org=self.org)
            
            adjusted_points = []
            for table in tables:
                for record in table.records:
                    adjusted_points.append({
                        "timestamp": record.get_time(),
                        "adjustment_factor": record.get_value("adjustment_factor"),
                        "open": record.get_value("open"),
                        "close": record.get_value("close")
                    })
            
            has_adjustments = len(adjusted_points) > 0
            
            result = {
                "has_adjustments": has_adjustments,
                "adjustment_count": len(adjusted_points),
                "adjustment_details": adjusted_points[:5] if has_adjustments else []  # Only include first 5 for brevity
            }
            
            logger.info(f"Checked for adjustments for {instrument}/{timeframe}: found {len(adjusted_points)}")
            return result
            
        except Exception as e:
            logger.error(f"Error checking for adjustments: {e}")
            return {"has_adjustments": False, "error": str(e)}
    
    def get_data_versions(self, instrument: str, timeframe: str) -> List[str]:
        """
        Get available data versions for an instrument/timeframe.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            
        Returns:
            List of available versions
        """
        try:
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -1y)
                |> filter(fn: (r) => r["_measurement"] == "market_data")
                |> filter(fn: (r) => r["instrument"] == "{instrument}")
                |> filter(fn: (r) => r["timeframe"] == "{timeframe}")
                |> group(columns: ["version"])
                |> distinct(column: "version")
            '''
            
            tables = self.query_api.query(query, org=self.org)
            
            versions = []
            for table in tables:
                for record in table.records:
                    versions.append(record.values.get("version"))
            
            logger.info(f"Found {len(versions)} versions for {instrument}/{timeframe}")
            return versions
            
        except Exception as e:
            logger.error(f"Error getting data versions: {e}")
            return []
    
    def check_data_availability(self, 
                               instrument: str, 
                               timeframe: str, 
                               start_date: Union[datetime, str], 
                               end_date: Union[datetime, str], 
                               version: str = "latest") -> Dict[str, Any]:
        """
        Check if data is available for a specific time range.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            start_date: The start date
            end_date: The end date
            version: The version tag (default: "latest")
            
        Returns:
            Dict containing availability information
        """
        try:
            # Convert dates to ISO format if they are datetime objects
            start_date_str = start_date.isoformat() if isinstance(start_date, datetime) else start_date
            end_date_str = end_date.isoformat() if isinstance(end_date, datetime) else end_date
            
            # Calculate the expected number of data points based on timeframe
            timeframe_duration = self._get_timeframe_duration_minutes(timeframe)
            
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
                
            expected_points = self._calculate_expected_points(
                start_date, end_date, timeframe_duration
            )
            
            # Count actual data points
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {start_date_str}, stop: {end_date_str})
                |> filter(fn: (r) => r["_measurement"] == "market_data")
                |> filter(fn: (r) => r["instrument"] == "{instrument}")
                |> filter(fn: (r) => r["timeframe"] == "{timeframe}")
                |> filter(fn: (r) => r["version"] == "{version}")
                |> filter(fn: (r) => r["_field"] == "close")
                |> count()
            '''
            
            tables = self.query_api.query(query, org=self.org)
            
            actual_points = 0
            for table in tables:
                for record in table.records:
                    actual_points = record.get_value()
            
            # Calculate availability percentage
            availability_pct = (actual_points / expected_points * 100) if expected_points > 0 else 0
            
            result = {
                "instrument": instrument,
                "timeframe": timeframe,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "expected_points": expected_points,
                "actual_points": actual_points,
                "missing_points": expected_points - actual_points,
                "availability_pct": availability_pct,
                "is_complete": actual_points >= expected_points,
                "version": version
            }
            
            logger.info(
                f"Data availability for {instrument}/{timeframe}: {availability_pct:.2f}% "
                f"({actual_points}/{expected_points} points)"
            )
            return result
            
        except Exception as e:
            logger.error(f"Error checking data availability: {e}")
            return {
                "instrument": instrument,
                "timeframe": timeframe,
                "error": str(e),
                "is_complete": False
            }
    
    def _get_timeframe_duration_minutes(self, timeframe: str) -> int:
        """
        Convert a timeframe string to minutes.
        
        Args:
            timeframe: The timeframe string (e.g., "1m", "1h", "1d")
            
        Returns:
            int: The duration in minutes
        """
        # Handle common timeframe formats
        if timeframe.endswith('m'):
            return int(timeframe[:-1])
        elif timeframe.endswith('h'):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith('d'):
            return int(timeframe[:-1]) * 60 * 24
        elif timeframe.endswith('w'):
            return int(timeframe[:-1]) * 60 * 24 * 7
        else:
            # Default to 1 minute if unknown format
            logger.warning(f"Unknown timeframe format: {timeframe}, defaulting to 1 minute")
            return 1
    
    def _calculate_expected_points(self, 
                                 start_date: datetime, 
                                 end_date: datetime, 
                                 timeframe_minutes: int) -> int:
        """
        Calculate the expected number of data points for a time range.
        
        Args:
            start_date: The start date
            end_date: The end date
            timeframe_minutes: The timeframe duration in minutes
            
        Returns:
            int: The expected number of data points
        """
        # Calculate the total minutes in the range
        delta = end_date - start_date
        total_minutes = delta.total_seconds() / 60
        
        # Calculate expected points
        expected_points = int(total_minutes / timeframe_minutes) + 1
        
        return max(expected_points, 0)  # Ensure non-negative result
    
    def close(self):
        """Close the InfluxDB client connection."""
        self.client.close()
        logger.info("InfluxDB client connection closed")