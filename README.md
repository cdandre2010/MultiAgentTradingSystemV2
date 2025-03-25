# Multi-Agent Trading System V2

A conversational multi-agent AI trading system platform that allows users to define personalized trading strategies through a natural language interface, perform backtesting, and generate trading signals.

## Overview

This system uses a hybrid architecture with multiple specialized AI agents to guide users through the process of creating, testing, and monitoring trading strategies. It improves upon version 1 with enhanced calculation accuracy, better code generation, more interactive conversations, and a client-server architecture.

## Key Features

- **Conversational Interface**: Create trading strategies using natural language
- **Multi-Agent Architecture**: Specialized agents for different aspects of the system
- **Strategy Backtesting**: Test strategies against historical data
- **Real-time Monitoring**: Generate signals based on live market data
- **Neo4j Graph Database**: Store strategy components and relationships
- **InfluxDB Time Series Database**: Store market data for analysis

## System Architecture

### Agent Layer
- **Master Agent**: Orchestrates workflow and coordinates other agents ✅
- **Conversational Agent**: Handles natural language dialogue with users ✅
- **Validation Agent**: Ensures strategies are valid and complete ✅
- **Data/Feature Agent**: Retrieves and processes market data ✅
- **Code Agent**: Generates executable strategy code 🔜
- **Feedback Agent**: Analyzes results and suggests improvements 🔜

### Technology Stack
- **Frontend**: React (JavaScript)
- **Backend**: FastAPI (Python)
- **Agentic Layer**: LangChain with Claude 3.7 Sonnet
- **Data Layer**: Neo4j, InfluxDB, SQLite/PostgreSQL

## Current Status

The project is currently in **v0.5.0** with the following components implemented:
- ✅ Development environment and project structure
- ✅ User authentication system with JWT tokens
- ✅ Database connection framework (SQLite, Neo4j)
- ✅ Master agent for orchestration
- ✅ Conversational agent for natural language interaction
- ✅ Validation agent with parameter checking and LLM-powered consistency verification
- ✅ Comprehensive strategy model with all trading components
- ✅ Intelligent data configuration and caching system
- ✅ InfluxDB integration with external data sources
- ✅ Neo4j knowledge graph enhancement
- ✅ Strategy repository implementation
- ✅ Knowledge-driven agent integration
- ✅ Data/Feature agent implementation
- ✅ ConversationalAgent integration with Data/Feature agent
- 🔜 Frontend visualization components
- 🔜 Code generation agent

## Current Focus: Integration and Frontend Development

Having completed the comprehensive strategy model, data management services, and Data/Feature Agent implementation, we're now focused on:

1. **Enhanced Strategy Model** ✅
   - Expanded the strategy model with all trading components
   - Added position sizing options (fixed, percentage, risk-based, volatility, Kelly)
   - Implemented advanced backtesting configuration (walk-forward, optimization, Monte Carlo)
   - Created trade management model with partial exits and pyramiding
   - Added comprehensive performance metrics and validation
   - Implemented robust model validation with data integrity checks

2. **Intelligent Data Configuration** ✅
   - Created data source configuration with priority-based selection
   - Implemented InfluxDB-first approach with external fallbacks
   - Added data quality and preprocessing specifications
   - Designed conversation flows for data requirements dialog
   - Implemented validation for data configuration completeness
   - Added lookback period calculation based on indicators

3. **InfluxDB Integration with Data Versioning** ✅
   - Designed data schema with versioning and audit capabilities
   - Created robust data integrity and adjustment detection
   - Built on-demand indicator calculation service
   - Implemented data snapshot mechanism for strategy auditing
   - Added intelligent caching with version awareness
   - Developed external data source connectors (Binance, YFinance, Alpha Vantage)

4. **Neo4j Knowledge Graph Integration** ✅
   - Enhanced Neo4j schema with complete trading strategy components
   - Built comprehensive StrategyRepository for sophisticated graph queries
   - Added metadata about component compatibility and recommendations
   - Created relationships between components with compatibility scores
   - Implemented strategy template generation based on knowledge graph
   
5. **Agent Integration with Knowledge Graph** ✅
   - Updated ConversationalAgent to use Neo4j for strategy recommendations
   - Enhanced ValidationAgent with knowledge-driven validation
   - Created knowledge integration module for consistent access
   - Implemented intelligent strategy parameter enhancement
   - Added knowledge-driven conversation capabilities
   - Created visualization tools for knowledge graph exploration

6. **Data/Feature Agent Implementation** ✅
   - Created specialized agent for market data processing
   - Implemented comprehensive message handling for:
     - Technical indicator calculations
     - Market data retrieval
     - Data availability verification
     - Strategy data preparation
     - Visualization data formatting
   - Added integration with MasterAgent for message routing
   - Implemented proper async/sync handling for service methods
   - Created extensive test suite following TDD approach

## Getting Started

### Prerequisites
- Python 3.9+
- Docker and Docker Compose (for database services)
- Anthropic API key (for Claude 3.7 Sonnet integration)

### Installation

1. Clone the repository
   ```
   git clone https://github.com/yourusername/MultiAgentTradingSystemV2.git
   cd MultiAgentTradingSystemV2
   ```

2. Create and activate a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install backend dependencies
   ```
   python -m pip install -e .
   # or
   pip install -r requirements.txt
   ```

4. Start the database services
   ```
   cd docker
   docker-compose up -d
   ```

5. Initialize the databases
   ```
   python -m src.database.init
   ```

### Running the Application

1. Set up environment variables in `.env` file
   ```
   # Example .env file
   ANTHROPIC_API_KEY=your_anthropic_api_key
   SECRET_KEY=your_secret_key
   
   # External data sources API keys
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
   BINANCE_API_KEY=your_binance_api_key
   BINANCE_API_SECRET=your_binance_api_secret
   ```

2. Start the backend server
   ```
   ./run.sh server
   # or
   uvicorn src.app.main:app --reload
   ```

3. Start the frontend development server (not implemented yet)
   ```
   cd frontend
   npm start
   ```

4. Visit the API documentation at `http://localhost:8000/docs`

## Development Workflow

- **Code Style**: We use Black for Python formatting and ESLint for JavaScript
- **Testing**: Write tests for all new functionality using pytest
- **Version Control**: Follow the GitHub flow with feature branches and pull requests

## License

[Specify your license here]