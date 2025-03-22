#!/usr/bin/env python3
"""
Script to initialize the Neo4j database with the enhanced knowledge graph.
"""

import sys
import os
import logging
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database import init_neo4j, db_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Initializing Neo4j database with enhanced knowledge graph...")
    
    # Connect to Neo4j
    db_manager.connect_neo4j()
    
    # Initialize with enhanced schema
    result = init_neo4j(enhanced=True)
    
    if result:
        logger.info("Neo4j initialization completed successfully!")
        logger.info("Enhanced knowledge graph with comprehensive strategy components is now ready.")
    else:
        logger.error("Neo4j initialization failed.")
        sys.exit(1)
    
    logger.info("""
Knowledge graph now includes:
- Strategy types with category, suitability, and timeframe metadata
- Position sizing methods with risk profiles and complexity ratings
- Risk management techniques with effectiveness and suitability ratings
- Trade management techniques with detailed properties
- Backtest methods with accuracy and complexity ratings
- Performance metrics with importance and interpretation guidance
- Data source types with reliability and cost information
- Comprehensive indicator metadata including calculation speeds
- Enhanced parameters with type information and validation ranges
- Rich relationships between components with compatibility scores
- Strategy templates for common trading approaches
    """)
    
    logger.info("You can now use the StrategyRepository to access the knowledge graph.")