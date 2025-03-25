# Testing Guide for Multi-Agent Trading System V2

This document outlines the testing strategy and requirements for the Multi-Agent Trading System V2, with a focus on following Test-Driven Development (TDD) principles.

## Current Testing Status

### Well-Tested Components

1. **Indicator Service (TA-Lib Implementation)**
   - Comprehensive test coverage in `test_indicators.py`
   - Tests for all indicator types (trend, momentum, volatility, volume, pattern)
   - Cache functionality testing
   - Parameter validation testing
   - Error handling

2. **Agent System**
   - Master Agent: `test_master_agent.py` covers message routing and processing
   - Conversational Agent: `test_conversational_agent.py` tests parameter extraction and message handling
   - Validation Agent: `test_validation_agent.py` covers validation rules and completeness checks
   - Knowledge Integration: `test_knowledge_integration.py` tests Neo4j-based recommendations

3. **Database Components**
   - Strategy Repository: `test_strategy_repository.py` for Neo4j operations
   - User Repository: `test_user_repository.py` for user data persistence
   - Data Integrity Service: `test_data_integrity.py` for data quality features
   - Data Versioning Service: `test_data_versioning.py` for snapshot management

### Components Requiring Testing

1. **Data Services**
   - **data_availability.py**: No dedicated tests
     - Need tests for availability checking across timeframes
     - Need tests for missing data handling
     - Need tests for integration with data sources
   
   - **data_retrieval.py**: No dedicated tests
     - Need tests for data retrieval from multiple sources
     - Need tests for fallback mechanisms
     - Need tests for caching behavior
     - Need tests for async operations

2. **Data/Feature Agent (Issue 3.2)**
   - Need comprehensive test suite before implementation begins
   - Tests must cover:
     - Message protocol handling
     - Integration with IndicatorService
     - Data validation functionality
     - Feature matrix generation
     - Visualization data formatting
     - Error handling and fallbacks

3. **Integration Tests**
   - Limited integration tests between components
   - Need tests showing full workflow from conversation to validation to data processing
   - Need tests for database interactions end-to-end

## Test-Driven Development Approach for Data/Feature Agent

### Step 1: Create Tests for Dependencies
Before implementing the Data/Feature Agent, create tests for the dependencies:

```python
# Example test for data_availability.py
def test_data_availability_check():
    service = DataAvailabilityService()
    result = service.check_availability(
        instrument="BTCUSDT",
        timeframe="1h",
        start_date="2023-01-01",
        end_date="2023-01-31"
    )
    assert "is_complete" in result
    assert "missing_dates" in result
    assert "coverage_percentage" in result
    assert "available_sources" in result
```

```python
# Example test for data_retrieval.py
def test_data_retrieval_fallback():
    service = DataRetrievalService()
    result = service.get_data(
        instrument="BTCUSDT",
        timeframe="1h",
        start_date="2023-01-01",
        end_date="2023-01-31",
        sources=["influxdb", "binance", "yahoo"]
    )
    assert result.instrument == "BTCUSDT"
    assert len(result.data) > 0
    assert hasattr(result, "source")  # Should indicate which source was used
```

### Step 2: Create Tests for Data/Feature Agent

```python
# Example test for agent message handling
def test_agent_message_handling():
    agent = DataFeatureAgent()
    message = {
        "type": "calculate_indicator",
        "data": {
            "indicator": "RSI",
            "parameters": {"period": 14},
            "instrument": "BTCUSDT",
            "timeframe": "1h",
            "start_date": "2023-01-01",
            "end_date": "2023-01-31"
        }
    }
    
    response = agent.process_message(message)
    assert response["type"] == "indicator_result"
    assert "values" in response["data"]
    assert "metadata" in response["data"]
```

```python
# Example test for indicator calculation integration
def test_indicator_calculation_integration():
    agent = DataFeatureAgent()
    result = agent.calculate_indicator(
        indicator="RSI",
        parameters={"period": 14},
        instrument="BTCUSDT",
        timeframe="1h",
        start_date="2023-01-01",
        end_date="2023-01-31"
    )
    
    assert "values" in result
    assert len(result["values"]) > 0
    assert "metadata" in result
```

```python
# Example test for data validation
def test_data_validation():
    agent = DataFeatureAgent()
    validation = agent.validate_data_for_strategy(
        strategy_id="test-strategy",
        data_config={
            "instrument": "BTCUSDT",
            "timeframe": "1h",
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
            "indicators": [{"name": "RSI", "parameters": {"period": 14}}]
        }
    )
    
    assert validation["is_valid"] is not None
    assert "issues" in validation
    assert "recommendations" in validation
```

### Step 3: Implement Agent Based on Tests

Only after tests are written, implement the Data/Feature Agent functionality:

1. Create the agent class that passes all tests
2. Implement minimal functionality to make tests pass
3. Refactor while maintaining test coverage
4. Add new tests for edge cases
5. Implement integration with other agents
6. Create integration tests

## Testing Tools and Practices

1. **Use pytest fixtures** to set up test data and dependencies
2. **Use mocking** for external services like databases and APIs
3. **Organize tests** by component and functionality
4. **Run tests frequently** during development
5. **Track code coverage** and aim for >90% coverage
6. **Include edge cases and error conditions**
7. **Test both synchronous and asynchronous functionality**
8. **Create integration tests** that span multiple components

## Executing Tests

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run specific test file
pytest tests/unit/test_data_feature_agent.py

# Run with coverage
pytest --cov=src tests/

# Run with detailed output
pytest -v tests/unit/test_data_feature_agent.py
```

## CI/CD Integration (Future)

Future plans include setting up GitHub Actions to:
1. Run tests on every pull request
2. Generate coverage reports
3. Enforce minimum coverage requirements
4. Run integration tests in a staging environment

## Additional Testing Considerations

1. **Test Data Generation**
   - Create scripts to generate consistent test data for all components
   - Build a shared test data repository for standard market scenarios
   - Include edge cases and anomalies in test data
   - Consider time-based scenarios (market open/close, weekends, holidays)

2. **Documentation Integration**
   - Update API documentation with new Data/Feature Agent endpoints
   - Include example responses in documentation
   - Document test strategies for new contributors
   - Add visualization examples to documentation

3. **Dependency Management**
   - Verify requirements.txt and setup.py reflect TA-Lib dependencies
   - Document system requirements for TA-Lib C/C++ libraries
   - Include installation instructions for different platforms
   - Consider containerized testing to ensure consistent environments

4. **Team TDD Practices**
   - Consider a TDD workshop for team alignment
   - Establish code review guidelines focused on test coverage
   - Define minimum test coverage requirements for components
   - Create templates for test files to ensure consistency

5. **Performance Metrics**
   - Implement metrics collection for the Data/Feature Agent
   - Track calculation times for different indicators
   - Monitor memory usage during batch operations
   - Establish performance baselines and regression tests