#!/usr/bin/env python3
"""
Database initialization script for the Multi-Agent Trading System.

This script initializes all databases used by the system:
- SQLite for user data
- Neo4j for strategy components
- InfluxDB for time-series data

Usage:
    python scripts/init_db.py [--force]

Options:
    --force    Force reinitialization of databases, potentially overwriting existing data
"""

import sys
import os
import logging
import argparse

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.init import init_all_databases

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Initialize all databases."""
    parser = argparse.ArgumentParser(description="Initialize databases for the Multi-Agent Trading System")
    parser.add_argument('--force', action='store_true', help='Force reinitialization of databases')
    args = parser.parse_args()
    
    if args.force:
        logger.warning("Forcing database reinitialization. This may overwrite existing data.")
    
    logger.info("Initializing databases...")
    results = init_all_databases()
    
    all_success = all(results.values())
    
    if all_success:
        logger.info("All databases initialized successfully")
    else:
        failures = [db for db, success in results.items() if not success]
        logger.error(f"Failed to initialize the following databases: {', '.join(failures)}")
        sys.exit(1)


if __name__ == "__main__":
    main()