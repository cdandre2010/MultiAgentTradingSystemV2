# Docker Setup for Multi-Agent Trading System V2

This document provides instructions for using Docker with the Multi-Agent Trading System.

## Services

The system uses the following containerized services:

- **Neo4j** (Graph Database)
  - Used for: Knowledge graph, strategy components, and relationships
  - Ports: 7474 (HTTP), 7689 (Bolt)
  - Credentials: neo4j/SchoolsOut2025

- **InfluxDB** (Time Series Database)
  - Used for: Market data storage and time series analysis
  - Port: 8086
  - Credentials: admin/password
  - Organization: mats_org
  - Bucket: market_data
  - Token: mats_token

- **Redis** (Caching)
  - Used for: Caching indicator calculations and query results
  - Port: 6379

## Getting Started

### Prerequisites

- Docker and Docker Compose installed on your system
- Sufficient disk space for database storage

### Commands

#### Start all services

```bash
cd docker
docker-compose up -d
```

#### Check status of containers

```bash
docker-compose ps
```

#### View logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs neo4j
docker-compose logs influxdb
docker-compose logs redis
```

#### Stop all services

```bash
docker-compose down
```

#### Reset everything (including volumes)

```bash
docker-compose down -v
```

### Accessing Services

- **Neo4j Browser**: http://localhost:7474 (login with neo4j/SchoolsOut2025)
- **InfluxDB UI**: http://localhost:8086 (login with admin/password)

## Troubleshooting

### Neo4j Issues

- If Neo4j fails to start, check if port 7474 or 7689 is already in use
- Verify that Neo4j has sufficient memory allocated in the docker-compose.yml

### InfluxDB Issues

- On first startup, InfluxDB may take some time to initialize
- If setup fails, try resetting with `docker-compose down -v` and starting again

### Connection Issues

- Ensure Docker network settings allow connections from your application
- For Windows/WSL users, confirm that Docker Desktop integration is enabled

## Database Initialization

After starting the containers, initialize the databases:

```bash
python scripts/init_db.py
```

This will set up the required schemas and initial data in Neo4j and InfluxDB.