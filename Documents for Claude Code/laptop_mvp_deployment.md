# Trading Strategy System: Laptop MVP Deployment Guide

This guide provides simplified instructions for deploying the Trading Strategy System MVP on your laptop.

## Prerequisites

- Python 3.9+
- Node.js 16+
- Docker Desktop
- Git

## Setup Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/trading-strategy-system.git
cd trading-strategy-system
```

### 2. Set Up Python Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Set Up Frontend Environment

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Return to root directory
cd ..
```

### 4. Start Docker Containers for Databases

Create a `docker-compose.yml` file in the project root:

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5.7
    environment:
      - NEO4J_AUTH=neo4j/password
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    volumes:
      - neo4j_data:/data

  influxdb:
    image: influxdb:2.6
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=password
      - DOCKER_INFLUXDB_INIT_ORG=myorg
      - DOCKER_INFLUXDB_INIT_BUCKET=market_data
      - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=mytoken
    ports:
      - "8086:8086"
    volumes:
      - influxdb_data:/var/lib/influxdb2

volumes:
  neo4j_data:
  influxdb_data:
```

Start the containers:

```bash
docker compose up -d
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```
# Database connections
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=mytoken
INFLUXDB_ORG=myorg
INFLUXDB_BUCKET=market_data

# Authentication
JWT_SECRET=your_development_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API settings
API_HOST=localhost
API_PORT=8000

# LLM settings
ANTHROPIC_API_KEY=your_api_key
```

### 6. Initialize Neo4j Schema

Create a script to initialize the Neo4j database schema at `scripts/init_neo4j.py`:

```python
from neo4j import GraphDatabase

# Connect to Neo4j
uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))

# Create schema
with driver.session() as session:
    # Create constraints
    session.run("""
        CREATE CONSTRAINT strategy_type_name IF NOT EXISTS 
        FOR (s:StrategyType) REQUIRE s.name IS UNIQUE
    """)
    
    session.run("""
        CREATE CONSTRAINT instrument_symbol IF NOT EXISTS
        FOR (i:Instrument) REQUIRE i.symbol IS UNIQUE
    """)
    
    session.run("""
        CREATE CONSTRAINT indicator_name IF NOT EXISTS
        FOR (i:Indicator) REQUIRE i.name IS UNIQUE
    """)
    
    # Add sample data
    # Strategy Types
    session.run("""
        MERGE (s:StrategyType {name: 'momentum'})
        SET s.description = 'Trading strategy based on price momentum'
    """)
    
    session.run("""
        MERGE (s:StrategyType {name: 'mean_reversion'})
        SET s.description = 'Trading strategy that assumes prices will revert to their mean'
    """)
    
    # Instruments
    session.run("""
        MERGE (i:Instrument {symbol: 'BTCUSDT'})
        SET i.type = 'crypto',
            i.data_source = 'Binance API'
    """)
    
    # Frequencies
    session.run("""
        MERGE (f:Frequency {name: '1h'})
        SET f.description = '1 hour interval'
    """)
    
    # Indicators
    session.run("""
        MERGE (i:Indicator {name: 'RSI'})
        SET i.description = 'Relative Strength Index'
    """)
    
    # Parameters
    session.run("""
        MERGE (p:Parameter {name: 'period'})
        SET p.default_value = 14,
            p.min_value = 5,
            p.max_value = 50
    """)
    
    # Relationships
    session.run("""
        MATCH (s:StrategyType {name: 'momentum'})
        MATCH (i:Indicator {name: 'RSI'})
        MERGE (s)-[:COMMONLY_USES]->(i)
    """)
    
    session.run("""
        MATCH (i:Indicator {name: 'RSI'})
        MATCH (p:Parameter {name: 'period'})
        MERGE (i)-[:HAS_PARAMETER]->(p)
    """)

# Close the driver
driver.close()

print("Neo4j schema initialized successfully!")
```

Run the initialization script:

```bash
python scripts/init_neo4j.py
```

### 7. Start the Backend Server

```bash
# Navigate to backend directory
cd backend

# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be accessible at http://localhost:8000

### 8. Start the Frontend Development Server

Open a new terminal window, navigate to the project, and activate the environment:

```bash
cd path/to/trading-strategy-system
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Start the frontend:

```bash
# Navigate to frontend directory
cd frontend

# Start the development server
npm start
```

The frontend will be accessible at http://localhost:3000

## Verifying the Setup

### 1. Check Database Connections

- Neo4j: Visit http://localhost:7474 in your browser
  - Log in with username `neo4j` and password `password`
  - Run `MATCH (n) RETURN n LIMIT 25` to verify data is loaded

- InfluxDB: Visit http://localhost:8086 in your browser
  - Log in with username `admin` and password `password`

### 2. Check API Endpoints

- Swagger Documentation: Visit http://localhost:8000/docs
- Health Check: Visit http://localhost:8000/api/health

### 3. Test the Application

- Register a user: Use the frontend or API endpoint
- Create a simple strategy
- Run a backtest

## Troubleshooting

### Database Connection Issues

If you can't connect to Neo4j or InfluxDB:

```bash
# Check if containers are running
docker ps

# View container logs
docker logs trading-strategy-system-neo4j-1
docker logs trading-strategy-system-influxdb-1

# Restart containers if needed
docker compose restart
```

### Backend Startup Issues

If the backend server won't start:

- Check Python environment is activated
- Verify all dependencies are installed
- Ensure `.env` file is in the correct location
- Check database connections

### Frontend Startup Issues

If the frontend won't start:

- Ensure Node.js is properly installed
- Verify all npm dependencies are installed
- Check for JavaScript errors in the console

## Next Steps

After the MVP is running locally:

1. Add sample data for testing
2. Implement user authentication
3. Build the core strategy creation conversational flow
4. Add basic backtesting functionality

This simplified setup provides all the components needed for MVP development on your laptop.