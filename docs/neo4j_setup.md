# Neo4j Setup for Multi-Agent Trading System V2

This document explains the Neo4j database setup for the Multi-Agent Trading System V2.

## Configuration

The system is configured to work with both Neo4j Desktop (Windows) and Docker-based Neo4j:

1. **Port Configuration**: 
   - Both setups use port **7689** for the Bolt protocol
   - Neo4j Desktop typically uses 7687, but our project uses 7689 to avoid conflicts
   - Docker container maps internal port 7687 to external port 7689 for compatibility

2. **Credentials**:
   - Username: `neo4j`
   - Password: `SchoolsOut2025`

3. **Connection String**:
   - `bolt://localhost:7689`
   
4. **Browser Interface**:
   - URL: http://localhost:7474
   - Same credentials as above

## Development Workflow

### Option 1: Using Neo4j Desktop (Windows)

1. Install Neo4j Desktop from [Neo4j Download Page](https://neo4j.com/download/)
2. Create a new database with the password set to `SchoolsOut2025`
3. Configure the database to use port 7689 for Bolt:
   - Click on the "..." menu for your database
   - Select "Settings"
   - Find the "Bolt port" setting and change it to 7689
   - Apply changes and restart the database
4. Start the database
5. Initialize with: `python scripts/init_neo4j.py`

### Option 2: Using Docker

1. Navigate to the docker directory: `cd docker`
2. Ensure docker-compose.yml has the correct configuration:
   ```yaml
   environment:
     - NEO4J_AUTH=neo4j/SchoolsOut2025  # Must set password before first initialization
     - NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
   ports:
     - "7474:7474"  # HTTP
     - "7689:7687"  # Bolt - maps internal 7687 to external 7689
   ```
3. Start the containers: `docker-compose up -d`
4. Wait for initialization (about 30-60 seconds)
5. Initialize with: `python scripts/init_neo4j.py`

### Switching Between Options

If you switch between Neo4j Desktop and Docker:
1. Ensure the other Neo4j instance is completely shut down
2. Clear the database before initializing: `python clear_neo4j.py`
3. Initialize with the enhanced schema: `python scripts/init_neo4j.py`

### Troubleshooting Docker Setup

If authentication issues occur with Docker:
1. Remove the container and volumes completely:
   ```bash
   docker-compose down -v
   ```
2. Verify docker-compose.yml has correct NEO4J_AUTH setting
3. Restart the containers:
   ```bash
   docker-compose up -d
   ```
4. Check logs for successful initialization:
   ```bash
   docker logs mats_neo4j
   ```
5. Wait for full initialization before connecting

## Schema Initialization

The system has two schema initialization scripts:

1. **Basic Schema** (src/database/scripts/neo4j_init.cypher)
   - Simple schema with core components only
   - Use for basic testing

2. **Enhanced Schema** (src/database/scripts/neo4j_init_enhanced.cypher)
   - Comprehensive knowledge graph with all strategy components
   - Complex relationships with compatibility scores
   - Used by repository and agents

To initialize with the enhanced schema:
```bash
python scripts/init_neo4j.py
```

To clear the database before reinitializing:
```bash
python clear_neo4j.py
python scripts/init_neo4j.py
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if Neo4j is running (Docker: `docker ps | grep neo4j`)
   - Verify the port configuration matches (.env file)
   - Check if another application is using port 7689
   - For Docker, verify port mapping: `docker port mats_neo4j`

2. **Authentication Failed**
   - Verify credentials in .env file match Neo4j setup
   - For Docker, check NEO4J_AUTH in docker-compose.yml
   - Try accessing via browser (http://localhost:7474) to test credentials
   - For Docker authentication issues:
     * Remove volumes: `docker-compose down -v`
     * Recreate container: `docker-compose up -d`
     * Password must be set before first initialization

3. **Authentication Rate Limit**
   - Too many failed login attempts
   - Wait a few minutes or restart Neo4j
   - For Docker, recreate the container: `docker-compose down -v && docker-compose up -d`

4. **Test Failures**
   - Run tests with verbose logging: `pytest tests/unit/test_strategy_repository.py -v --log-cli-level=INFO`
   - Clear database and reinitialize before testing
   - Verify connection using browser interface before running tests

### Repository Testing

The StrategyRepository tests are designed to work with the enhanced schema. To run:

```bash
python clear_neo4j.py  # Optional, clears database
python scripts/init_neo4j.py  # Initialize with enhanced schema
pytest tests/unit/test_strategy_repository.py -v
```