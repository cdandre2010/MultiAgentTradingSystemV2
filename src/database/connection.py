from typing import Dict, Any, Optional
import sqlite3
from neo4j import GraphDatabase
from influxdb_client import InfluxDBClient
import redis
from ..app.config import settings


class DatabaseManager:
    """
    Manages connections to various databases used in the system.
    Provides connection pools and helper methods for database operations.
    """
    
    def __init__(self):
        """Initialize database connections."""
        self.sqlite_conn = None
        self.neo4j_driver = None
        self.influxdb_client = None
        self.redis_client = None
    
    def connect_sqlite(self, database_path: Optional[str] = None) -> None:
        """
        Connect to SQLite database.
        
        Args:
            database_path: Path to SQLite database file, falls back to config if not provided
        """
        path = database_path or settings.DATABASE_URI or "trading_system.db"
        self.sqlite_conn = sqlite3.connect(path)
        self.sqlite_conn.row_factory = sqlite3.Row
    
    def connect_neo4j(
        self, 
        uri: Optional[str] = None, 
        username: Optional[str] = None, 
        password: Optional[str] = None
    ) -> None:
        """
        Connect to Neo4j database.
        
        Args:
            uri: Neo4j URI, falls back to config if not provided
            username: Neo4j username, falls back to config if not provided
            password: Neo4j password, falls back to config if not provided
        """
        uri = uri or settings.NEO4J_URI
        username = username or settings.NEO4J_USERNAME
        password = password or settings.NEO4J_PASSWORD
        
        if uri and username and password:
            self.neo4j_driver = GraphDatabase.driver(uri, auth=(username, password))
    
    def connect_influxdb(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        org: Optional[str] = None,
        bucket: Optional[str] = None
    ) -> None:
        """
        Connect to InfluxDB.
        
        Args:
            url: InfluxDB URL, falls back to config if not provided
            token: InfluxDB token, falls back to config if not provided
            org: InfluxDB organization, falls back to config if not provided
            bucket: InfluxDB bucket, falls back to config if not provided
        """
        url = url or settings.INFLUXDB_URL
        token = token or settings.INFLUXDB_TOKEN
        org = org or settings.INFLUXDB_ORG
        
        if url and token:
            self.influxdb_client = InfluxDBClient(url=url, token=token, org=org)
            self.influxdb_bucket = bucket or settings.INFLUXDB_BUCKET
    
    def connect_redis(self, url: Optional[str] = None) -> None:
        """
        Connect to Redis.
        
        Args:
            url: Redis URL, falls back to config if not provided
        """
        url = url or settings.REDIS_URL
        
        if url:
            self.redis_client = redis.from_url(url)
    
    def connect_all(self) -> Dict[str, bool]:
        """
        Connect to all databases.
        
        Returns:
            Dict with connection status for each database
        """
        status = {
            "sqlite": False,
            "neo4j": False,
            "influxdb": False,
            "redis": False
        }
        
        try:
            self.connect_sqlite()
            status["sqlite"] = True
        except Exception as e:
            print(f"SQLite connection error: {e}")
        
        try:
            self.connect_neo4j()
            status["neo4j"] = self.neo4j_driver is not None
        except Exception as e:
            print(f"Neo4j connection error: {e}")
        
        try:
            self.connect_influxdb()
            status["influxdb"] = self.influxdb_client is not None
        except Exception as e:
            print(f"InfluxDB connection error: {e}")
        
        try:
            self.connect_redis()
            status["redis"] = self.redis_client is not None
        except Exception as e:
            print(f"Redis connection error: {e}")
        
        return status
    
    def close_all(self) -> None:
        """Close all database connections."""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        
        if self.neo4j_driver:
            self.neo4j_driver.close()
        
        if self.influxdb_client:
            self.influxdb_client.close()
        
        # Redis connections are automatically managed by the connection pool


# Singleton instance for database connections
db_manager = DatabaseManager()