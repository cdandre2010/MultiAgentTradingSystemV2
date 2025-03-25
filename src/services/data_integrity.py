"""
Data integrity and adjustment detection service.

This module provides services for detecting data discrepancies, corporate actions,
and implementing data correction workflows to ensure data integrity.
"""

import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple, Set
import numpy as np
import pandas as pd
from enum import Enum

from ..database.influxdb import InfluxDBClient
from ..models.market_data import (
    OHLCV, 
    OHLCVPoint, 
    DataSnapshotMetadata,
    AdjustmentInfo,
    MarketDataRequest
)
from .data_versioning import DataVersioningService

logger = logging.getLogger(__name__)


class AdjustmentType(str, Enum):
    """Types of adjustments that can be detected in market data."""
    SPLIT = "split"
    DIVIDEND = "dividend"
    MERGER = "merger"
    SPINOFF = "spinoff"
    RENAME = "rename"
    DELISTING = "delisting"
    GAP = "gap"
    CORRECTION = "correction"
    UNKNOWN = "unknown"


class DataDiscrepancyType(str, Enum):
    """Types of data discrepancies that can be detected."""
    PRICE_OUTLIER = "price_outlier"
    VOLUME_OUTLIER = "volume_outlier"
    MISSING_DATA = "missing_data"
    SOURCE_CONFLICT = "source_conflict"
    TIMESTAMP_IRREGULARITY = "timestamp_irregularity"
    VALUE_CHANGE = "value_change"
    DUPLICATE_DATA = "duplicate_data"


class DataIntegrityService:
    """
    Service for detecting data discrepancies, corporate actions, and implementing
    data correction workflows to ensure data integrity.
    
    This service provides methods for reconciling data with external sources,
    detecting potential issues, managing adjustments, and ensuring data quality.
    """
    
    def __init__(self,
                influxdb_client: InfluxDBClient,
                versioning_service: Optional[DataVersioningService] = None):
        """
        Initialize the service.
        
        Args:
            influxdb_client: The InfluxDB client
            versioning_service: Optional DataVersioningService for version management
        """
        self.influxdb = influxdb_client
        self.versioning_service = versioning_service or DataVersioningService(influxdb_client)
        
        # Configuration settings for anomaly detection
        self.config = {
            # Z-score threshold for outlier detection
            "z_score_threshold": 3.0,
            
            # Price change thresholds (percentage)
            "price_spike_threshold": 10.0,  # 10% change in a single period
            "price_gap_threshold": 5.0,     # 5% gap between close and next open
            
            # Volume thresholds
            "volume_spike_factor": 5.0,     # 5x average volume
            
            # Split detection threshold
            "split_ratio_threshold": 0.3,   # 30% price drop with volume increase
            
            # Confidence thresholds for different adjustment types
            "adjustment_confidence_threshold": {
                AdjustmentType.SPLIT: 0.8,
                AdjustmentType.DIVIDEND: 0.7,
                AdjustmentType.MERGER: 0.9,
                AdjustmentType.SPINOFF: 0.85,
                AdjustmentType.GAP: 0.6,
                AdjustmentType.CORRECTION: 0.7,
                AdjustmentType.UNKNOWN: 0.5
            },
            
            # Time window for analysis (in units of timeframe)
            "analysis_window": 20,
            
            # Minimum data points required for reliable detection
            "min_data_points": 30
        }
    
    async def detect_anomalies(self,
                             instrument: str,
                             timeframe: str,
                             start_date: Union[datetime, str],
                             end_date: Union[datetime, str],
                             version: str = "latest") -> Dict[str, Any]:
        """
        Detect anomalies in market data for a specific period.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            start_date: The start date
            end_date: The end date
            version: The data version to analyze
            
        Returns:
            Dict containing detected anomalies with categorization and confidence scores
        """
        try:
            # Retrieve data for analysis
            data = self.influxdb.query_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                version=version
            )
            
            if not data or len(data) < self.config["min_data_points"]:
                logger.warning(
                    f"Insufficient data points ({len(data) if data else 0}) for "
                    f"reliable anomaly detection. Minimum required: {self.config['min_data_points']}"
                )
                return {
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "start_date": start_date if isinstance(start_date, str) else start_date.isoformat(),
                    "end_date": end_date if isinstance(end_date, str) else end_date.isoformat(),
                    "version": version,
                    "anomalies": [],
                    "warning": "Insufficient data points for reliable analysis"
                }
            
            # Convert to pandas DataFrame for analysis
            df = pd.DataFrame(data)
            df = df.sort_values("timestamp")
            
            # Calculate metrics for anomaly detection
            anomalies = []
            
            # 1. Detect price outliers using Z-score
            price_anomalies = self._detect_price_anomalies(df)
            anomalies.extend(price_anomalies)
            
            # 2. Detect volume outliers
            volume_anomalies = self._detect_volume_anomalies(df)
            anomalies.extend(volume_anomalies)
            
            # 3. Detect price gaps
            gap_anomalies = self._detect_price_gaps(df)
            anomalies.extend(gap_anomalies)
            
            # 4. Detect potential corporate actions
            corporate_action_anomalies = self._detect_potential_corporate_actions(df)
            anomalies.extend(corporate_action_anomalies)
            
            # 5. Detect timestamp irregularities
            timestamp_anomalies = self._detect_timestamp_irregularities(df, timeframe)
            anomalies.extend(timestamp_anomalies)
            
            # Group anomalies by date for easier analysis
            grouped_anomalies = {}
            for anomaly in anomalies:
                date_str = anomaly["timestamp"].isoformat() if isinstance(anomaly["timestamp"], datetime) else anomaly["timestamp"]
                if date_str not in grouped_anomalies:
                    grouped_anomalies[date_str] = []
                grouped_anomalies[date_str].append(anomaly)
            
            # Sort by confidence (highest first)
            sorted_anomalies = sorted(
                anomalies, 
                key=lambda x: x.get("confidence", 0), 
                reverse=True
            )
            
            # Generate summary
            summary = {
                "total_anomalies": len(anomalies),
                "high_confidence_anomalies": len([a for a in anomalies if a.get("confidence", 0) >= 0.8]),
                "medium_confidence_anomalies": len([a for a in anomalies if 0.5 <= a.get("confidence", 0) < 0.8]),
                "low_confidence_anomalies": len([a for a in anomalies if a.get("confidence", 0) < 0.5]),
                "anomaly_types": {},
                "most_significant_date": max(grouped_anomalies.keys(), key=lambda d: sum(a.get("confidence", 0) for a in grouped_anomalies[d])) if grouped_anomalies else None
            }
            
            # Count anomaly types for summary
            for anomaly in anomalies:
                anomaly_type = anomaly.get("type", "unknown")
                if anomaly_type not in summary["anomaly_types"]:
                    summary["anomaly_types"][anomaly_type] = 0
                summary["anomaly_types"][anomaly_type] += 1
            
            return {
                "instrument": instrument,
                "timeframe": timeframe,
                "start_date": start_date if isinstance(start_date, str) else start_date.isoformat(),
                "end_date": end_date if isinstance(end_date, str) else end_date.isoformat(),
                "version": version,
                "anomalies": sorted_anomalies[:100] if len(sorted_anomalies) > 100 else sorted_anomalies,  # Limit to top 100 anomalies
                "grouped_anomalies": grouped_anomalies,
                "summary": summary,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return {
                "instrument": instrument,
                "timeframe": timeframe,
                "error": str(e)
            }
    
    async def reconcile_with_source(self,
                                  instrument: str,
                                  timeframe: str,
                                  source: str,
                                  start_date: Union[datetime, str],
                                  end_date: Union[datetime, str],
                                  create_adjustment: bool = False) -> Dict[str, Any]:
        """
        Reconcile cached data with external source to detect discrepancies.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            source: The external data source to compare with
            start_date: The start date
            end_date: The end date
            create_adjustment: Whether to automatically create adjustments for discrepancies
            
        Returns:
            Dict containing reconciliation results and identified discrepancies
        """
        try:
            # Get data from InfluxDB (cached data)
            cached_data = self.influxdb.query_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                version="latest"
            )
            
            if not cached_data:
                logger.warning(f"No cached data found for {instrument}/{timeframe}")
                return {
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "status": "failed",
                    "reason": "No cached data available for comparison"
                }
            
            # Import the appropriate connector based on source
            if source.lower() == "binance":
                from ..data_sources.binance import BinanceConnector
                connector_class = BinanceConnector
            elif source.lower() == "yfinance":
                from ..data_sources.yfinance import YFinanceConnector
                connector_class = YFinanceConnector
            elif source.lower() == "alpha_vantage":
                from ..data_sources.alpha_vantage import AlphaVantageConnector
                connector_class = AlphaVantageConnector
            elif source.lower() == "csv":
                from ..data_sources.csv import CSVConnector
                connector_class = CSVConnector
            else:
                return {
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "status": "failed",
                    "reason": f"Unknown source: {source}"
                }
            
            # Create connector instance (do not cache to InfluxDB to avoid circular issues)
            connector = connector_class(
                config={},
                cache_to_influxdb=False,
                influxdb_client=None
            )
            
            # Fetch data from source
            source_data = await connector.fetch_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if not source_data or not source_data.data:
                logger.warning(f"No source data found for {instrument}/{timeframe} from {source}")
                return {
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "status": "failed",
                    "reason": f"No source data available from {source}"
                }
            
            # Convert both datasets to dictionaries with timestamps as keys
            cached_dict = {self._timestamp_to_str(point["timestamp"]): point for point in cached_data}
            source_dict = {self._timestamp_to_str(point.timestamp): {
                "open": point.open,
                "high": point.high,
                "low": point.low,
                "close": point.close,
                "volume": point.volume
            } for point in source_data.data}
            
            # Find common timestamps and compare values
            common_timestamps = set(cached_dict.keys()) & set(source_dict.keys())
            discrepancies = []
            
            for ts in common_timestamps:
                cached_point = cached_dict[ts]
                source_point = source_dict[ts]
                
                # Compare values with tolerance for float precision issues
                diff_dict = {}
                for field in ["open", "high", "low", "close", "volume"]:
                    cached_value = cached_point.get(field, 0)
                    source_value = source_point.get(field, 0)
                    
                    # For volume, use a higher threshold as it can vary more
                    threshold = 0.0001 if field != "volume" else 0.01
                    
                    if cached_value == 0 and source_value == 0:
                        continue
                    
                    if cached_value == 0:
                        pct_diff = 100.0  # Arbitrary large number
                    else:
                        pct_diff = abs((source_value - cached_value) / cached_value) * 100
                    
                    if pct_diff > threshold:
                        diff_dict[field] = {
                            "cached": cached_value,
                            "source": source_value,
                            "diff": source_value - cached_value,
                            "pct_diff": pct_diff
                        }
                
                if diff_dict:
                    discrepancies.append({
                        "timestamp": ts,
                        "differences": diff_dict,
                        "severity": self._calculate_discrepancy_severity(diff_dict)
                    })
            
            # Find missing timestamps in each direction
            missing_in_cached = set(source_dict.keys()) - set(cached_dict.keys())
            missing_in_source = set(cached_dict.keys()) - set(source_dict.keys())
            
            # Calculate adjustment recommendation if there are systematic discrepancies
            adjustment_recommendation = None
            if discrepancies:
                adjustment_recommendation = self._calculate_adjustment_recommendation(
                    discrepancies, instrument, timeframe
                )
            
            # Create automatic adjustment if requested and we have a high-confidence recommendation
            adjustment_created = False
            if (
                create_adjustment and 
                adjustment_recommendation and 
                adjustment_recommendation.get("confidence", 0) >= 0.8
            ):
                await self._create_adjustment(
                    instrument=instrument,
                    timeframe=timeframe,
                    adjustment_type=adjustment_recommendation["type"],
                    adjustment_data=adjustment_recommendation,
                    source=source
                )
                adjustment_created = True
            
            # Sort discrepancies by severity (highest first)
            discrepancies.sort(key=lambda x: x["severity"], reverse=True)
            
            return {
                "instrument": instrument,
                "timeframe": timeframe,
                "source": source,
                "start_date": start_date if isinstance(start_date, str) else start_date.isoformat(),
                "end_date": end_date if isinstance(end_date, str) else end_date.isoformat(),
                "reconciliation_timestamp": datetime.now().isoformat(),
                "total_cached_points": len(cached_dict),
                "total_source_points": len(source_dict),
                "common_points": len(common_timestamps),
                "missing_in_cached": list(missing_in_cached)[:100] if len(missing_in_cached) > 100 else list(missing_in_cached),
                "missing_in_source": list(missing_in_source)[:100] if len(missing_in_source) > 100 else list(missing_in_source),
                "discrepancies": discrepancies[:100] if len(discrepancies) > 100 else discrepancies,
                "total_discrepancies": len(discrepancies),
                "adjustment_recommendation": adjustment_recommendation,
                "adjustment_created": adjustment_created,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error reconciling data with source: {e}")
            return {
                "instrument": instrument,
                "timeframe": timeframe,
                "source": source,
                "status": "error",
                "error": str(e)
            }
    
    async def detect_corporate_actions(self,
                                    instrument: str,
                                    timeframe: str,
                                    start_date: Union[datetime, str],
                                    end_date: Union[datetime, str],
                                    version: str = "latest") -> Dict[str, Any]:
        """
        Detect potential corporate actions like splits and dividends.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            start_date: The start date
            end_date: The end date
            version: The data version to analyze
            
        Returns:
            Dict containing detected corporate actions with confidence scores
        """
        try:
            # Retrieve data for analysis
            data = self.influxdb.query_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                version=version
            )
            
            if not data or len(data) < self.config["min_data_points"]:
                logger.warning(
                    f"Insufficient data points ({len(data) if data else 0}) for "
                    f"reliable corporate action detection. Minimum required: {self.config['min_data_points']}"
                )
                return {
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "corporate_actions": [],
                    "warning": "Insufficient data points for reliable analysis"
                }
            
            # Convert to pandas DataFrame for analysis
            df = pd.DataFrame(data)
            df = df.sort_values("timestamp")
            
            # Run specialized detection algorithms
            corporate_actions = []
            
            # 1. Stock split detection
            splits = self._detect_stock_splits(df)
            corporate_actions.extend(splits)
            
            # 2. Dividend detection
            dividends = self._detect_dividends(df)
            corporate_actions.extend(dividends)
            
            # 3. Merger/acquisition detection
            mergers = self._detect_mergers(df)
            corporate_actions.extend(mergers)
            
            # Sort by confidence (highest first)
            corporate_actions.sort(key=lambda x: x.get("confidence", 0), reverse=True)
            
            return {
                "instrument": instrument,
                "timeframe": timeframe,
                "start_date": start_date if isinstance(start_date, str) else start_date.isoformat(),
                "end_date": end_date if isinstance(end_date, str) else end_date.isoformat(),
                "version": version,
                "corporate_actions": corporate_actions,
                "total_detected": len(corporate_actions),
                "high_confidence_actions": len([a for a in corporate_actions if a.get("confidence", 0) >= 0.8]),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error detecting corporate actions: {e}")
            return {
                "instrument": instrument,
                "timeframe": timeframe,
                "error": str(e)
            }
    
    async def create_adjustment(self,
                             instrument: str,
                             timeframe: str,
                             adjustment_type: str,
                             adjustment_factor: float,
                             reference_date: Union[datetime, str],
                             description: Optional[str] = None,
                             affected_fields: Optional[List[str]] = None,
                             source: Optional[str] = None,
                             user_id: str = "system") -> Dict[str, Any]:
        """
        Create a market data adjustment and apply it to create a new version.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            adjustment_type: Type of adjustment (split, dividend, etc.)
            adjustment_factor: The adjustment factor to apply
            reference_date: The reference date for the adjustment
            description: Optional description of the adjustment
            affected_fields: Fields to adjust (defaults to price fields only)
            source: Optional source of adjustment information
            user_id: The user creating the adjustment
            
        Returns:
            Dict containing adjustment results and new version information
        """
        try:
            # Set default affected fields if not provided
            if affected_fields is None:
                # For most adjustments, we only adjust price fields
                affected_fields = ["open", "high", "low", "close"]
                
                # For some adjustment types (like splits), also adjust volume
                if adjustment_type.lower() in [AdjustmentType.SPLIT.value, AdjustmentType.MERGER.value]:
                    affected_fields.append("volume")
            
            # Normalize adjustment type
            adj_type = adjustment_type.lower()
            
            # Get data to adjust
            data = self.influxdb.query_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                # For adjustments, we need all historical data up to the reference date
                start_date=datetime(2000, 1, 1),  # Far in the past
                end_date=reference_date,
                version="latest"
            )
            
            if not data:
                logger.warning(f"No data found to adjust for {instrument}/{timeframe}")
                return {
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "status": "failed",
                    "reason": "No data available to adjust"
                }
            
            # Create a snapshot of the original data before adjustment
            snapshot_id = await self.versioning_service.create_snapshot(
                instrument=instrument,
                timeframe=timeframe,
                start_date=datetime(2000, 1, 1),  # Far in the past
                end_date=reference_date,
                user_id=user_id,
                purpose="pre_adjustment",
                tags={
                    "adjustment_type": adj_type,
                    "adjustment_factor": str(adjustment_factor)
                },
                description=f"Pre-adjustment snapshot for {adj_type} on {reference_date}"
            )
            
            # Apply the adjustment to the data
            adjusted_data = []
            for point in data:
                adjusted_point = point.copy()
                
                # For each affected field, apply the adjustment
                for field in affected_fields:
                    if field in point:
                        # Different adjustments are applied differently
                        if adj_type == AdjustmentType.SPLIT.value:
                            if field == "volume":
                                # For splits, volume is multiplied by the factor
                                adjusted_point[field] = point[field] * adjustment_factor
                            else:
                                # For splits, prices are divided by the factor
                                adjusted_point[field] = point[field] / adjustment_factor
                        else:
                            # For most other adjustments, we apply the factor directly
                            adjusted_point[field] = point[field] * adjustment_factor
                
                # Add adjustment metadata
                adjusted_point["adjustment_factor"] = adjustment_factor
                adjusted_data.append(adjusted_point)
            
            # Generate a new version ID for the adjusted data
            adjustment_version = f"adj_{adj_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Write the adjusted data with the new version
            success = self.influxdb.write_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                data=adjusted_data,
                source=source or "adjustment",
                version=adjustment_version,
                is_adjusted=True
            )
            
            if not success:
                logger.error(f"Failed to write adjusted data for {instrument}/{timeframe}")
                return {
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "status": "failed",
                    "reason": "Failed to write adjusted data"
                }
            
            # Record the adjustment in the audit log
            adjustment_metadata = {
                "adjustment_type": adj_type,
                "adjustment_factor": adjustment_factor,
                "reference_date": reference_date.isoformat() if isinstance(reference_date, datetime) else reference_date,
                "affected_fields": affected_fields,
                "description": description or f"{adj_type.capitalize()} adjustment factor {adjustment_factor}",
                "source": source,
                "original_version": "latest",
                "adjusted_points": len(adjusted_data),
                "pre_adjustment_snapshot": snapshot_id
            }
            
            # Record in version audit
            await self.versioning_service._record_version_audit(
                instrument=instrument,
                timeframe=timeframe,
                version=adjustment_version,
                user_id=user_id,
                action=f"create_{adj_type}_adjustment",
                metadata=adjustment_metadata,
                related_version="latest"
            )
            
            # Create an audit record for the adjustment
            adjustment_record = {
                "measurement": "data_adjustments",
                "tags": {
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "adjustment_type": adj_type,
                    "version": adjustment_version
                },
                "time": datetime.now(),
                "fields": {
                    "adjustment_factor": float(adjustment_factor),
                    "reference_date": reference_date.isoformat() if isinstance(reference_date, datetime) else reference_date,
                    "affected_fields": json.dumps(affected_fields),
                    "description": description or f"{adj_type.capitalize()} adjustment factor {adjustment_factor}",
                    "source": source or "manual",
                    "user_id": user_id,
                    "adjusted_points": len(adjusted_data),
                    "metadata": json.dumps(adjustment_metadata)
                }
            }
            
            self.influxdb.write_api.write(
                bucket=self.influxdb.audit_bucket,
                record=adjustment_record
            )
            
            # Tag the new version
            await self.versioning_service.tag_version(
                instrument=instrument,
                timeframe=timeframe,
                version=adjustment_version,
                tag_name="adjustment_type",
                tag_value=adj_type,
                user_id=user_id
            )
            
            return {
                "instrument": instrument,
                "timeframe": timeframe,
                "adjustment_type": adj_type,
                "adjustment_factor": adjustment_factor,
                "reference_date": reference_date.isoformat() if isinstance(reference_date, datetime) else reference_date,
                "affected_fields": affected_fields,
                "adjusted_points": len(adjusted_data),
                "adjustment_version": adjustment_version,
                "pre_adjustment_snapshot": snapshot_id,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error creating adjustment: {e}")
            return {
                "instrument": instrument,
                "timeframe": timeframe,
                "status": "error",
                "error": str(e)
            }
    
    async def list_adjustments(self,
                            instrument: Optional[str] = None,
                            timeframe: Optional[str] = None,
                            adjustment_type: Optional[str] = None,
                            start_date: Optional[Union[datetime, str]] = None,
                            end_date: Optional[Union[datetime, str]] = None) -> List[Dict[str, Any]]:
        """
        List all adjustments with filtering options.
        
        Args:
            instrument: Optional instrument to filter by
            timeframe: Optional timeframe to filter by
            adjustment_type: Optional adjustment type to filter by
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            List of adjustment records
        """
        try:
            # Set default date range if not provided
            if not start_date:
                start_date = datetime.now() - timedelta(days=365)  # Last year
            if not end_date:
                end_date = datetime.now()
                
            # Convert dates to ISO format if they are datetime objects
            start_date_str = start_date.isoformat() if isinstance(start_date, datetime) else start_date
            end_date_str = end_date.isoformat() if isinstance(end_date, datetime) else end_date
            
            # Build the query with filters
            query = f'''
            from(bucket: "{self.influxdb.audit_bucket}")
                |> range(start: {start_date_str}, stop: {end_date_str})
                |> filter(fn: (r) => r["_measurement"] == "data_adjustments")
            '''
            
            if instrument:
                query += f'|> filter(fn: (r) => r["instrument"] == "{instrument}")\n'
            
            if timeframe:
                query += f'|> filter(fn: (r) => r["timeframe"] == "{timeframe}")\n'
                
            if adjustment_type:
                query += f'|> filter(fn: (r) => r["adjustment_type"] == "{adjustment_type}")\n'
            
            # Complete the query
            query += '''
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"], desc: true)
            '''
            
            # Execute the query
            tables = self.influxdb.query_api.query(query, org=self.influxdb.org)
            
            # Process the results
            adjustments = []
            for table in tables:
                for record in table.records:
                    # Get all field values
                    adjustment = {
                        "timestamp": record.get_time().isoformat(),
                        "instrument": record.values.get("instrument"),
                        "timeframe": record.values.get("timeframe"),
                        "adjustment_type": record.values.get("adjustment_type"),
                        "adjustment_factor": record.values.get("adjustment_factor"),
                        "reference_date": record.values.get("reference_date"),
                        "version": record.values.get("version"),
                        "source": record.values.get("source"),
                        "user_id": record.values.get("user_id"),
                        "description": record.values.get("description")
                    }
                    
                    # Parse JSON fields if present
                    metadata_str = record.values.get("metadata")
                    if metadata_str:
                        try:
                            metadata = json.loads(metadata_str)
                            adjustment["metadata"] = metadata
                        except json.JSONDecodeError:
                            adjustment["metadata"] = {}
                    
                    affected_fields_str = record.values.get("affected_fields")
                    if affected_fields_str:
                        try:
                            affected_fields = json.loads(affected_fields_str)
                            adjustment["affected_fields"] = affected_fields
                        except json.JSONDecodeError:
                            adjustment["affected_fields"] = []
                    
                    adjustments.append(adjustment)
            
            return adjustments
            
        except Exception as e:
            logger.error(f"Error listing adjustments: {e}")
            return []
    
    async def verify_data_quality(self,
                               instrument: str,
                               timeframe: str,
                               start_date: Union[datetime, str],
                               end_date: Union[datetime, str],
                               version: str = "latest") -> Dict[str, Any]:
        """
        Perform a comprehensive data quality assessment.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            start_date: The start date
            end_date: The end date
            version: The data version to analyze
            
        Returns:
            Dict containing quality metrics and identified issues
        """
        try:
            # Get data for quality verification
            data = self.influxdb.query_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                version=version
            )
            
            if not data:
                logger.warning(f"No data found for quality assessment for {instrument}/{timeframe}")
                return {
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "quality_score": 0,
                    "status": "failed",
                    "reason": "No data available for assessment"
                }
            
            # Convert to pandas DataFrame for analysis
            df = pd.DataFrame(data)
            df = df.sort_values("timestamp")
            
            # Calculate expected data points based on timeframe
            timeframe_mins = self._get_timeframe_duration_minutes(timeframe)
            expected_points = self._calculate_expected_points(
                start_date, end_date, timeframe_mins
            )
            
            # Check completeness (what percentage of expected points are present)
            completeness = len(df) / expected_points if expected_points > 0 else 0
            
            # Check for missing data points
            missing_points = expected_points - len(df)
            
            # Check for duplicates
            duplicates = df.duplicated(subset=["timestamp"]).sum()
            
            # Check for null values
            null_values = df.isnull().sum().to_dict()
            
            # Check price integrity (high >= low, etc.)
            price_integrity_issues = []
            for idx, row in df.iterrows():
                issues = []
                if row.get("high") < row.get("low"):
                    issues.append("high < low")
                if row.get("open") < row.get("low") or row.get("open") > row.get("high"):
                    issues.append("open outside range")
                if row.get("close") < row.get("low") or row.get("close") > row.get("high"):
                    issues.append("close outside range")
                if row.get("volume") < 0:
                    issues.append("negative volume")
                
                if issues:
                    price_integrity_issues.append({
                        "timestamp": row.get("timestamp").isoformat() if isinstance(row.get("timestamp"), datetime) else row.get("timestamp"),
                        "issues": issues,
                        "values": {
                            "open": row.get("open"),
                            "high": row.get("high"),
                            "low": row.get("low"),
                            "close": row.get("close"),
                            "volume": row.get("volume")
                        }
                    })
            
            # Check for consistency issues (large jumps, etc.)
            consistency_issues = []
            if len(df) > 1:
                # Calculate period-to-period changes
                df["price_change_pct"] = df["close"].pct_change() * 100
                df["volume_change_pct"] = df["volume"].pct_change() * 100
                
                # Find outliers in changes (more than 3 standard deviations)
                price_mean = df["price_change_pct"].mean()
                price_std = df["price_change_pct"].std()
                price_outliers = df[abs(df["price_change_pct"] - price_mean) > 3 * price_std]
                
                volume_mean = df["volume_change_pct"].mean()
                volume_std = df["volume_change_pct"].std()
                volume_outliers = df[abs(df["volume_change_pct"] - volume_mean) > 3 * volume_std]
                
                # Add consistency issues
                for idx, row in price_outliers.iterrows():
                    consistency_issues.append({
                        "timestamp": row.get("timestamp").isoformat() if isinstance(row.get("timestamp"), datetime) else row.get("timestamp"),
                        "type": "price_jump",
                        "change_pct": row.get("price_change_pct"),
                        "value": row.get("close"),
                        "previous_value": df.loc[idx-1, "close"] if idx > 0 else None
                    })
                
                for idx, row in volume_outliers.iterrows():
                    consistency_issues.append({
                        "timestamp": row.get("timestamp").isoformat() if isinstance(row.get("timestamp"), datetime) else row.get("timestamp"),
                        "type": "volume_jump",
                        "change_pct": row.get("volume_change_pct"),
                        "value": row.get("volume"),
                        "previous_value": df.loc[idx-1, "volume"] if idx > 0 else None
                    })
            
            # Check for timestamp consistency
            timestamps = df["timestamp"].tolist()
            timestamp_issues = []
            
            # Convert all timestamps to datetime if they are strings
            timestamps = [
                datetime.fromisoformat(ts) if isinstance(ts, str) else ts
                for ts in timestamps
            ]
            
            if len(timestamps) > 1:
                for i in range(1, len(timestamps)):
                    # Calculate the difference in minutes
                    diff = (timestamps[i] - timestamps[i-1]).total_seconds() / 60
                    
                    # If the difference is not close to the expected timeframe
                    if abs(diff - timeframe_mins) > 0.1 * timeframe_mins:  # Allow 10% tolerance
                        timestamp_issues.append({
                            "timestamp": timestamps[i].isoformat(),
                            "previous_timestamp": timestamps[i-1].isoformat(),
                            "difference_minutes": diff,
                            "expected_minutes": timeframe_mins,
                            "deviation_pct": abs(diff - timeframe_mins) / timeframe_mins * 100
                        })
            
            # Calculate overall quality score (0-100)
            quality_factors = {
                "completeness": 0.35,
                "integrity": 0.20,
                "consistency": 0.25,
                "timestamp_accuracy": 0.20
            }
            
            completeness_score = completeness * 100
            
            integrity_score = 100 - (len(price_integrity_issues) / len(df) * 100 if len(df) > 0 else 0)
            
            consistency_score = 100 - (len(consistency_issues) / len(df) * 100 if len(df) > 0 else 0)
            
            timestamp_score = 100 - (len(timestamp_issues) / len(df) * 100 if len(df) > 0 else 0)
            
            quality_score = (
                quality_factors["completeness"] * completeness_score +
                quality_factors["integrity"] * integrity_score +
                quality_factors["consistency"] * consistency_score +
                quality_factors["timestamp_accuracy"] * timestamp_score
            )
            
            # Generate quality assessment result
            quality_result = {
                "instrument": instrument,
                "timeframe": timeframe,
                "version": version,
                "start_date": start_date if isinstance(start_date, str) else start_date.isoformat(),
                "end_date": end_date if isinstance(end_date, str) else end_date.isoformat(),
                "data_points": len(df),
                "expected_points": expected_points,
                "missing_points": missing_points,
                "completeness": completeness,
                "duplicates": int(duplicates),
                "null_values": null_values,
                "price_integrity_issues": price_integrity_issues[:100] if len(price_integrity_issues) > 100 else price_integrity_issues,
                "consistency_issues": consistency_issues[:100] if len(consistency_issues) > 100 else consistency_issues,
                "timestamp_issues": timestamp_issues[:100] if len(timestamp_issues) > 100 else timestamp_issues,
                "scores": {
                    "completeness": completeness_score,
                    "integrity": integrity_score,
                    "consistency": consistency_score,
                    "timestamp_accuracy": timestamp_score,
                    "overall": quality_score
                },
                "quality_level": self._get_quality_level(quality_score),
                "assessment_timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
            return quality_result
            
        except Exception as e:
            logger.error(f"Error verifying data quality: {e}")
            return {
                "instrument": instrument,
                "timeframe": timeframe,
                "status": "error",
                "error": str(e)
            }
    
    #
    # Helper methods for anomaly detection and analysis
    #
    
    def _detect_price_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect price anomalies using statistical methods."""
        anomalies = []
        
        # Calculate z-scores for price fields
        for field in ["open", "high", "low", "close"]:
            if field in df.columns:
                # Calculate rolling mean and std for z-score
                window = min(20, len(df) // 4) if len(df) > 20 else len(df)
                rolling_mean = df[field].rolling(window=window).mean()
                rolling_std = df[field].rolling(window=window).std()
                
                # Avoid division by zero
                rolling_std = rolling_std.replace(0, np.nan)
                
                # Calculate z-scores
                z_scores = (df[field] - rolling_mean) / rolling_std
                
                # Find outliers
                outliers = df[abs(z_scores) > self.config["z_score_threshold"]].copy()
                
                for idx, row in outliers.iterrows():
                    # Skip NaN values
                    if pd.isna(z_scores.loc[idx]):
                        continue
                    
                    # Calculate confidence based on z-score
                    z_score = abs(z_scores.loc[idx])
                    confidence = min(0.5 + z_score / 10, 0.95)
                    
                    anomalies.append({
                        "timestamp": row["timestamp"],
                        "type": DataDiscrepancyType.PRICE_OUTLIER.value,
                        "field": field,
                        "value": row[field],
                        "expected": rolling_mean.loc[idx],
                        "z_score": z_score,
                        "confidence": confidence,
                        "description": f"Abnormal {field} value detected (z-score: {z_score:.2f})"
                    })
        
        # Detect large price changes
        if len(df) > 1:
            for field in ["open", "high", "low", "close"]:
                if field in df.columns:
                    df[f"{field}_pct_change"] = df[field].pct_change() * 100
                    
                    # Find large price changes
                    spikes = df[abs(df[f"{field}_pct_change"]) > self.config["price_spike_threshold"]].copy()
                    
                    for idx, row in spikes.iterrows():
                        # Skip first row (no previous value)
                        if idx == 0 or pd.isna(row[f"{field}_pct_change"]):
                            continue
                        
                        change_pct = row[f"{field}_pct_change"]
                        # Calculate confidence based on magnitude of change
                        confidence = min(0.5 + abs(change_pct) / 100, 0.95)
                        
                        # Look for confirmation in other price fields
                        other_fields = [f for f in ["open", "high", "low", "close"] if f != field]
                        confirming_fields = 0
                        
                        for other_field in other_fields:
                            if other_field in df.columns:
                                other_change = df.loc[idx, f"{other_field}_pct_change"]
                                if not pd.isna(other_change) and abs(other_change) > self.config["price_spike_threshold"] / 2:
                                    confirming_fields += 1
                        
                        # Adjust confidence based on confirmation
                        if confirming_fields > 0:
                            confidence = min(confidence + 0.1 * confirming_fields, 0.95)
                        
                        anomalies.append({
                            "timestamp": row["timestamp"],
                            "type": DataDiscrepancyType.PRICE_OUTLIER.value,
                            "field": field,
                            "value": row[field],
                            "previous_value": df.iloc[idx-1][field],
                            "change_pct": change_pct,
                            "confidence": confidence,
                            "description": f"Large {field} change of {change_pct:.2f}% detected"
                        })
        
        return anomalies
    
    def _detect_volume_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect volume anomalies using statistical methods."""
        anomalies = []
        
        if "volume" not in df.columns or len(df) < 5:
            return anomalies
        
        # Calculate rolling average volume
        window = min(20, len(df) // 4) if len(df) > 20 else len(df)
        df["volume_avg"] = df["volume"].rolling(window=window).mean()
        
        # Find volume spikes
        df["volume_ratio"] = df["volume"] / df["volume_avg"]
        volume_spikes = df[df["volume_ratio"] > self.config["volume_spike_factor"]].copy()
        
        for idx, row in volume_spikes.iterrows():
            # Skip NaN values
            if pd.isna(row["volume_ratio"]):
                continue
            
            # Calculate confidence based on volume ratio
            ratio = row["volume_ratio"]
            confidence = min(0.5 + ratio / 20, 0.95)
            
            anomalies.append({
                "timestamp": row["timestamp"],
                "type": DataDiscrepancyType.VOLUME_OUTLIER.value,
                "value": row["volume"],
                "average_volume": row["volume_avg"],
                "volume_ratio": ratio,
                "confidence": confidence,
                "description": f"Volume spike {ratio:.2f}x above average detected"
            })
        
        # Check for zero volume periods in normally active instruments
        if df["volume"].median() > 0:
            zero_volumes = df[df["volume"] == 0].copy()
            
            for idx, row in zero_volumes.iterrows():
                # Calculate confidence based on typical volume
                typical_volume = df["volume"].median()
                confidence = min(0.5 + typical_volume / 1000, 0.9)
                
                anomalies.append({
                    "timestamp": row["timestamp"],
                    "type": DataDiscrepancyType.VOLUME_OUTLIER.value,
                    "value": 0,
                    "typical_volume": typical_volume,
                    "confidence": confidence,
                    "description": "Zero volume period detected in active instrument"
                })
        
        return anomalies
    
    def _detect_price_gaps(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect gaps between close and next open prices."""
        anomalies = []
        
        if len(df) < 2:
            return anomalies
        
        # Calculate gaps between close and next open
        df = df.sort_values("timestamp")
        df["next_open"] = df["open"].shift(-1)
        df["gap_pct"] = (df["next_open"] - df["close"]) / df["close"] * 100
        
        # Find significant gaps
        gaps = df[abs(df["gap_pct"]) > self.config["price_gap_threshold"]].copy()
        
        for idx, row in gaps.iterrows():
            # Skip last row (no next open)
            if pd.isna(row["gap_pct"]):
                continue
            
            gap_pct = row["gap_pct"]
            # Calculate confidence based on gap size
            confidence = min(0.5 + abs(gap_pct) / 20, 0.95)
            
            anomalies.append({
                "timestamp": row["timestamp"],
                "type": DataDiscrepancyType.GAP.value,
                "close_value": row["close"],
                "next_open_value": row["next_open"],
                "gap_pct": gap_pct,
                "confidence": confidence,
                "description": f"Price gap of {gap_pct:.2f}% between close and next open"
            })
        
        return anomalies
    
    def _detect_potential_corporate_actions(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect patterns suggestive of corporate actions."""
        anomalies = []
        
        # Combine results from specialized detectors
        anomalies.extend(self._detect_stock_splits(df))
        anomalies.extend(self._detect_dividends(df))
        
        return anomalies
    
    def _detect_stock_splits(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect potential stock splits based on price and volume patterns."""
        anomalies = []
        
        if len(df) < 10:
            return anomalies
        
        # Calculate large overnight price drops
        df = df.sort_values("timestamp")
        df["next_open"] = df["open"].shift(-1)
        df["price_drop_pct"] = (df["next_open"] - df["close"]) / df["close"] * 100
        
        # Calculate volume changes
        df["next_volume"] = df["volume"].shift(-1)
        df["volume_change_ratio"] = df["next_volume"] / df["volume"]
        
        # Find potential splits (large price drop with volume increase)
        potential_splits = df[
            (df["price_drop_pct"] < -self.config["split_ratio_threshold"] * 100) & 
            (df["volume_change_ratio"] > 1.5)
        ].copy()
        
        for idx, row in potential_splits.iterrows():
            # Skip last row or NaN values
            if pd.isna(row["price_drop_pct"]) or pd.isna(row["volume_change_ratio"]):
                continue
            
            # Analyze the drop to estimate split ratio
            drop_pct = abs(row["price_drop_pct"])
            
            # Common split ratios: 2:1 (50% drop), 3:1 (67% drop), 4:1 (75% drop), etc.
            split_ratios = {
                2: 50,  # 2:1 split → 50% drop
                3: 67,  # 3:1 split → 67% drop
                4: 75,  # 4:1 split → 75% drop
                5: 80,  # 5:1 split → 80% drop
                10: 90  # 10:1 split → 90% drop
            }
            
            # Find the closest split ratio
            closest_ratio = min(split_ratios.items(), key=lambda x: abs(x[1] - drop_pct))
            ratio = closest_ratio[0]
            expected_drop = closest_ratio[1]
            
            # Calculate confidence based on how close to the expected drop
            confidence = 0.7 * (1 - min(abs(drop_pct - expected_drop) / expected_drop, 1))
            
            # Boost confidence if volume increased significantly
            volume_increase = row["volume_change_ratio"]
            if volume_increase > 1.8:
                confidence += 0.1
            if volume_increase > 2.5:
                confidence += 0.1
            
            # Cap confidence
            confidence = min(confidence, 0.95)
            
            if confidence >= self.config["adjustment_confidence_threshold"][AdjustmentType.SPLIT]:
                anomalies.append({
                    "timestamp": row["timestamp"],
                    "type": AdjustmentType.SPLIT.value,
                    "close_value": row["close"],
                    "next_open_value": row["next_open"],
                    "price_drop_pct": row["price_drop_pct"],
                    "volume_change_ratio": row["volume_change_ratio"],
                    "estimated_split_ratio": f"{ratio}:1",
                    "confidence": confidence,
                    "description": f"Potential {ratio}:1 stock split detected with {drop_pct:.2f}% price drop"
                })
        
        return anomalies
    
    def _detect_dividends(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect potential dividend payments based on price patterns."""
        anomalies = []
        
        if len(df) < 10:
            return anomalies
        
        # Calculate overnight price drops without corresponding volume changes
        df = df.sort_values("timestamp")
        df["next_open"] = df["open"].shift(-1)
        df["price_drop_pct"] = (df["next_open"] - df["close"]) / df["close"] * 100
        
        # Calculate volume changes
        df["next_volume"] = df["volume"].shift(-1)
        df["volume_change_ratio"] = df["next_volume"] / df["volume"]
        
        # Find potential dividends (modest price drop without volume increase)
        potential_dividends = df[
            (df["price_drop_pct"] < -0.5) &  # More than 0.5% drop
            (df["price_drop_pct"] > -5.0) &  # Less than 5% drop
            (df["volume_change_ratio"] < 1.5)  # Without large volume increase
        ].copy()
        
        for idx, row in potential_dividends.iterrows():
            # Skip last row or NaN values
            if pd.isna(row["price_drop_pct"]) or pd.isna(row["volume_change_ratio"]):
                continue
            
            # Calculate confidence based on typical dividend characteristics
            drop_pct = abs(row["price_drop_pct"])
            
            # Typical dividend yields range from 0.5% to 4%
            confidence = 0.6
            
            # Adjust confidence based on how typical the drop is for dividends
            if 0.5 <= drop_pct <= 4.0:
                confidence += 0.2
            elif drop_pct > 4.0:
                confidence -= 0.1 * (drop_pct - 4.0)
            
            # Reduce confidence if volume changed significantly
            volume_change = abs(1 - row["volume_change_ratio"])
            if volume_change > 0.3:
                confidence -= 0.1
            
            # Cap confidence
            confidence = max(min(confidence, 0.9), 0.5)
            
            if confidence >= self.config["adjustment_confidence_threshold"][AdjustmentType.DIVIDEND]:
                anomalies.append({
                    "timestamp": row["timestamp"],
                    "type": AdjustmentType.DIVIDEND.value,
                    "close_value": row["close"],
                    "next_open_value": row["next_open"],
                    "price_drop_pct": row["price_drop_pct"],
                    "estimated_dividend": row["close"] * abs(row["price_drop_pct"]) / 100,
                    "estimated_yield": abs(row["price_drop_pct"]),
                    "confidence": confidence,
                    "description": f"Potential dividend of {abs(row['price_drop_pct']):.2f}% detected"
                })
        
        return anomalies
    
    def _detect_mergers(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect potential mergers based on price and volume patterns."""
        anomalies = []
        
        if len(df) < 20:
            return anomalies
        
        # Calculate large price jumps with volume spikes
        df = df.sort_values("timestamp")
        df["price_change_pct"] = df["close"].pct_change() * 100
        
        # Calculate volume spikes
        df["volume_ratio"] = df["volume"] / df["volume"].rolling(window=10).mean()
        
        # Find potential merger events (large price jump with extreme volume)
        potential_mergers = df[
            (abs(df["price_change_pct"]) > 15) &  # More than 15% price change
            (df["volume_ratio"] > 5)  # More than 5x normal volume
        ].copy()
        
        for idx, row in potential_mergers.iterrows():
            # Skip first row or NaN values
            if idx == 0 or pd.isna(row["price_change_pct"]) or pd.isna(row["volume_ratio"]):
                continue
            
            # Calculate confidence based on how extreme the event is
            price_change = abs(row["price_change_pct"])
            volume_spike = row["volume_ratio"]
            
            # Base confidence on price change and volume spike
            confidence = 0.5 + min(price_change / 100, 0.25) + min(volume_spike / 30, 0.2)
            
            # Cap confidence
            confidence = min(confidence, 0.9)
            
            if confidence >= self.config["adjustment_confidence_threshold"][AdjustmentType.MERGER]:
                direction = "up" if row["price_change_pct"] > 0 else "down"
                anomalies.append({
                    "timestamp": row["timestamp"],
                    "type": AdjustmentType.MERGER.value,
                    "price_change_pct": row["price_change_pct"],
                    "volume_ratio": row["volume_ratio"],
                    "confidence": confidence,
                    "description": f"Potential merger/acquisition event with {price_change:.2f}% price movement {direction} and {volume_spike:.1f}x volume spike"
                })
        
        return anomalies
    
    def _detect_timestamp_irregularities(self, df: pd.DataFrame, timeframe: str) -> List[Dict[str, Any]]:
        """Detect irregularities in timestamp sequences."""
        anomalies = []
        
        if len(df) < 2:
            return anomalies
        
        # Get expected interval in minutes
        expected_interval = self._get_timeframe_duration_minutes(timeframe)
        expected_timedelta = timedelta(minutes=expected_interval)
        
        # Sort by timestamp
        df = df.sort_values("timestamp")
        timestamps = df["timestamp"].tolist()
        
        # Check intervals between timestamps
        for i in range(1, len(timestamps)):
            current = timestamps[i]
            previous = timestamps[i-1]
            
            # Convert to datetime if needed
            if isinstance(current, str):
                current = datetime.fromisoformat(current)
            if isinstance(previous, str):
                previous = datetime.fromisoformat(previous)
                
            # Calculate actual interval
            interval = (current - previous).total_seconds() / 60  # in minutes
            
            # Check if interval is significantly different from expected
            if abs(interval - expected_interval) > 0.1 * expected_interval:  # 10% tolerance
                # Calculate confidence based on how far from expected
                deviation = abs(interval - expected_interval) / expected_interval
                confidence = 0.9 - min(deviation, 0.5)
                
                anomalies.append({
                    "timestamp": current.isoformat() if isinstance(current, datetime) else current,
                    "previous_timestamp": previous.isoformat() if isinstance(previous, datetime) else previous,
                    "type": DataDiscrepancyType.TIMESTAMP_IRREGULARITY.value,
                    "expected_interval": expected_interval,
                    "actual_interval": interval,
                    "deviation": deviation,
                    "confidence": confidence,
                    "description": f"Timestamp irregularity: {interval:.1f} minutes instead of expected {expected_interval} minutes"
                })
        
        return anomalies
    
    def _calculate_discrepancy_severity(self, diff_dict: Dict[str, Dict[str, float]]) -> float:
        """Calculate the severity score for data discrepancies."""
        if not diff_dict:
            return 0.0
        
        # Weights for different fields
        field_weights = {
            "open": 0.15,
            "high": 0.25,
            "low": 0.25,
            "close": 0.3,
            "volume": 0.05
        }
        
        # Calculate weighted average of percent differences
        total_weight = 0
        weighted_pct_diff = 0
        
        for field, values in diff_dict.items():
            if field in field_weights and "pct_diff" in values:
                weight = field_weights.get(field, 0.1)
                total_weight += weight
                weighted_pct_diff += weight * values["pct_diff"]
        
        if total_weight == 0:
            return 0.0
        
        avg_pct_diff = weighted_pct_diff / total_weight
        
        # Normalize to 0-1 scale with diminishing returns for larger differences
        severity = min(1.0, avg_pct_diff / 100)
        
        return severity
    
    def _calculate_adjustment_recommendation(self, 
                                          discrepancies: List[Dict[str, Any]],
                                          instrument: str,
                                          timeframe: str) -> Optional[Dict[str, Any]]:
        """Calculate adjustment recommendations based on observed discrepancies."""
        if not discrepancies:
            return None
        
        # Extract all percent differences for price fields
        price_diffs = []
        for discrepancy in discrepancies:
            differences = discrepancy.get("differences", {})
            for field, values in differences.items():
                if field in ["open", "high", "low", "close"] and "pct_diff" in values:
                    price_diffs.append(values["pct_diff"])
        
        if not price_diffs:
            return None
        
        # Calculate median percent difference
        median_diff = np.median(price_diffs)
        
        # Analyze the pattern of differences
        if abs(median_diff) < 0.1:
            # Very small differences, no adjustment needed
            return None
        
        # Calculate confidence based on consistency of differences
        std_diff = np.std(price_diffs)
        mean_diff = np.mean(price_diffs)
        cv = std_diff / abs(mean_diff) if abs(mean_diff) > 0 else float('inf')
        
        # More consistent differences (lower CV) = higher confidence
        confidence = 0.9 - min(cv, 0.9)
        
        # Determine adjustment type based on magnitude and pattern
        if median_diff < -30 and confidence > 0.7:
            # Large negative difference suggests a split
            ratio = round(100 / (100 + median_diff))
            return {
                "type": AdjustmentType.SPLIT.value,
                "instrument": instrument,
                "timeframe": timeframe,
                "factor": ratio,
                "median_diff_pct": median_diff,
                "confidence": confidence,
                "description": f"Recommend {ratio}:1 split adjustment based on consistent {median_diff:.2f}% price difference",
                "affected_fields": ["open", "high", "low", "close"]
            }
        elif abs(median_diff) < 15 and confidence > 0.7:
            # Modest difference suggests a dividend or minor adjustment
            factor = 1 + (median_diff / 100)
            return {
                "type": AdjustmentType.DIVIDEND.value if median_diff < 0 else AdjustmentType.CORRECTION.value,
                "instrument": instrument,
                "timeframe": timeframe,
                "factor": factor,
                "median_diff_pct": median_diff,
                "confidence": confidence,
                "description": f"Recommend {AdjustmentType.DIVIDEND.value if median_diff < 0 else AdjustmentType.CORRECTION.value} adjustment of {abs(median_diff):.2f}%",
                "affected_fields": ["open", "high", "low", "close"]
            }
        
        # Default adjustment if pattern doesn't match common types
        factor = 1 + (median_diff / 100)
        return {
            "type": AdjustmentType.UNKNOWN.value,
            "instrument": instrument,
            "timeframe": timeframe,
            "factor": factor,
            "median_diff_pct": median_diff,
            "confidence": confidence * 0.8,  # Reduce confidence for unknown type
            "description": f"Possible data adjustment needed ({median_diff:.2f}% difference)",
            "affected_fields": ["open", "high", "low", "close"]
        }
    
    async def _create_adjustment(self,
                              instrument: str,
                              timeframe: str,
                              adjustment_type: str,
                              adjustment_data: Dict[str, Any],
                              source: str) -> bool:
        """Create an adjustment based on detection results."""
        try:
            factor = adjustment_data.get("factor", 1.0)
            description = adjustment_data.get("description", "Automatically detected adjustment")
            affected_fields = adjustment_data.get("affected_fields", ["open", "high", "low", "close"])
            
            # For splits, use the ratio as the adjustment factor
            if adjustment_type == AdjustmentType.SPLIT.value:
                # Ensure factor is properly formatted for splits
                factor = float(factor)
            else:
                # For other adjustments, use the calculated factor
                factor = float(factor)
            
            # Create the adjustment
            result = await self.create_adjustment(
                instrument=instrument,
                timeframe=timeframe,
                adjustment_type=adjustment_type,
                adjustment_factor=factor,
                reference_date=datetime.now(),  # TODO: Use a more appropriate reference date
                description=description,
                affected_fields=affected_fields,
                source=f"auto_reconciliation_{source}",
                user_id="system"
            )
            
            if result.get("status") == "success":
                logger.info(f"Created automatic adjustment: {description}")
                return True
            else:
                logger.error(f"Failed to create adjustment: {result.get('reason')}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating adjustment: {e}")
            return False
    
    def _timestamp_to_str(self, ts) -> str:
        """Convert timestamp to string for consistent comparison."""
        if isinstance(ts, datetime):
            return ts.isoformat()
        return str(ts)
    
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
                                start_date: Union[datetime, str], 
                                end_date: Union[datetime, str], 
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
        # Convert string dates to datetime for calculation
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
            
        # Calculate the total minutes in the range
        delta = end_date - start_date
        total_minutes = delta.total_seconds() / 60
        
        # Calculate expected points
        expected_points = int(total_minutes / timeframe_minutes) + 1
        
        return max(expected_points, 0)  # Ensure non-negative result
    
    def _get_quality_level(self, quality_score: float) -> str:
        """Convert quality score to qualitative level."""
        if quality_score >= 95:
            return "Excellent"
        elif quality_score >= 90:
            return "Very Good"
        elif quality_score >= 80:
            return "Good"
        elif quality_score >= 70:
            return "Fair"
        elif quality_score >= 60:
            return "Moderate"
        elif quality_score >= 50:
            return "Poor"
        else:
            return "Very Poor"