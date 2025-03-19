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
- Master Agent: Orchestrates workflow and coordinates other agents
- Conversational Agent: Handles natural language dialogue with users
- Validation Agent: Ensures strategies are valid and complete
- Data/Feature Agent: Retrieves and processes market data
- Code Agent: Generates executable strategy code
- Feedback Agent: Analyzes results and suggests improvements

### Technology Stack
- **Frontend**: React (JavaScript)
- **Backend**: FastAPI (Python)
- **Agentic Layer**: LangChain with Claude 3.7 Sonnet
- **Data Layer**: Neo4j, InfluxDB, SQLite/PostgreSQL

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 16+
- Neo4j Database
- InfluxDB Database

### Installation

1. Clone the repository
   ```
   git clone https://github.com/yourusername/MultiAgentTradingSystemV2.git
   cd MultiAgentTradingSystemV2
   ```

2. Install backend dependencies
   ```
   python -m pip install -e ".[dev]"
   ```

3. Install frontend dependencies
   ```
   cd frontend
   npm install
   ```

### Running the Application

1. Start the backend server
   ```
   uvicorn app.main:app --reload
   ```

2. Start the frontend development server
   ```
   cd frontend
   npm start
   ```

## Development Workflow

- **Code Style**: We use Black for Python formatting and ESLint for JavaScript
- **Testing**: Write tests for all new functionality using pytest
- **Version Control**: Follow the GitHub flow with feature branches and pull requests

## License

[Specify your license here]