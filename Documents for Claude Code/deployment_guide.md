# Trading Strategy System: Deployment Guide

This document provides instructions for setting up development, staging, and production environments for the Trading Strategy System.

## Table of Contents
1. [Local Development Environment](#local-development-environment)
2. [Staging Environment](#staging-environment)
3. [Production Environment](#production-environment)
4. [Database Setup](#database-setup)
5. [Monitoring and Logging](#monitoring-and-logging)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Backup and Recovery](#backup-and-recovery)

## Local Development Environment

### Prerequisites

- Python 3.9+
- Node.js 16+
- Docker and Docker Compose
- Git

### Setup Steps

1. **Clone the Repository**

```bash
git clone https://github.com/example/trading-strategy-system.git
cd trading-strategy-system
```

2. **Set Up Python Environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
```

3. **Set Up Frontend**

```bash
cd frontend
npm install
cd ..
```

4. **Configure Environment Variables**

Create a `.env` file in the root directory:

```
# Database URLs
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your_token
INFLUXDB_ORG=your_org
INFLUXDB_BUCKET=market_data
REDIS_URL=redis://localhost:6379/0

# Authentication
JWT_SECRET=your_jwt_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# LLM
ANTHROPIC_API_KEY=your_api_key
```

5. **Start Docker Containers**

```bash
docker-compose -f docker-compose.dev.yml up -d
```

This will start:
- Neo4j on port 7687 (Bolt) and 7474 (HTTP)
- InfluxDB on port 8086
- Redis on port 6379

6. **Initialize Neo4j Database**

```bash
python scripts/init_neo4j.py
```

7. **Start Backend Server**

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

8. **Start Frontend Development Server**

```bash
cd frontend
npm start
```

The frontend will be available at http://localhost:3000.

### Docker Compose Configuration

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  neo4j:
    image: neo4j:5.7
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_PLUGINS=["apoc"]
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs

  influxdb:
    image: influxdb:2.6
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=password
      - DOCKER_INFLUXDB_INIT_ORG=your_org
      - DOCKER_INFLUXDB_INIT_BUCKET=market_data
      - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=your_token
    ports:
      - "8086:8086"
    volumes:
      - influxdb_data:/var/lib/influxdb2

  redis:
    image: redis:7.0
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  neo4j_data:
  neo4j_logs:
  influxdb_data:
  redis_data:
```

### Running Tests

```bash
# Run backend tests
cd backend
pytest

# Run frontend tests
cd frontend
npm test
```

## Staging Environment

The staging environment mirrors the production setup but uses separate databases and configurations for testing.

### Infrastructure Setup

1. **Set Up AWS Resources**

```bash
cd terraform
terraform init
terraform workspace new staging
terraform apply -var-file=staging.tfvars
```

2. **Configure Environment Variables**

Update environment variables in AWS Parameter Store or set up `.env.staging` file for Docker Compose.

3. **Deploy Services**

```bash
./scripts/deploy_staging.sh
```

### Staging Configuration

```yaml
# docker-compose.staging.yml
version: '3.8'

services:
  backend:
    image: ${ECR_REPOSITORY_URL}/trading-strategy-backend:${IMAGE_TAG}
    environment:
      - ENV=staging
      - NEO4J_URI=${NEO4J_URI}
      - NEO4J_USER=${NEO4J_USER}
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
      - INFLUXDB_URL=${INFLUXDB_URL}
      - INFLUXDB_TOKEN=${INFLUXDB_TOKEN}
      - INFLUXDB_ORG=${INFLUXDB_ORG}
      - INFLUXDB_BUCKET=${INFLUXDB_BUCKET}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET=${JWT_SECRET}
      - JWT_ALGORITHM=${JWT_ALGORITHM}
      - ACCESS_TOKEN_EXPIRE_MINUTES=${ACCESS_TOKEN_EXPIRE_MINUTES}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    ports:
      - "8000:8000"
    restart: always

  frontend:
    image: ${ECR_REPOSITORY_URL}/trading-strategy-frontend:${IMAGE_TAG}
    ports:
      - "80:80"
    restart: always
```

## Production Environment

The production environment uses AWS services for high availability, scalability, and security.

### AWS Architecture

- **ECS Fargate**: Container orchestration
- **RDS**: PostgreSQL database for user data
- **EC2**: Hosts for Neo4j and InfluxDB
- **ElastiCache**: Redis for caching
- **ALB**: Load balancing and SSL termination
- **S3**: Static file storage
- **CloudFront**: CDN for frontend
- **CloudWatch**: Monitoring and logging
- **IAM**: Access management

### Deployment Steps

1. **Set Up AWS Infrastructure**

```bash
cd terraform
terraform init
terraform workspace select production
terraform apply -var-file=production.tfvars
```

2. **Build and Push Docker Images**

```bash
./scripts/build_and_push.sh
```

3. **Deploy Services**

```bash
./scripts/deploy_production.sh
```

4. **Verify Deployment**

```bash
./scripts/verify_deployment.sh
```

### Scaling Configuration

Update the following parameters in AWS console or via Terraform:

- Backend: Adjust the desired task count in ECS service
- Database: Modify instance size or enable read replicas
- ElastiCache: Change instance size or add nodes

## Database Setup

### Neo4j Setup

1. **Neo4j Schema Initialization**

```bash
python scripts/init_neo4j.py --env production
```

2. **Create Constraints and Indexes**

```cypher
CREATE CONSTRAINT strategy_type_name IF NOT EXISTS FOR (s:StrategyType) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT instrument_symbol IF NOT EXISTS FOR (i:Instrument) REQUIRE i.symbol IS UNIQUE;
CREATE CONSTRAINT indicator_name IF NOT EXISTS FOR (i:Indicator) REQUIRE i.name IS UNIQUE;
CREATE CONSTRAINT strategy_id IF NOT EXISTS FOR (s:Strategy) REQUIRE s.id IS UNIQUE;

CREATE INDEX strategy_user_idx IF NOT EXISTS FOR (s:Strategy) ON (s.user_id);
CREATE INDEX condition_type_idx IF NOT EXISTS FOR (c:Condition) ON (c.type);
```

3. **Load Initial Data**

```bash
python scripts/load_neo4j_data.py --env production
```

### InfluxDB Setup

1. **Create Organization and Bucket**

```bash
influx setup \
  --username admin \
  --password password \
  --org your_org \
  --bucket market_data \
  --retention 30d
```

2. **Create API Token**

```bash
influx auth create \
  --org your_org \
  --description "Trading Strategy System Token" \
  --all-access
```

3. **Set Up Retention Policies**

```bash
influx bucket create \
  --name market_data_1m \
  --org your_org \
  --retention 30d

influx bucket create \
  --name market_data_1h \
  --org your_org \
  --retention 365d

influx bucket create \
  --name market_data_1d \
  --org your_org \
  --retention 0
```

### PostgreSQL Setup

1. **Create Database Schema**

```bash
psql -h <db_host> -U <username> -d <database> -f scripts/create_schema.sql
```

2. **Create Database User and Permissions**

```sql
CREATE USER trading_app WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE trading_strategy TO trading_app;
GRANT USAGE ON SCHEMA public TO trading_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO trading_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO trading_app;
```

## Monitoring and Logging

### CloudWatch Setup

1. **Create Log Groups**

```bash
aws logs create-log-group --log-group-name /ecs/trading-strategy-backend
aws logs create-log-group --log-group-name /ecs/trading-strategy-frontend
```

2. **Configure Metric Alarms**

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name trading-strategy-cpu-high \
  --alarm-description "CPU usage high" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 60 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions "Name=ServiceName,Value=trading-strategy-backend" "Name=ClusterName,Value=trading-strategy-cluster" \
  --evaluation-periods 5 \
  --alarm-actions <sns_topic_arn>
```

### Prometheus and Grafana (Optional)

1. **Install Prometheus**

```bash
cd monitoring
helm install prometheus prometheus-community/prometheus \
  -f prometheus-values.yml \
  --namespace monitoring
```

2. **Install Grafana**

```bash
helm install grafana grafana/grafana \
  -f grafana-values.yml \
  --namespace monitoring
```

3. **Import Dashboards**

Import the following dashboard definitions:
- `dashboards/neo4j-dashboard.json`
- `dashboards/influxdb-dashboard.json`
- `dashboards/backend-dashboard.json`

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs