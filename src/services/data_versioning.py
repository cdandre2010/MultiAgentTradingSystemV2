"""
Data versioning and audit service for market data.

This module provides a comprehensive service for versioning market data,
creating data snapshots for audit purposes, tracking data lineage, and
implementing data retention policies.
"""

import logging
import uuid
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Set

from ..database.influxdb import InfluxDBClient
from ..models.market_data import (
    OHLCV, 
    OHLCVPoint, 
    DataSnapshotMetadata,
    MarketDataRequest
)

logger = logging.getLogger(__name__)


class DataVersioningService:
    """
    Service for comprehensive data versioning and audit capabilities.
    
    This service provides methods for creating, managing, and auditing 
    data versions, implementing data snapshots, tracking data lineage,
    and enforcing data retention policies for market data.
    """
    
    def __init__(self, influxdb_client: InfluxDBClient):
        """
        Initialize the service.
        
        Args:
            influxdb_client: The InfluxDB client
        """
        self.influxdb = influxdb_client
    
    async def create_snapshot(self, 
                             instrument: str, 
                             timeframe: str, 
                             start_date: Union[datetime, str], 
                             end_date: Union[datetime, str],
                             user_id: Optional[str] = "system",
                             strategy_id: Optional[str] = None,
                             snapshot_id: Optional[str] = None,
                             purpose: str = "backtest",
                             tags: Optional[Dict[str, str]] = None,
                             description: Optional[str] = None) -> str:
        """
        Create a point-in-time snapshot of data for audit purposes.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            start_date: The start date
            end_date: The end date
            user_id: The user ID creating the snapshot
            strategy_id: Optional strategy ID for tracking
            snapshot_id: Optional snapshot ID (generated if None)
            purpose: The purpose of the snapshot (backtest, approval, compliance)
            tags: Additional tags for the snapshot
            description: Optional description of the snapshot
            
        Returns:
            str: The snapshot ID
        """
        # Generate a snapshot ID if not provided
        if snapshot_id is None:
            snapshot_id = f"snapshot_{uuid.uuid4()}"
        
        try:
            # Query the latest data
            data = self.influxdb.query_ohlcv(
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
            success = self.influxdb.write_ohlcv(
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
            
            # Record snapshot metadata with extended information
            metadata = {
                "source_versions": json.dumps({"latest": True}),
                "created_by": user_id,
                "purpose": purpose,
                "data_hash": data_hash,
                "data_points": len(data),
                "start_date": start_date.isoformat() if isinstance(start_date, datetime) else start_date,
                "end_date": end_date.isoformat() if isinstance(end_date, datetime) else end_date,
                "creation_time": datetime.now().isoformat(),
                "description": description or f"Snapshot for {purpose}",
            }
            
            # Add strategy ID if provided
            if strategy_id:
                metadata["strategy_id"] = strategy_id
            
            # Add additional tags
            if tags:
                metadata["tags"] = json.dumps(tags)
            
            # Record in the audit log
            self._record_version_audit(
                instrument=instrument,
                timeframe=timeframe,
                version=snapshot_id,
                user_id=user_id,
                action="create_snapshot",
                metadata=metadata
            )
            
            logger.info(f"Created snapshot {snapshot_id} for {instrument}/{timeframe} with {len(data)} data points")
            return snapshot_id
            
        except Exception as e:
            logger.error(f"Error creating snapshot: {e}")
            return ""
    
    async def get_snapshot_metadata(self, snapshot_id: str) -> Optional[DataSnapshotMetadata]:
        """
        Get metadata for a specific snapshot.
        
        Args:
            snapshot_id: The snapshot ID
            
        Returns:
            DataSnapshotMetadata object or None if not found
        """
        try:
            # Query the audit bucket for the snapshot metadata
            query = f'''
            from(bucket: "{self.influxdb.audit_bucket}")
                |> range(start: -1y)
                |> filter(fn: (r) => r["_measurement"] == "data_audit")
                |> filter(fn: (r) => r["snapshot_id"] == "{snapshot_id}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> limit(n: 1)
            '''
            
            tables = self.influxdb.query_api.query(query, org=self.influxdb.org)
            
            for table in tables:
                for record in table.records:
                    instrument = record.values.get("instrument")
                    timeframe = record.values.get("timeframe")
                    created_by = record.values.get("created_by", "system")
                    purpose = record.values.get("purpose", "backtest")
                    data_hash = record.values.get("data_hash", "")
                    
                    # Parse JSON fields
                    source_versions = {}
                    source_versions_str = record.values.get("source_versions")
                    if source_versions_str:
                        try:
                            source_versions = json.loads(source_versions_str)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse source_versions for snapshot {snapshot_id}")
                    
                    # Create metadata object
                    return DataSnapshotMetadata(
                        snapshot_id=snapshot_id,
                        instrument=instrument,
                        timeframe=timeframe,
                        created_at=record.get_time(),
                        created_by=created_by,
                        strategy_id=record.values.get("strategy_id"),
                        purpose=purpose,
                        source_versions=source_versions,
                        data_hash=data_hash,
                        data_points=int(record.values.get("data_points", 0)),
                        start_date=record.values.get("start_date"),
                        end_date=record.values.get("end_date")
                    )
            
            logger.warning(f"Snapshot metadata not found for {snapshot_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting snapshot metadata: {e}")
            return None
    
    async def compare_versions(self, 
                           instrument: str,
                           timeframe: str,
                           version1: str,
                           version2: str,
                           start_date: Optional[Union[datetime, str]] = None,
                           end_date: Optional[Union[datetime, str]] = None) -> Dict[str, Any]:
        """
        Compare two data versions and identify differences.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            version1: First version to compare
            version2: Second version to compare
            start_date: Optional start date to limit comparison
            end_date: Optional end date to limit comparison
            
        Returns:
            Dict containing comparison results
        """
        try:
            # Set default date range if not provided
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            # Query data for both versions
            data1 = self.influxdb.query_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                version=version1
            )
            
            data2 = self.influxdb.query_ohlcv(
                instrument=instrument,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                version=version2
            )
            
            # Convert to dictionaries with timestamp as key for easy comparison
            data1_dict = {str(point["timestamp"]): point for point in data1}
            data2_dict = {str(point["timestamp"]): point for point in data2}
            
            # Find common timestamps
            common_timestamps = set(data1_dict.keys()) & set(data2_dict.keys())
            
            # Find timestamps unique to each version
            only_in_v1 = set(data1_dict.keys()) - set(data2_dict.keys())
            only_in_v2 = set(data2_dict.keys()) - set(data1_dict.keys())
            
            # Find differences in common timestamps
            differences = []
            for ts in common_timestamps:
                point1 = data1_dict[ts]
                point2 = data2_dict[ts]
                
                # Compare all values
                diff = {}
                for field in ["open", "high", "low", "close", "volume"]:
                    if point1.get(field) != point2.get(field):
                        diff[field] = {
                            "v1": point1.get(field),
                            "v2": point2.get(field),
                            "diff": point2.get(field) - point1.get(field) if field in point1 and field in point2 else None,
                            "pct_change": (
                                (point2.get(field) - point1.get(field)) / point1.get(field) * 100
                                if field in point1 and field in point2 and point1.get(field) != 0
                                else None
                            )
                        }
                
                if diff:
                    differences.append({
                        "timestamp": ts,
                        "differences": diff
                    })
            
            # Calculate summary statistics
            summary = {
                "total_points_v1": len(data1),
                "total_points_v2": len(data2),
                "common_points": len(common_timestamps),
                "only_in_v1": len(only_in_v1),
                "only_in_v2": len(only_in_v2),
                "different_points": len(differences),
                "comparison_range": {
                    "start_date": start_date.isoformat() if isinstance(start_date, datetime) else start_date,
                    "end_date": end_date.isoformat() if isinstance(end_date, datetime) else end_date
                }
            }
            
            # Limit the size of the differences array for large datasets
            max_differences = 100
            if len(differences) > max_differences:
                logger.info(f"Limiting differences output to {max_differences} items")
                differences = differences[:max_differences]
            
            result = {
                "instrument": instrument,
                "timeframe": timeframe,
                "version1": version1,
                "version2": version2,
                "summary": summary,
                "differences": differences,
                "only_in_v1_samples": list(only_in_v1)[:10] if only_in_v1 else [],
                "only_in_v2_samples": list(only_in_v2)[:10] if only_in_v2 else []
            }
            
            logger.info(
                f"Compared versions {version1} and {version2} for {instrument}/{timeframe}: "
                f"{len(differences)} differences found"
            )
            return result
            
        except Exception as e:
            logger.error(f"Error comparing versions: {e}")
            return {
                "instrument": instrument,
                "timeframe": timeframe,
                "version1": version1,
                "version2": version2,
                "error": str(e)
            }
    
    async def list_versions(self, 
                        instrument: str, 
                        timeframe: str,
                        include_snapshots: bool = True,
                        include_latest: bool = True,
                        include_metadata: bool = False) -> List[Dict[str, Any]]:
        """
        List all available versions for an instrument/timeframe.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            include_snapshots: Whether to include snapshot versions
            include_latest: Whether to include the latest version
            include_metadata: Whether to include version metadata
            
        Returns:
            List of version information
        """
        try:
            versions = self.influxdb.get_data_versions(
                instrument=instrument,
                timeframe=timeframe
            )
            
            if not include_snapshots:
                versions = [v for v in versions if not v.startswith("snapshot_")]
            
            if not include_latest and "latest" in versions:
                versions.remove("latest")
            
            # Early return if no metadata requested
            if not include_metadata:
                return [{"version": v} for v in versions]
            
            # Query metadata for each version
            result = []
            for version in versions:
                version_info = {"version": version}
                
                # If it's a snapshot, get detailed metadata
                if version.startswith("snapshot_"):
                    metadata = await self.get_snapshot_metadata(version)
                    if metadata:
                        version_info["created_at"] = metadata.created_at
                        version_info["created_by"] = metadata.created_by
                        version_info["purpose"] = metadata.purpose
                        version_info["data_points"] = metadata.data_points
                        version_info["start_date"] = metadata.start_date
                        version_info["end_date"] = metadata.end_date
                        if metadata.strategy_id:
                            version_info["strategy_id"] = metadata.strategy_id
                
                # Query the first data point to get the start date
                if "start_date" not in version_info:
                    query = f'''
                    from(bucket: "{self.influxdb.bucket}")
                        |> range(start: -5y)
                        |> filter(fn: (r) => r["_measurement"] == "market_data")
                        |> filter(fn: (r) => r["instrument"] == "{instrument}")
                        |> filter(fn: (r) => r["timeframe"] == "{timeframe}")
                        |> filter(fn: (r) => r["version"] == "{version}")
                        |> filter(fn: (r) => r["_field"] == "close")
                        |> first()
                    '''
                    
                    tables = self.influxdb.query_api.query(query, org=self.influxdb.org)
                    for table in tables:
                        for record in table.records:
                            version_info["start_date"] = record.get_time().isoformat()
                
                # Query the last data point to get the end date
                if "end_date" not in version_info:
                    query = f'''
                    from(bucket: "{self.influxdb.bucket}")
                        |> range(start: -5y)
                        |> filter(fn: (r) => r["_measurement"] == "market_data")
                        |> filter(fn: (r) => r["instrument"] == "{instrument}")
                        |> filter(fn: (r) => r["timeframe"] == "{timeframe}")
                        |> filter(fn: (r) => r["version"] == "{version}")
                        |> filter(fn: (r) => r["_field"] == "close")
                        |> last()
                    '''
                    
                    tables = self.influxdb.query_api.query(query, org=self.influxdb.org)
                    for table in tables:
                        for record in table.records:
                            version_info["end_date"] = record.get_time().isoformat()
                
                # Count the number of data points
                if "data_points" not in version_info:
                    query = f'''
                    from(bucket: "{self.influxdb.bucket}")
                        |> range(start: -5y)
                        |> filter(fn: (r) => r["_measurement"] == "market_data")
                        |> filter(fn: (r) => r["instrument"] == "{instrument}")
                        |> filter(fn: (r) => r["timeframe"] == "{timeframe}")
                        |> filter(fn: (r) => r["version"] == "{version}")
                        |> filter(fn: (r) => r["_field"] == "close")
                        |> count()
                    '''
                    
                    tables = self.influxdb.query_api.query(query, org=self.influxdb.org)
                    for table in tables:
                        for record in table.records:
                            version_info["data_points"] = record.get_value()
                
                result.append(version_info)
            
            logger.info(f"Listed {len(result)} versions for {instrument}/{timeframe}")
            return result
            
        except Exception as e:
            logger.error(f"Error listing versions: {e}")
            return []
    
    async def apply_retention_policy(self,
                                  instrument: Optional[str] = None,
                                  timeframe: Optional[str] = None,
                                  max_snapshot_age_days: int = 90,
                                  exempt_purposes: Optional[List[str]] = None,
                                  exempt_tags: Optional[Dict[str, str]] = None,
                                  dry_run: bool = False) -> Dict[str, Any]:
        """
        Apply data retention policy to snapshots.
        
        Args:
            instrument: Optional instrument to limit scope (applies to all if None)
            timeframe: Optional timeframe to limit scope (applies to all if None)
            max_snapshot_age_days: Maximum age in days for snapshots to keep
            exempt_purposes: Purposes to exempt from deletion (e.g., "approval", "compliance")
            dry_run: If True, report what would be deleted without actually deleting
            
        Returns:
            Dict with retention policy results
        """
        if exempt_purposes is None:
            exempt_purposes = ["approval", "compliance"]
        
        try:
            retention_cutoff = datetime.now() - timedelta(days=max_snapshot_age_days)
            
            # Build the query to find snapshots
            query = f'''
            from(bucket: "{self.influxdb.audit_bucket}")
                |> range(start: -5y)
                |> filter(fn: (r) => r["_measurement"] == "data_audit")
            '''
            
            # Add instrument filter if specified
            if instrument:
                query += f'|> filter(fn: (r) => r["instrument"] == "{instrument}")\n'
            
            # Add timeframe filter if specified
            if timeframe:
                query += f'|> filter(fn: (r) => r["timeframe"] == "{timeframe}")\n'
            
            # Complete the query
            query += '''
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
            '''
            
            tables = self.influxdb.query_api.query(query, org=self.influxdb.org)
            
            # Analyze snapshots to find candidates for deletion
            candidates = []
            exempt = []
            
            for table in tables:
                for record in table.records:
                    snapshot_id = record.values.get("snapshot_id")
                    created_at = record.get_time()
                    purpose = record.values.get("purpose", "")
                    instrument_value = record.values.get("instrument", "")
                    timeframe_value = record.values.get("timeframe", "")
                    
                    # Skip snapshots newer than the cutoff
                    if created_at > retention_cutoff:
                        continue
                    
                    # Skip snapshots with exempt purposes
                    if purpose in exempt_purposes:
                        exempt.append({
                            "snapshot_id": snapshot_id,
                            "instrument": instrument_value,
                            "timeframe": timeframe_value,
                            "created_at": created_at.isoformat(),
                            "purpose": purpose,
                            "exempt_reason": f"Purpose '{purpose}' is exempt"
                        })
                        continue
                    
                    # Check exempt tags if provided
                    if exempt_tags:
                        tags_str = record.values.get("tags", "{}")
                        try:
                            tags = json.loads(tags_str)
                            is_exempt = False
                            
                            for tag_key, tag_value in exempt_tags.items():
                                if tag_key in tags and tags[tag_key] == tag_value:
                                    exempt.append({
                                        "snapshot_id": snapshot_id,
                                        "instrument": instrument_value,
                                        "timeframe": timeframe_value,
                                        "created_at": created_at.isoformat(),
                                        "purpose": purpose,
                                        "exempt_reason": f"Tag '{tag_key}={tag_value}' is exempt"
                                    })
                                    is_exempt = True
                                    break
                            
                            if is_exempt:
                                continue
                                
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse tags for snapshot {snapshot_id}")
                    
                    # Add to candidates for deletion
                    candidates.append({
                        "snapshot_id": snapshot_id,
                        "instrument": instrument_value,
                        "timeframe": timeframe_value,
                        "created_at": created_at.isoformat(),
                        "purpose": purpose,
                        "age_days": (datetime.now() - created_at).days
                    })
            
            # If this is a dry run, just return the candidates
            if dry_run:
                return {
                    "dry_run": True,
                    "retention_policy": {
                        "max_snapshot_age_days": max_snapshot_age_days,
                        "exempt_purposes": exempt_purposes,
                        "exempt_tags": exempt_tags
                    },
                    "candidates_for_deletion": candidates,
                    "exempt_snapshots": exempt,
                    "total_candidates": len(candidates),
                    "total_exempt": len(exempt)
                }
            
            # Delete the candidates
            deleted = []
            failed = []
            
            for candidate in candidates:
                snapshot_id = candidate["snapshot_id"]
                instrument_value = candidate["instrument"]
                timeframe_value = candidate["timeframe"]
                
                try:
                    # Delete market data points with this version
                    delete_query = f'''
                    from(bucket: "{self.influxdb.bucket}")
                        |> range(start: -5y)
                        |> filter(fn: (r) => r["_measurement"] == "market_data")
                        |> filter(fn: (r) => r["instrument"] == "{instrument_value}")
                        |> filter(fn: (r) => r["timeframe"] == "{timeframe_value}")
                        |> filter(fn: (r) => r["version"] == "{snapshot_id}")
                    '''
                    
                    self.influxdb.delete_api.delete(
                        start=datetime.now() - timedelta(days=5*365),
                        stop=datetime.now(),
                        predicate=f'_measurement="market_data" AND instrument="{instrument_value}" AND timeframe="{timeframe_value}" AND version="{snapshot_id}"',
                        bucket=self.influxdb.bucket,
                        org=self.influxdb.org
                    )
                    
                    # Delete audit log entry
                    self.influxdb.delete_api.delete(
                        start=datetime.now() - timedelta(days=5*365),
                        stop=datetime.now(),
                        predicate=f'_measurement="data_audit" AND snapshot_id="{snapshot_id}"',
                        bucket=self.influxdb.audit_bucket,
                        org=self.influxdb.org
                    )
                    
                    # Record the deletion in the audit log
                    self._record_version_audit(
                        instrument=instrument_value,
                        timeframe=timeframe_value,
                        version=snapshot_id,
                        user_id="system",
                        action="delete_snapshot",
                        metadata={
                            "reason": "retention_policy",
                            "age_days": candidate["age_days"],
                            "max_age_days": max_snapshot_age_days
                        }
                    )
                    
                    deleted.append(candidate)
                    logger.info(f"Deleted snapshot {snapshot_id} as part of retention policy")
                    
                except Exception as e:
                    logger.error(f"Failed to delete snapshot {snapshot_id}: {e}")
                    failed.append({
                        **candidate,
                        "error": str(e)
                    })
            
            return {
                "dry_run": False,
                "retention_policy": {
                    "max_snapshot_age_days": max_snapshot_age_days,
                    "exempt_purposes": exempt_purposes,
                    "exempt_tags": exempt_tags
                },
                "deleted_snapshots": deleted,
                "failed_deletions": failed,
                "exempt_snapshots": exempt,
                "total_deleted": len(deleted),
                "total_failed": len(failed),
                "total_exempt": len(exempt)
            }
            
        except Exception as e:
            logger.error(f"Error applying retention policy: {e}")
            return {
                "error": str(e),
                "dry_run": dry_run
            }
    
    async def tag_version(self,
                       instrument: str,
                       timeframe: str,
                       version: str,
                       tag_name: str,
                       tag_value: str,
                       user_id: str = "system") -> bool:
        """
        Add a tag to a data version for categorization.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            version: The version to tag
            tag_name: The tag name
            tag_value: The tag value
            user_id: The user ID applying the tag
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First check if this version exists
            versions = self.influxdb.get_data_versions(
                instrument=instrument,
                timeframe=timeframe
            )
            
            if version not in versions:
                logger.warning(f"Version {version} not found for {instrument}/{timeframe}")
                return False
            
            # For snapshot versions, update the metadata
            if version.startswith("snapshot_"):
                # Query the audit bucket for the snapshot metadata
                query = f'''
                from(bucket: "{self.influxdb.audit_bucket}")
                    |> range(start: -5y)
                    |> filter(fn: (r) => r["_measurement"] == "data_audit")
                    |> filter(fn: (r) => r["snapshot_id"] == "{version}")
                    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                    |> limit(n: 1)
                '''
                
                tables = self.influxdb.query_api.query(query, org=self.influxdb.org)
                
                for table in tables:
                    for record in table.records:
                        # Get existing tags or create new ones
                        tags = {}
                        tags_str = record.values.get("tags")
                        if tags_str:
                            try:
                                tags = json.loads(tags_str)
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse tags for snapshot {version}")
                        
                        # Add the new tag
                        tags[tag_name] = tag_value
                        
                        # Write back to the audit log
                        audit_point = {
                            "measurement": "data_audit",
                            "tags": {
                                "instrument": instrument,
                                "timeframe": timeframe,
                                "snapshot_id": version
                            },
                            "time": record.get_time(),
                            "fields": {
                                "tags": json.dumps(tags)
                            }
                        }
                        
                        self.influxdb.write_api.write(
                            bucket=self.influxdb.audit_bucket, 
                            record=audit_point
                        )
                        
                        # Record the tag update in the audit log
                        self._record_version_audit(
                            instrument=instrument,
                            timeframe=timeframe,
                            version=version,
                            user_id=user_id,
                            action="tag_version",
                            metadata={
                                "tag_name": tag_name,
                                "tag_value": tag_value
                            }
                        )
                        
                        logger.info(f"Tagged version {version} for {instrument}/{timeframe} with {tag_name}={tag_value}")
                        return True
                
                logger.warning(f"No metadata found for snapshot {version}")
                return False
                
            # For non-snapshot versions, create a dedicated tags record
            tag_point = {
                "measurement": "version_tags",
                "tags": {
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "version": version,
                    "tag_name": tag_name
                },
                "time": datetime.now(),
                "fields": {
                    "tag_value": tag_value,
                    "user_id": user_id
                }
            }
            
            self.influxdb.write_api.write(
                bucket=self.influxdb.audit_bucket, 
                record=tag_point
            )
            
            # Record the tag update in the audit log
            self._record_version_audit(
                instrument=instrument,
                timeframe=timeframe,
                version=version,
                user_id=user_id,
                action="tag_version",
                metadata={
                    "tag_name": tag_name,
                    "tag_value": tag_value
                }
            )
            
            logger.info(f"Tagged version {version} for {instrument}/{timeframe} with {tag_name}={tag_value}")
            return True
            
        except Exception as e:
            logger.error(f"Error tagging version: {e}")
            return False
    
    async def get_version_lineage(self,
                               instrument: str,
                               timeframe: str,
                               version: str) -> Dict[str, Any]:
        """
        Get the lineage information for a data version.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            version: The version to get lineage for
            
        Returns:
            Dict containing lineage information
        """
        try:
            # Query the audit log for version events
            query = f'''
            from(bucket: "{self.influxdb.audit_bucket}")
                |> range(start: -5y)
                |> filter(fn: (r) => r["_measurement"] == "version_audit")
                |> filter(fn: (r) => r["instrument"] == "{instrument}")
                |> filter(fn: (r) => r["timeframe"] == "{timeframe}")
                |> filter(fn: (r) => r["version"] == "{version}" OR r["related_version"] == "{version}")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"])
            '''
            
            tables = self.influxdb.query_api.query(query, org=self.influxdb.org)
            
            events = []
            for table in tables:
                for record in table.records:
                    action = record.values.get("action", "")
                    metadata_str = record.values.get("metadata", "{}")
                    user_id = record.values.get("user_id", "system")
                    
                    try:
                        metadata = json.loads(metadata_str)
                    except json.JSONDecodeError:
                        metadata = {}
                    
                    events.append({
                        "timestamp": record.get_time().isoformat(),
                        "action": action,
                        "user_id": user_id,
                        "metadata": metadata,
                        "version": record.values.get("version", ""),
                        "related_version": record.values.get("related_version", "")
                    })
            
            # Query for parent versions (if this is a derived version)
            parent_versions = []
            for event in events:
                if event["action"] == "create_derived_version" and event["version"] == version:
                    parent_version = event["related_version"]
                    if parent_version:
                        parent_versions.append(parent_version)
            
            # Query for child versions (versions derived from this one)
            child_versions = []
            for event in events:
                if event["action"] == "create_derived_version" and event["related_version"] == version:
                    child_version = event["version"]
                    if child_version:
                        child_versions.append(child_version)
            
            # Build the lineage tree
            lineage = {
                "instrument": instrument,
                "timeframe": timeframe,
                "version": version,
                "events": events,
                "parent_versions": parent_versions,
                "child_versions": child_versions
            }
            
            # If this is a snapshot, add the snapshot metadata
            if version.startswith("snapshot_"):
                metadata = await self.get_snapshot_metadata(version)
                if metadata:
                    lineage["snapshot_metadata"] = {
                        "created_at": metadata.created_at.isoformat(),
                        "created_by": metadata.created_by,
                        "purpose": metadata.purpose,
                        "strategy_id": metadata.strategy_id,
                        "data_points": metadata.data_points,
                        "start_date": metadata.start_date,
                        "end_date": metadata.end_date
                    }
            
            logger.info(f"Retrieved lineage for {version} for {instrument}/{timeframe}")
            return lineage
            
        except Exception as e:
            logger.error(f"Error getting version lineage: {e}")
            return {
                "instrument": instrument,
                "timeframe": timeframe,
                "version": version,
                "error": str(e)
            }
    
    def _record_version_audit(self,
                           instrument: str,
                           timeframe: str,
                           version: str,
                           user_id: str,
                           action: str,
                           metadata: Dict[str, Any],
                           related_version: Optional[str] = None) -> None:
        """
        Record an audit event for a version.
        
        Args:
            instrument: The instrument symbol
            timeframe: The timeframe
            version: The version
            user_id: The user ID performing the action
            action: The action performed
            metadata: Additional metadata about the action
            related_version: Optional related version (for derivation, comparison)
        """
        try:
            # Create the audit point
            audit_point = {
                "measurement": "version_audit",
                "tags": {
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "version": version,
                    "action": action
                },
                "time": datetime.now(),
                "fields": {
                    "user_id": user_id,
                    "metadata": json.dumps(metadata)
                }
            }
            
            # Add related version if provided
            if related_version:
                audit_point["tags"]["related_version"] = related_version
            
            # Write to the audit bucket
            self.influxdb.write_api.write(
                bucket=self.influxdb.audit_bucket, 
                record=audit_point
            )
            
            logger.debug(f"Recorded audit event for {version}: {action}")
            
        except Exception as e:
            logger.error(f"Error recording version audit: {e}")