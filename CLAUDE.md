# CLAUDE.md - Multi-Agent Trading System V2

## Build/Test/Lint Commands
- Setup environment: `python -m pip install -e .`
- Run server: `uvicorn app.main:app --reload`
- Lint code: `flake8 src/ tests/`
- Format code: `black src/ tests/`
- Type check: `mypy src/ tests/`
- Run all tests: `pytest tests/`
- Run single test: `pytest tests/path_to_test.py::TestClass::test_method -v`
- Run with coverage: `pytest --cov=src tests/`
- Build frontend: `cd frontend && npm run build`
- Run frontend dev server: `cd frontend && npm start`

## Code Style Guidelines
- **Architecture**: Agent-based with Master, Conversational, Validation, Data/Feature, Code, and Feedback agents
- **Imports**: Group standard library → third-party → local with alphabetical sorting
- **Formatting**: Use Black with 88 character line length, isort for import sorting
- **Types**: Comprehensive type hints for all functions and return values
- **Naming**: snake_case for variables/functions, PascalCase for classes, UPPER_CASE for constants
- **Documentation**: Google-style docstrings for public APIs
- **Error handling**: Custom exceptions with informative messages; log at appropriate levels
- **Testing**: Unit tests for all components, end-to-end tests for agent interactions
- **Database**: Separate data management layers for Neo4j, InfluxDB, and SQL databases