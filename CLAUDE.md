# CLAUDE.md - Multi-Agent Trading System V2

## Build/Test/Lint Commands
- Setup environment: `python -m pip install -e .`
- Run server: `uvicorn src.app.main:app --reload`
- Run server with host & port: `uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000`
- Lint code: `flake8 src/ tests/`
- Format code: `black src/ tests/`
- Type check: `mypy src/ tests/`
- Run all tests: `pytest tests/`
- Run unit tests only: `pytest tests/unit/`
- Run single test: `pytest tests/path_to_test.py::TestClass::test_method -v`
- Run with coverage: `pytest --cov=src tests/`
- Build frontend: `cd frontend && npm run build`
- Run frontend dev server: `cd frontend && npm start`
- Run helper script: `./run.sh [command]` (setup, server, test, lint, format, typecheck, clean)
- Swagger UI: Visit `http://localhost:8000/docs` when server is running
- Test data connectors: `python scripts/test_connectors.py [--binance] [--yfinance] [--alphavantage] [--csv]`
- Initialize Neo4j enhanced schema: `python scripts/init_neo4j.py`
- Run Neo4j repository tests: `pytest tests/unit/test_strategy_repository.py -v`

## Project Structure
- `src/`: Source code
  - `app/`: FastAPI application
    - `routers/`: API route handlers 
    - `auth.py`: Authentication module
    - `config.py`: Application configuration
    - `main.py`: FastAPI app initialization
  - `agents/`: Agent implementation 
  - `database/`: Database connections and repositories
    - `repositories/`: Data access classes
    - `scripts/`: Database initialization scripts
      - `neo4j_init.cypher`: Basic Neo4j schema
      - `neo4j_init_enhanced.cypher`: Enhanced knowledge graph schema
    - `connection.py`: Database connection manager
    - `strategy_repository.py`: Repository for Neo4j knowledge graph operations
  - `models/`: Pydantic data models
  - `data_sources/`: External data source connectors
    - `base.py`: Base connector class
    - `binance.py`: Binance exchange connector
    - `yfinance.py`: Yahoo Finance connector
    - `alpha_vantage.py`: Alpha Vantage connector
    - `csv.py`: Local CSV file connector
  - `utils/`: Utility functions
    - `visualization.py`: Knowledge graph visualization tools
- `tests/`: Test files
  - `unit/`: Unit tests
    - `test_strategy_repository.py`: Tests for Neo4j knowledge graph repository
  - `integration/`: Integration tests
- `scripts/`: Helper scripts
  - `test_connectors.py`: Script to test data source connectors
  - `init_neo4j.py`: Script to initialize Neo4j with enhanced schema
- `frontend/`: React frontend (to be implemented)
- `docker/`: Docker configurations (to be implemented)

## Code Style Guidelines
- **Architecture**: Agent-based with Master, Conversational, Validation, Data/Feature, Code, and Feedback agents (Master, Conversational, and Validation agents implemented; others planned)
- **Knowledge-Driven Approach**: ConversationalAgent constructs strategies by querying Neo4j for appropriate components, ValidationAgent verifies using relationship data
- **API Design**: RESTful endpoints with OAuth2 authentication, consistent error responses
- **Imports**: Group standard library → third-party → local with alphabetical sorting
- **Formatting**: Use Black with 88 character line length, isort for import sorting
- **Types**: Comprehensive type hints for all functions and return values
- **Naming**: snake_case for variables/functions, PascalCase for classes, UPPER_CASE for constants
- **Documentation**: Google-style docstrings for public APIs
- **Error handling**: Custom exceptions with informative messages; log at appropriate levels
- **Testing**: Unit tests for all components, end-to-end tests for agent interactions
- **Database**: Separate data management layers for Neo4j, InfluxDB, and SQL databases
- **Authentication**: JWT-based token authentication with refresh tokens and role-based permissions
- **Repository Pattern**: All database access through repository classes

## Development Workflow
1. Pick an issue from the project board
2. Create a feature branch: `git checkout -b feature/issue-number-description`
3. Implement the feature following TDD approach
4. Run tests and linting: `./run.sh test && ./run.sh lint`
5. Commit changes: `git commit -m "Issue #X: Description of changes"`
6. Push branch: `git push -u origin feature/issue-number-description`
7. Create pull request on GitHub
8. Update project board

## Database Management and Testing Tips

1. Neo4j Database Management:
   - To clear Neo4j database: `python clear_neo4j.py`
   - To initialize/reinitialize Neo4j: `python scripts/init_neo4j.py` 
   - Neo4j Configuration: 
     * Neo4j Desktop on Windows: Uses port 7689 (configured in Neo4j Desktop settings)
     * Docker Neo4j: Maps internal port 7687 to external port 7689 (configured in docker-compose.yml)
     * Both setups use same credentials: neo4j/SchoolsOut2025
     * Browser interface: http://localhost:7474 (login with neo4j/SchoolsOut2025)
   - Resetting Docker Neo4j completely:
     * `docker-compose down -v` (removes volumes)
     * `docker-compose up -d` (recreates container)
   - Run repository tests: `pytest tests/unit/test_strategy_repository.py -v`
   - Use `--log-cli-level=INFO` to see detailed logging during tests

2. Running tests on Windows:
   - Use correct virtual environment: `venv_win/Scripts/python.exe -m pytest ...` 
   - Make sure all dependencies are installed in the virtual environment
   - For Windows-specific issues with Neo4j, check connection settings and firewall

## TODO Items / Current Tasks

1. Advanced InfluxDB Data Management Features:
   - 🔄 Issue 3.1.1: Data Versioning and Audit System
     - Implement DataVersioningService class
     - Create snapshot creation and management system
     - Add data version comparison functionality
     - Implement retention policies for data versions
     - Create audit trail for data usage in backtests
   
   - 📅 Issue 3.1.2: Data Integrity and Adjustment Detection
     - Create detection algorithms for market data discrepancies
     - Implement corporate action identification
     - Add notification system for data anomalies
     - Build correction workflows for data issues
   
   - 📅 Issue 3.1.3: Indicator Calculation Service
     - Implement efficient indicator calculation engine
     - Create caching system for calculated indicators
     - Add parameter flexibility for indicators
     - Build visualization support for calculated indicators

2. Future Tasks:
   - Add more relationship types to the Neo4j knowledge graph
   - Enhance frontend to display knowledge-driven recommendations
   - Implement Data/Feature Agent (Issue 6.1)
   - Create interactive visualizations for strategy exploration

3. Technical Improvements:
   - Fix YFinance connector issues
     - Implement more robust error handling and retries
     - Add fallback mechanisms when API is unreliable
   - Address deprecated datetime.utcnow() warnings in codebase