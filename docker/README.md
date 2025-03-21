# Docker Configuration for Multi-Agent Trading System V2

This directory contains Docker configurations for running the databases and services required by the Multi-Agent Trading System.

## Services

### Neo4j
- **Purpose**: Graph database for storing strategy components and relationships
- **Port**: 7474 (HTTP), 7687 (Bolt)
- **Username**: neo4j
- **Password**: password (change in production!)
- **Web Interface**: http://localhost:7474

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
1. Visit http://localhost:7474
2. Connect using the credentials above
3. Run the initialization scripts in `/src/database/scripts/neo4j_init.cypher`

### InfluxDB
1. Visit http://localhost:8086
2. Log in using the credentials above
3. Verify the "market_data" bucket is created

## Security Note

The credentials in this docker-compose file are for development only. For production:
1. Change all passwords and tokens
2. Use environment variables or Docker secrets
3. Configure proper access controls