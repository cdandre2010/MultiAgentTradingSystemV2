# Docker Configuration for Multi-Agent Trading System V2

This directory contains Docker configurations for running the databases and services required by the Multi-Agent Trading System.

## Services

### Neo4j
- **Purpose**: Graph database for storing strategy components and relationships
- **Port**: 7474 (HTTP), 7689 (Bolt - modified to match Neo4j Desktop)
- **Username**: neo4j
- **Password**: SchoolsOut2025
- **Web Interface**: http://localhost:7474
- **Note**: Port 7689 is used to maintain compatibility with Neo4j Desktop
- **Important**: Password is set through NEO4J_AUTH environment variable and must be configured before first initialization

### InfluxDB
- **Purpose**: Time series database for market data
- **Port**: 8086
- **Username**: admin
- **Password**: password (change in production!)
- **Organization**: mats_org
- **Bucket**: market_data
- **Token**: mats_token (change in production!)
- **Web Interface**: http://localhost:8086

### Redis
- **Purpose**: Caching and session management
- **Port**: 6379

## Usage

### Start All Services
```bash
cd docker
docker-compose up -d
```

### Stop All Services
```bash
cd docker
docker-compose down
```

### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs neo4j
```

### Data Persistence
All data is persisted in Docker volumes:
- `neo4j_data`, `neo4j_logs`, `neo4j_import`, `neo4j_plugins`
- `influxdb_data`, `influxdb_config`
- `redis_data`

To reset all data:
```bash
docker-compose down -v
```

## Initial Setup

After starting the services for the first time:

### Neo4j
1. Wait for Neo4j to fully initialize (30-60 seconds after `docker-compose up -d`)
2. Visit http://localhost:7474
3. Connect using the credentials above (neo4j/SchoolsOut2025)
4. Alternatively, initialize using the Python script:
   ```bash
   # From project root
   python scripts/init_neo4j.py  # Initialize with enhanced knowledge graph schema
   ```
5. To clear the database before reinitializing:
   ```bash
   python clear_neo4j.py
   ```

### InfluxDB
1. Visit http://localhost:8086
2. Log in using the credentials above
3. Verify the "market_data" bucket is created

## Security Note

The credentials in this docker-compose file are for development only. For production:
1. Change all passwords and tokens
2. Use environment variables or Docker secrets
3. Configure proper access controls