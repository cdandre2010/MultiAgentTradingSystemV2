"""
Database initialization module for the Multi-Agent Trading System.

This module provides functions to initialize the various databases used in the system:
- SQLite: User data, backtest results, and metadata
- Neo4j: Graph database for strategy components and relationships
- InfluxDB: Time-series database for market data
"""

import os
import sqlite3
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from .connection import db_manager

# Set up logging
logger = logging.getLogger(__name__)


def init_sqlite(db_path: Optional[str] = None) -> bool:
    """
    Initialize the SQLite database with the required schema.
    
    Args:
        db_path: Path to the SQLite database file, falls back to config if not provided
    
    Returns:
        True if initialization successful, False otherwise
    """
    try:
        # Ensure connection path is set
        if db_manager.sqlite_path is None:
            db_manager.connect_sqlite(db_path)
        
        # Get thread-local connection
        conn = db_manager.get_sqlite_connection()
        
        # Get the script path
        script_path = Path(__file__).parent / "scripts" / "sqlite_init.sql"
        
        # Read SQL script
        with open(script_path, "r") as f:
            sql_script = f.read()
        
        # Execute script
        conn.executescript(sql_script)
        conn.commit()
        
        logger.info("SQLite database initialized successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error initializing SQLite database: {e}")
        return False


def init_neo4j(enhanced: bool = True) -> bool:
    """
    Initialize the Neo4j database with the required schema and seed data.
    
    Args:
        enhanced: Whether to use the enhanced schema with comprehensive strategy components
                 Default is True for the comprehensive knowledge graph schema
    
    Returns:
        True if initialization successful, False otherwise
    """
    try:
        # Ensure connection is established
        if db_manager.neo4j_driver is None:
            db_manager.connect_neo4j()
        
        # Get the script path
        if enhanced:
            script_path = Path(__file__).parent / "scripts" / "neo4j_init_enhanced.cypher"
            logger.info("Using enhanced Neo4j schema with comprehensive knowledge graph")
        else:
            script_path = Path(__file__).parent / "scripts" / "neo4j_init.cypher"
            logger.info("Using basic Neo4j schema")
        
        # Read Cypher script
        with open(script_path, "r") as f:
            cypher_script = f.read()
        
        # Split script into individual statements (naive approach, assumes each statement ends with semicolon)
        statements = [stmt.strip() for stmt in cypher_script.split(";") if stmt.strip()]
        
        # Execute statements
        with db_manager.neo4j_driver.session() as session:
            for statement in statements:
                session.run(statement)
        
        logger.info("Neo4j database initialized successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error initializing Neo4j database: {e}")
        return False


def init_influxdb() -> bool:
    """
    Initialize the InfluxDB database with buckets.
    
    Returns:
        True if initialization successful, False otherwise
    """
    try:
        # Ensure connection is established
        if db_manager.influxdb_client is None:
            db_manager.connect_influxdb()
            
        if db_manager.influxdb_client is None:
            logger.error("Failed to connect to InfluxDB")
            return False
        
        # Check if the client is healthy
        if not db_manager.influxdb_client.health_check():
            logger.error("InfluxDB health check failed")
            return False
            
        # Create audit bucket if it doesn't exist yet
        audit_bucket = "data_audit"
        
        # We don't need to check bucket existence since our custom client handles
        # writing to buckets directly through the client's bucket parameter
        
        logger.info("InfluxDB initialization completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error initializing InfluxDB database: {e}")
        return False


def init_all_databases() -> Dict[str, bool]:
    """
    Initialize all databases used by the system.
    
    Returns:
        Dictionary with initialization status for each database
    """
    results = {
        "sqlite": False,
        "neo4j": False,
        "influxdb": False
    }
    
    # Connect to all databases
    db_status = db_manager.connect_all()
    
    # Initialize each database if connected
    if db_status["sqlite"]:
        results["sqlite"] = init_sqlite()
    
    if db_status["neo4j"]:
        results["neo4j"] = init_neo4j()
    
    if db_status["influxdb"]:
        results["influxdb"] = init_influxdb()
    
    return results


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize databases
    results = init_all_databases()
    
    # Print results
    for db, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        print(f"{db.upper()} initialization: {status}")