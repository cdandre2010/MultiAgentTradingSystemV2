# Trading Strategy System: Test Specifications

This document provides detailed test specifications for the Trading Strategy System, organized by component type. These specifications follow the Test Driven Development (TDD) approach, where tests are written before implementation.

## Table of Contents
1. [Unit Tests](#unit-tests)
2. [Integration Tests](#integration-tests)
3. [Agent Tests](#agent-tests)
4. [End-to-End Tests](#end-to-end-tests)
5. [Performance Tests](#performance-tests)
6. [Security Tests](#security-tests)
7. [Test Execution Guidelines](#test-execution-guidelines)

## Unit Tests

### Authentication System Tests

```python
def test_user_registration_validation():
    """Test user registration input validation."""
    # Test case: Missing required fields
    response = client.post("/api/auth/register", json={
        "username": "testuser"
        # Missing email and password
    })
    assert response.status_code == 422
    
    # Test case: Invalid email format
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "invalid-email",
        "password": "securePassword123"
    })
    assert response.status_code == 422
    
    # Test case: Password too short
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "short"
    })
    assert response.status_code == 422

def test_user_registration_success():
    """Test successful user registration."""
    response = client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securePassword123"
    })
    assert response.status_code == 201
    data = response.json()
    assert "user_id" in data
    assert "token" in data
    assert isinstance(data["user_id"], str)
    assert isinstance(data["token"], str)

def test_user_registration_duplicate():
    """Test registration with duplicate username/email."""
    # Register first user
    client.post("/api/auth/register", json={
        "username": "duplicate",
        "email": "duplicate@example.com",
        "password": "securePassword123"
    })
    
    # Attempt duplicate username
    response = client.post("/api/auth/register", json={
        "username": "duplicate",
        "email": "different@example.com",
        "password": "securePassword123"
    })
    assert response.status_code == 400
    
    # Attempt duplicate email
    response = client.post("/api/auth/register", json={
        "username": "different",
        "email": "duplicate@example.com",
        "password": "securePassword123"
    })
    assert response.status_code == 400

def test_user_login_success():
    """Test successful user login."""
    # Register user first
    client.post("/api/auth/register", json={
        "username": "logintest",
        "email": "login@example.com",
        "password": "securePassword123"
    })
    
    # Test login
    response = client.post("/api/auth/login", json={
        "username": "logintest",
        "password": "securePassword123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "token" in data

def test_user_login_invalid_credentials():
    """Test login with invalid credentials."""
    # Register user first
    client.post("/api/auth/register", json={
        "username": "invalid",
        "email": "invalid@example.com",
        "password": "securePassword123"
    })
    
    # Test wrong password
    response = client.post("/api/auth/login", json={
        "username": "invalid",
        "password": "wrongPassword"
    })
    assert response.status_code == 401
    
    # Test non-existent user
    response = client.post("/api/auth/login", json={
        "username": "nonexistent",
        "password": "anyPassword"
    })
    assert response.status_code == 401

def test_jwt_token_validation():
    """Test JWT token validation."""
    # Register and login to get token
    client.post("/api/auth/register", json={
        "username": "tokentest",
        "email": "token@example.com",
        "password": "securePassword123"
    })
    login_response = client.post("/api/auth/login", json={
        "username": "tokentest",
        "password": "securePassword123"
    })
    token = login_response.json()["token"]
    
    # Test protected endpoint with valid token
    response = client.get("/api/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    
    # Test with invalid token
    response = client.get("/api/protected", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401
    
    # Test with expired token (would require time manipulation or a test token with short expiry)
    # This would be implementation-specific
```

### Neo4j Database Tests

```python
def test_neo4j_connection():
    """Test Neo4j database connection."""
    driver = get_neo4j_driver()
    
    with driver.session() as session:
        result = session.run("RETURN 1 AS num")
        record = result.single()
        assert record["num"] == 1

def test_create_strategy_type():
    """Test creation of a StrategyType node."""
    driver = get_neo4j_driver()
    
    with driver.session() as session:
        # Clear any existing test data
        session.run("MATCH (s:StrategyType {name: 'TestStrategy'}) DETACH DELETE s")
        
        # Create new strategy type
        result = session.run("""
            CREATE (s:StrategyType {
                name: 'TestStrategy',
                description: 'A test strategy',
                version: 1
            })
            RETURN s
        """)
        record = result.single()
        node = record["s"]
        
        assert node["name"] == "TestStrategy"
        assert node["description"] == "A test strategy"
        assert node["version"] == 1

def test_create_relationship():
    """Test creation of a relationship between nodes."""
    driver = get_neo4j_driver()
    
    with driver.session() as session:
        # Clear any existing test data
        session.run("""
            MATCH (s:StrategyType {name: 'RelationTest'})-[r]->(i:Indicator {name: 'TestRSI'})
            DETACH DELETE s, i
        """)
        
        # Create nodes and relationship
        result = session.run("""
            CREATE (s:StrategyType {name: 'RelationTest', description: 'Test'})
            CREATE (i:Indicator {name: 'TestRSI', description: 'Test RSI'})
            CREATE (s)-[r:COMMONLY_USES]->(i)
            RETURN r
        """)
        assert result.single() is not None
        
        # Verify relationship exists
        result = session.run("""
            MATCH (s:StrategyType {name: 'RelationTest'})-[r:COMMONLY_USES]->(i:Indicator {name: 'TestRSI'})
            RETURN r
        """)
        assert result.single() is not None

def test_query_related_nodes():
    """Test querying related nodes."""
    driver = get_neo4j_driver()
    
    with driver.session() as session:
        # Set up test data
        session.run("""
            CREATE (s:StrategyType {name: 'QueryTest', description: 'Test'})
            CREATE (i1:Indicator {name: 'TestRSI', description: 'Test RSI'})
            CREATE (i2:Indicator {name: 'TestMACD', description: 'Test MACD'})
            CREATE (s)-[:COMMONLY_USES]->(i1)
            CREATE (s)-[:COMMONLY_USES]->(i2)
        """)
        
        # Query indicators used by strategy
        result = session.run("""
            MATCH (s:StrategyType {name: 'QueryTest'})-[:COMMONLY_USES]->(i:Indicator)
            RETURN i.name AS name
        """)
        names = [record["name"] for record in result]
        
        assert "TestRSI" in names
        assert "TestMACD" in names
        assert len(names) == 2
```

### InfluxDB Tests

```python
def test_influxdb_connection():
    """Test InfluxDB connection."""
    client = get_influxdb_client()
    health = client.health()
    
    assert health.status == "pass"

def test_write_ohlcv_data():
    """Test writing OHLCV data to InfluxDB."""
    client = get_influxdb_client()
    write_api = client.write_api()
    
    # Create test data point
    point = Point("BTCUSDT") \
        .tag("frequency", "1h") \
        .field("open", 50000.0) \
        .field("high", 51000.0) \
        .field("low", 49000.0) \
        .field("close", 50500.0) \
        .field("volume", 100.0) \
        .time(datetime.utcnow())
    
    # Write data
    write_api.write(bucket="market_data", record=point)
    
    # Allow time for write to complete
    time.sleep(1)
    
    # Query written data
    query_api = client.query_api()
    query = f'''
        from(bucket:"market_data")
        |> range(start: -1h)
        |> filter(fn: (r) => r._measurement == "BTCUSDT" and r.frequency == "1h")
    '''
    result = query_api.query(org="my-org", query=query)
    
    # Verify data was written
    assert len(result) > 0
    
    # Clean up test data
    delete_api = client.delete_api()
    delete_api.delete(
        start=datetime.utcnow() - timedelta(hours=1),
        stop=datetime.utcnow() + timedelta(hours=1),
        predicate='_measurement="BTCUSDT"',
        bucket="market_data"
    )

def test_query_historical_data():
    """Test querying historical OHLCV data."""
    client = get_influxdb_client()
    write_api = client.write_api()
    
    # Create historical test data (5 points)
    base_time = datetime.utcnow() - timedelta(days=5)
    for i in range(5):
        point_time = base_time + timedelta(days=i)
        point = Point("ETHUSDT") \
            .tag("frequency", "1d") \
            .field("close", 3000.0 + (i * 100)) \
            .time(point_time)
        write_api.write(bucket="market_data", record=point)
    
    # Allow time for write to complete
    time.sleep(1)
    
    # Query historical data
    query_api = client.query_api()
    query = f'''
        from(bucket:"market_data")
        |> range(start: {int(base_time.timestamp())})
        |> filter(fn: (r) => r._measurement == "ETHUSDT" and r.frequency == "1d")
        |> sort(columns: ["_time"])
    '''
    result = query_api.query(org="my-org", query=query)
    
    # Extract values
    values = []
    for table in result:
        for record in table.records:
            values.append(record.get_value())
    
    # Verify correct number of points and values
    assert len(values) == 5
    assert values[0] == 3000.0
    assert values[4] == 3400.0
    
    # Clean up test data
    delete_api = client.delete_api()
    delete_api.delete(
        start=base_time - timedelta(days=1),
        stop=datetime.utcnow() + timedelta(days=1),
        predicate='_measurement="ETHUSDT"',
        bucket="market_data"
    )
```

### React Component Tests

```javascript
// Login Component Test
test('login form submits correctly', async () => {
  // Mock API response
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ token: 'test-token', user_id: '123' }),
    })
  );

  // Render component
  render(<Login />);
  
  // Fill form
  fireEvent.change(screen.getByLabelText(/username/i), {
    target: { value: 'testuser' },
  });
  
  fireEvent.change(screen.getByLabelText(/password/i), {
    target: { value: 'password123' },
  });
  
  // Submit form
  fireEvent.click(screen.getByRole('button', { name: /log in/i }));
  
  // Wait for form submission
  await waitFor(() => {
    expect(global.fetch).toHaveBeenCalledWith(
      '/api/auth/login',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          username: 'testuser',
          password: 'password123',
        }),
      })
    );
  });
  
  // Check for successful login (e.g., token stored)
  expect(localStorage.getItem('token')).toBe('test-token');
});

// Strategy Component Test
test('strategy type selection shows recommendations', async () => {
  // Mock API response
  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve([
        { name: 'momentum', description: 'Momentum strategy' },
        { name: 'meanreversion', description: 'Mean reversion strategy' }
      ]),
    })
  );

  // Render component
  render(<StrategyTypeSelector />);
  
  // Wait for options to load
  await screen.findByText(/momentum/i);
  
  // Select momentum strategy
  fireEvent.click(screen.getByText(/momentum/i));
  
  // Check that recommendation appears
  expect(await screen.findByText(/RSI is commonly used/i)).toBeInTheDocument();
});
```

## Integration Tests

### API and Database Integration

```python
def test_strategy_creation_api_with_db():
    """Test strategy creation through API with database integration."""
    # Register and login
    client.post("/api/auth/register", json={
        "username": "strategytest",
        "email": "strategy@example.com",
        "password": "securePassword123"
    })
    login_response = client.post("/api/auth/login", json={
        "username": "strategytest",
        "password": "securePassword123"
    })
    token = login_response.json()["token"]
    
    # Create strategy through API
    strategy_data = {
        "name": "My Test Strategy",
        "strategy_type": "momentum",
        "instrument": "BTCUSDT",
        "frequency": "1h",
        "indicators": [
            {"name": "RSI", "parameters": {"period": 14}}
        ],
        "conditions": [
            {"type": "entry", "logic": "RSI < 30"},
            {"type": "exit", "logic": "RSI > 70"}
        ],
        "position_sizing": {"method": "percent", "value": 2},
        "risk_management": {
            "stop_loss": 5,
            "take_profit": 10,
            "max_positions": 1
        }
    }
    response = client.post(
        "/api/strategies",
        json=strategy_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    strategy_id = response.json()["strategy_id"]
    
    # Verify strategy exists in Neo4j
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (s:Strategy {id: $id})
            RETURN s.name AS name
        """, id=strategy_id)
        record = result.single()
        assert record["name"] == "My Test Strategy"
        
        # Verify relationships
        result = session.run("""
            MATCH (s:Strategy {id: $id})-[:HAS_INDICATOR]->(i:Indicator)
            RETURN i.name AS name
        """, id=strategy_id)
        record = result.single()
        assert record["name"] == "RSI"

def test_backtest_api_with_db():
    """Test backtest execution through API with database integration."""
    # Create strategy and get ID (assuming previous test)
    # ...
    
    # Prepare historical data in InfluxDB
    client = get_influxdb_client()
    write_api = client.write_api()
    
    # Create test data points (simplified)
    base_time = datetime.utcnow() - timedelta(days=30)
    for i in range(30):
        point_time = base_time + timedelta(days=i)
        # Create data with RSI cycling between oversold and overbought
        rsi_value = 20 if i % 10 < 5 else 80
        
        point = Point("BTCUSDT") \
            .tag("frequency", "1h") \
            .field("close", 50000.0 + (i * 100)) \
            .field("rsi", rsi_value) \
            .time(point_time)
        write_api.write(bucket="market_data", record=point)
    
    # Run backtest through API
    response = client.post(
        f"/api/backtest",
        json={
            "strategy_id": strategy_id,
            "start_date": (base_time + timedelta(days=1)).isoformat(),
            "end_date": (base_time + timedelta(days=29)).isoformat()
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    backtest_id = response.json()["backtest_id"]
    
    # Get backtest results
    response = client.get(
        f"/api/backtest/{backtest_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    results = response.json()
    
    # Verify results
    assert "performance" in results
    assert "trades" in results
    assert len(results["trades"]) > 0
```

### Frontend and Backend Integration

```javascript
// This would typically be done with tools like Cypress or Playwright
// Here's a simplified example:

describe('End-to-end strategy creation flow', () => {
  beforeAll(async () => {
    // Set up test user
    // ...
  });
  
  test('user can create and backtest a strategy', async () => {
    // Log in
    await page.goto('/login');
    await page.fill('[name=username]', 'testuser');
    await page.fill('[name=password]', 'password123');
    await page.click('button[type=submit]');
    
    // Navigate to strategy creation
    await page.click('text=Create Strategy');
    
    // Select strategy type
    await page.click('text=Momentum');
    await page.click('button:has-text("Continue")');
    
    // Select instrument
    await page.click('text=BTCUSDT');
    await page.click('button:has-text("Continue")');
    
    // Select frequency
    await page.click('text=1 hour');
    await page.click('button:has-text("Continue")');
    
    // Add indicator
    await page.click('text=RSI');
    await page.fill('[name=period]', '14');
    await page.click('button:has-text("Add Indicator")');
    await page.click('button:has-text("Continue")');
    
    // Define conditions
    await page.fill('[name=entry-condition]', 'RSI < 30');
    await page.fill('[name=exit-condition]', 'RSI > 70');
    await page.click('button:has-text("Continue")');
    
    // Set position sizing and risk management
    await page.fill('[name=position-size]', '2');
    await page.fill('[name=stop-loss]', '5');
    await page.fill('[name=take-profit]', '10');
    await page.click('button:has-text("Continue")');
    
    // Review and create
    await page.click('button:has-text("Create Strategy")');
    
    // Verify strategy created
    expect(await page.textContent('.success-message')).toContain('Strategy created successfully');
    
    // Run backtest
    await page.click('button:has-text("Run Backtest")');
    
    // Wait for backtest to complete
    await page.waitForSelector('.backtest-results');
    
    // Verify results displayed
    expect(await page.isVisible('.performance-metrics')).toBe(true);
    expect(await page.isVisible('.trade-history')).toBe(true);
  });
});
```

## Agent Tests

### Master Agent Tests

```python
def test_master_agent_delegation():
    """Test Master Agent's ability to delegate tasks to specialized agents."""
    master_agent = MasterAgent()
    
    # Simulate conversation about strategy type
    response = master_agent.process_message({
        "role": "user",
        "content": "I want to create a momentum strategy for Bitcoin"
    })
    
    # Check that conversation agent was invoked
    assert "delegated_to" in response["metadata"]
    assert response["metadata"]["delegated_to"] == "conversation_agent"
    
    # Simulate validation request
    response = master_agent.process_message({
        "role": "system",
        "content": "Validate RSI parameter",
        "metadata": {
            "action": "validate",
            "parameters": {
                "indicator": "RSI",
                "parameter": "period",
                "value": 14
            }
        }
    })
    
    # Check that validation agent was invoked
    assert "delegated_to" in response["metadata"]
    assert response["metadata"]["delegated_to"] == "validation_agent"

def test_master_agent_state_management():
    """Test Master Agent's ability to maintain conversation state."""
    master_agent = MasterAgent()
    
    # Initialize conversation
    master_agent.process_message({
        "role": "user",
        "content": "I want to create a momentum strategy"
    })
    
    # Add instrument
    master_agent.process_message({
        "role": "user",
        "content": "I want to trade Bitcoin"
    })
    
    # Add indicator
    master_agent.process_message({
        "role": "user",
        "content": "Let's use RSI"
    })
    
    # Check state
    state = master_agent.get_state()
    assert "strategy_type" in state
    assert state["strategy_type"] == "momentum"
    assert "instrument" in state
    assert "bitcoin" in state["instrument"].lower()
    assert "indicators" in state
    assert "RSI" in [i["name"] for i in state["indicators"]]
```

### Conversational Agent Tests

```python
def test_conversation_agent_strategy_type_extraction():
    """Test Conversational Agent's ability to extract strategy type."""
    agent = ConversationalAgent()
    
    response = agent.process_message({
        "role": "user",
        "content": "I want to build a mean reversion strategy that buys when prices are oversold"
    })
    
    assert "strategy_type" in response["extracted_info"]
    assert response["extracted_info"]["strategy_type"] == "mean reversion"

def test_conversation_agent_indicator_extraction():
    """Test Conversational Agent's ability to extract indicators."""
    agent = ConversationalAgent()
    
    response = agent.process_message({
        "role": "user",
        "content": "I want to use RSI with period 14 and MACD with standard settings"
    })
    
    assert "indicators" in response["extracted_info"]
    indicators = response["extracted_info"]["indicators"]
    assert len(indicators) == 2
    
    assert any(i["name"] == "RSI" for i in indicators)
    rsi = next(i for i in indicators if i["name"] == "RSI")
    assert "parameters" in rsi
    assert "period" in rsi["parameters"]
    assert rsi["parameters"]["period"] == 14
    
    assert any(i["name"] == "MACD" for i in indicators)
```

### Validation Agent Tests

```python
def test_validation_agent_parameter_validation():
    """Test Validation Agent's parameter range checking."""
    agent = ValidationAgent()
    
    # Test valid parameter
    result = agent.validate_parameter({
        "indicator": "RSI",
        "parameter": "period",
        "value": 14
    })
    assert result["valid"] is True
    
    # Test parameter below minimum
    result = agent.validate_parameter({
        "indicator": "RSI",
        "parameter": "period",
        "value": 2  # Assuming minimum is higher
    })
    assert result["valid"] is False
    assert "minimum" in result["message"].lower()
    
    # Test parameter above maximum
    result = agent.validate_parameter({
        "indicator": "RSI",
        "parameter": "period",
        "value": 1000  # Assuming maximum is lower
    })
    assert result["valid"] is False
    assert "maximum" in result["message"].lower()

def test_validation_agent_strategy_completeness():
    """Test Validation Agent's strategy completeness checking."""
    agent = ValidationAgent()
    
    # Test complete strategy
    result = agent.validate_completeness({
        "strategy_type": "momentum",
        "instrument": "BTCUSDT",
        "frequency": "1h",
        "indicators": [{"name": "RSI", "parameters": {"period": 14}}],
        "conditions": [
            {"type": "entry", "logic": "RSI < 30"},
            {"type": "exit", "logic": "RSI > 70"}
        ],
        "position_sizing": {"method": "percent", "value": 2},
        "risk_management": {
            "stop_loss": 5,
            "take_profit": 10,
            "max_positions": 1
        }
    })
    assert result["valid"] is True
    
    # Test missing conditions
    result = agent.validate_completeness({
        "strategy_type": "momentum",
        "instrument": "BTCUSDT",
        "frequency": "1h",
        "indicators": [{"name": "RSI", "parameters": {"period": 14}}],
        # Missing conditions
        "position_sizing": {"method": "percent", "value": 2},
        "risk_management": {
            "stop_loss": 5,
            "take_profit": 10,
            "max_positions": 1
        }
    })
    assert result["valid"] is False
    assert "conditions" in result["message"].lower()
```

## End-to-End Tests

These tests verify complete workflows from start to finish:

```python
def test_full_strategy_creation_workflow():
    """Test the complete strategy creation workflow."""
    # This would be a comprehensive test covering:
    # 1. User login
    # 2. Strategy creation via conversational interface
    # 3. Strategy validation
    # 4. Saving to database
    # 5. Retrieving the strategy
    # Too lengthy to include in full here

def test_strategy_backtest_workflow():
    """Test the complete backtest workflow."""
    # This would cover:
    # 1. Creating a strategy
    # 2. Setting up historical data
    # 3. Running a backtest
    # 4. Getting performance metrics
    # 5. Receiving improvement suggestions
    # Too lengthy to include in full here

def test_real_time_data_workflow():
    """Test the real-time data workflow."""
    # This would cover:
    # 1. Setting up WebSocket connection
    # 2. Subscribing to market data
    # 3. Receiving updates
    # 4. Processing signals
    # Too lengthy to include in full here
```

## Performance Tests

```python
def test_concurrent_backtest_performance():
    """Test performance with multiple concurrent backtests."""
    # Create 10 test strategies
    strategies = []
    for i in range(10):
        # Create strategy...
        strategies.append(strategy_id)
    
    # Run backtests concurrently
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(run_backtest, strategy_id)
            for strategy_id in strategies
        ]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    end_time = time.time()
    
    # Assert performance
    assert len(results) == 10
    assert end_time - start_time < 30  # Should complete in under 30 seconds

def test_large_dataset_performance():
    """Test performance with a large historical dataset."""
    # Create historical dataset with 1 year of 1-minute data
    # (would be over 500,000 data points)
    # ...
    
    # Run backtest on large dataset
    start_time = time.time()
    result = run_backtest(strategy_id, large_dataset=True)
    end_time = time.time()
    
    # Assert performance
    assert end_time - start_time < 60  # Should complete in under 60 seconds
```

## Security Tests

```python
def test_sql_injection_prevention():
    """Test prevention of SQL injection attacks."""
    # Attempt SQL injection in username
    response = client.post("/api/auth/login", json={
        "username": "' OR 1=1--",
        "password": "password"
    })
    assert response.status_code == 401  # Should fail authentication
    
    # Attempt SQL injection in strategy name
    response = client.post(
        "/api/strategies",
        json={"name": "'; DROP TABLE users;--", "components": {}},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201  # Should succeed but sanitize input
    
    # Verify database integrity
    # ...

def test_xss_prevention():
    """Test prevention of cross-site scripting attacks."""
    # Attempt XSS in strategy name
    response = client.post(
        "/api/strategies",
        json={"name": "<script>alert('XSS')</script>", "components": {}},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    strategy_id = response.json()["strategy_id"]
    
    # Get strategy and verify script tags were escaped
    response = client.get(
        f"/api/strategies/{strategy_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert "<script>" not in response.json()["name"]

def test_rate_limiting():
    """Test rate limiting protection."""
    # Make 100 requests in quick succession
    responses = []
    for i in range(100):
        response = client.get("/api/strategies", headers={"Authorization": f"Bearer {token}"})
        responses.append(response.status_code)
    
    # Verify some requests were rate limited
    assert 429 in responses  # HTTP 429 Too Many Requests
```

## Test Execution Guidelines

### Running Tests

1. **Environment Setup**:
   ```
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements-dev.txt
   ```

2. **Unit Tests**:
   ```
   pytest tests/unit/
   ```

3. **Integration Tests**:
   ```
   pytest tests/integration/
   ```

4. **Agent Tests**:
   ```
   pytest tests/agents/
   ```

5. **End-to-End Tests**:
   ```
   pytest tests/e2e/
   ```

6. **Performance Tests**:
   ```
   pytest tests/performance/
   ```

7. **Security Tests**:
   ```
   pytest tests/security/
   ```

8. **All Tests**:
   ```
   pytest
   ```

### Continuous Integration

- Run unit and integration tests on every pull request
- Run all tests before merging to main branch
- Performance tests should be run nightly
- Security tests should be run weekly

### Test Coverage

- Aim for minimum 80% code coverage
- Use coverage.py to measure coverage:
  ```
  coverage run -m pytest
  coverage report
  coverage html  # Generate HTML report
  ```

### Mock Services

- Use Docker containers for Neo4j and InfluxDB during testing
- For agent tests, use mock LLM responses to avoid API calls
- Create test fixtures for common data setups

### Troubleshooting Failed Tests

1. Check test logs for detailed error messages
2. Verify test environment configuration
3. Check database state before and after tests
4. Use pytest's `-v` flag for verbose output
5. Use `pytest.set_trace()` for debugging specific tests

This test specification provides a comprehensive framework for implementing the Trading Strategy System following Test Driven Development principles.