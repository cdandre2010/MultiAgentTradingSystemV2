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
    - `connection.py`: Database connection manager
  - `models/`: Pydantic data models
  - `utils/`: Utility functions
- `tests/`: Test files
  - `unit/`: Unit tests
  - `integration/`: Integration tests
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