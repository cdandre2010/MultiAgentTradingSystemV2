# Trading Strategy System: Agent Architecture

## Overview

The Trading Strategy System uses a multi-agent architecture powered by LangChain and Claude 3.7 Sonnet. The system is organized into specialized agents, each responsible for specific tasks, coordinated by a Master Agent that manages workflow and communication between agents. This document details the architecture, responsibilities, and implementation approach for each agent.

## Agent System Design

### Architecture Diagram

```
┌─────────────────────────────────────┐
│            Master Agent                           │
│  (Orchestration & State Management)               │
└───────────────┬─────────────────────┘
                │
     ┌───────────┼─────────────────────┐
     │               │                             │
┌───▼───┐   ┌───▼───┐   ┌───────┐   ┌───▼───┐
│Conver-   │   │Valid-    │   │ Data/   │   │Feed-     │
│sational  │   │ation     │   │Feature  │   │back      │
│ Agent    │   │ Agent    │   │ Agent   │   │ Agent    │
└───────┘   └────────┘  └───┬───┘   └───────┘
                                     │
                               ┌───▼───┐
                               │ Code     │
                               │ Agent    │
                               └───────┘
```

### Message Format

All inter-agent communication uses a standardized JSON message format:

```json
{
  "message_id": "msg_12345",
  "timestamp": "2023-06-01T12:34:56Z",
  "sender": "master_agent",
  "recipient": "validation_agent",
  "message_type": "request",
  "content": {
    "action": "validate_parameter",
    "parameters": {
      "indicator": "RSI",
      "parameter_name": "period",
      "parameter_value": 14
    }
  },
  "context": {
    "strategy_id": "strat_6789",
    "conversation_id": "conv_5678",
    "user_id": "user_1234"
  }
}
```

## Agent Implementations

### Master Agent

**Purpose**: Orchestrate the overall workflow and coordinate communication between specialized agents.

**Implementation**:
- **Pattern**: RouterChain with ReAct for planning
- **State Management**: Maintains conversation state and strategy creation progress
- **Responsibilities**:
  - Route user messages to appropriate specialized agents
  - Maintain conversation context and history
  - Coordinate the strategy creation workflow
  - Handle error recovery and fallbacks
  - Track progress through strategy creation steps

**Code Structure**:
```python
class MasterAgent:
    def __init__(self):
        self.conversation_agent = ConversationalAgent()
        self.validation_agent = ValidationAgent()
        self.data_feature_agent = DataFeatureAgent()
        self.code_agent = CodeAgent()
        self.feedback_agent = FeedbackAgent()
        self.conversation_state = {}
        self.llm = Claude("claude-3-7-sonnet-20250219")
        
        # Create router chain
        self.router_chain = LLMRouterChain.from_llm(
            llm=self.llm,
            destination_chains={
                "conversation": self.conversation_agent.chain,
                "validation": self.validation_agent.chain,
                "data": self.data_feature_agent.chain,
                "code": self.code_agent.chain,
                "feedback": self.feedback_agent.chain
            }
        )
    
    def process_message(self, message):
        # Update state with message
        self.update_state(message)
        
        # Determine which agent should handle this message
        destination = self.route_message(message)
        
        # Forward to appropriate agent
        if destination == "conversation":
            response = self.conversation_agent.process(message, self.conversation_state)
        elif destination == "validation":
            response = self.validation_agent.process(message, self.conversation_state)
        # ... other destinations
        
        # Update state with response
        self.update_state(response)
        
        return response
    
    def route_message(self, message):
        # Use router chain to determine destination
        result = self.router_chain.run(message)
        return result.destination
    
    def update_state(self, message):
        # Extract relevant information and update state
        if "extracted_info" in message:
            for key, value in message["extracted_info"].items():
                self.conversation_state[key] = value
```

### Conversational Agent

**Purpose**: Engage with users in natural language to collect strategy requirements and guide them through the creation process.

**Implementation**:
- **Pattern**: Sequential Chain with Memory
- **LLM Integration**: Uses Claude 3.7 Sonnet with specialized prompts
- **Neo4j Integration**: Uses strategy repository for knowledge-driven recommendations
- **Responsibilities**:
  - Extract strategy components from natural language
  - Guide users through strategy creation steps with knowledge-driven recommendations
  - Provide explanations using relationship metadata from Neo4j
  - Enhance strategies with compatible components from knowledge graph
  - Handle non-linear conversation flows with context-aware recommendations

**Prompt Templates**:
```
# Conversational Agent - Strategy Type Identification
You are a specialized agent that helps users create trading strategies. 
Your current task is to identify the type of strategy the user wants to create.

Common strategy types include:
- Momentum
- Mean Reversion
- Trend Following
- Breakout
- Range Trading

User message: {user_message}

Extract the strategy type from the user's message. If unclear, ask a follow-up question.
```

**Code Structure**:
```python
class ConversationalAgent:
    def __init__(self):
        self.llm = Claude("claude-3-7-sonnet-20250219")
        self.memory = ConversationBufferMemory()
        
        # Create specialized chains for different steps
        self.strategy_type_chain = LLMChain(
            llm=self.llm,
            prompt=self.load_prompt("strategy_type_prompt.txt"),
            output_parser=StrategyTypeParser()
        )
        
        self.instrument_chain = LLMChain(
            llm=self.llm,
            prompt=self.load_prompt("instrument_prompt.txt"),
            output_parser=InstrumentParser()
        )
        
        # Additional chains for other steps...
    
    def process(self, message, state):
        # Determine current step in strategy creation
        current_step = state.get("current_step", "strategy_type")
        
        # Process based on current step
        if current_step == "strategy_type":
            result = self.strategy_type_chain.run(
                user_message=message["content"],
                history=self.memory.load_memory_variables({})["history"]
            )
            next_step = "instrument"
        elif current_step == "instrument":
            result = self.instrument_chain.run(
                user_message=message["content"],
                strategy_type=state.get("strategy_type", ""),
                history=self.memory.load_memory_variables({})["history"]
            )
            next_step = "frequency"
        # Additional steps...
        
        # Update memory
        self.memory.save_context({"user": message["content"]}, {"ai": result["response"]})
        
        return {
            "content": result["response"],
            "extracted_info": result["extracted_info"],
            "current_step": next_step
        }
```

### Validation Agent

**Purpose**: Ensure that user inputs and strategy components are valid, compatible, and complete.

**Implementation**:
- **Pattern**: ReAct Agent with Structured Output
- **Tools Integration**: Neo4j query tools, parameter validators, knowledge graph integration
- **Responsibilities**:
  - Validate parameter ranges and types using knowledge graph data
  - Check compatibility between components with Neo4j relationship queries
  - Verify strategy completeness against templates from knowledge graph
  - Generate human-readable explanations with relationship metadata
  - Provide knowledge-driven suggestions for improvement

**Tools Definitions**:
```python
TOOLS = [
    Tool(
        name="check_parameter_range",
        func=check_parameter_range,
        description="Checks if a parameter value is within the allowed range"
    ),
    Tool(
        name="check_indicator_compatibility",
        func=check_indicator_compatibility,
        description="Checks if an indicator is compatible with a strategy type"
    ),
    Tool(
        name="verify_strategy_completeness",
        func=verify_strategy_completeness,
        description="Verifies that a strategy has all required components"
    ),
    # Additional tools...
]
```

**Code Structure**:
```python
class ValidationAgent:
    def __init__(self):
        self.llm = Claude("claude-3-7-sonnet-20250219")
        self.tools = TOOLS
        
        # Create ReAct agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.load_prompt("validation_prompt.txt")
        )
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            verbose=True
        )
    
    def process(self, message, state):
        # Extract validation request
        if "action" in message.get("content", {}):
            action = message["content"]["action"]
            parameters = message["content"]["parameters"]
            
            # Execute validation
            result = self.agent_executor.run(
                action=action,
                parameters=parameters,
                strategy_state=state
            )
            
            return {
                "content": result["explanation"],
                "validation_result": result["validation_result"],
                "valid": result["valid"]
            }
        else:
            # Handle free-form validation requests
            result = self.agent_executor.run(
                input=message["content"],
                strategy_state=state
            )
            
            return {
                "content": result["explanation"],
                "validation_result": result.get("validation_result", {}),
                "valid": result.get("valid", False)
            }
    
    def validate_parameter(self, indicator, parameter, value):
        # Implementation of parameter validation logic
        # Queries Neo4j for parameter constraints
        pass
    
    def validate_completeness(self, strategy):
        # Implementation of strategy completeness validation
        # Ensures all required components are present
        pass
```

### Data and Feature Agent

**Purpose**: Retrieve market data and calculate technical indicators for backtesting and analysis.

**Implementation**:
- **Pattern**: Tool-using Agent with Parallel Processing
- **Integration**: InfluxDB for time-series data
- **Responsibilities**:
  - Retrieve historical market data
  - Calculate technical indicators
  - Optimize computations with parallel processing
  - Prepare feature matrices for backtesting

**Code Structure**:
```python
class DataFeatureAgent:
    def __init__(self):
        self.llm = Claude("claude-3-7-sonnet-20250219")
        self.influxdb_client = get_influxdb_client()
        
        # Tools for data retrieval and processing
        self.tools = [
            Tool(
                name="get_historical_data",
                func=self.get_historical_data,
                description="Retrieves historical OHLCV data for an instrument"
            ),
            Tool(
                name="calculate_indicator",
                func=self.calculate_indicator,
                description="Calculates a technical indicator with given parameters"
            ),
            Tool(
                name="prepare_feature_matrix",
                func=self.prepare_feature_matrix,
                description="Prepares a feature matrix for backtesting"
            )
        ]
        
        # Create agent
        self.agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self.tools
        )
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=self.agent,
            tools=self.tools,
            verbose=True
        )
    
    def process(self, message, state):
        # Execute data/feature request
        result = self.agent_executor.run(
            input=message["content"],
            strategy_state=state
        )
        
        return {
            "content": "Data processing complete",
            "data_result": result
        }
    
    def get_historical_data(self, instrument, frequency, start_date, end_date):
        # Implementation of historical data retrieval from InfluxDB
        query = f'''
            from(bucket:"market_data")
            |> range(start: {start_date}, stop: {end_date})
            |> filter(fn: (r) => r._measurement == "{instrument}" and r.frequency == "{frequency}")
        '''
        result = self.influxdb_client.query_api().query(query=query)
        # Process and return data
        pass
    
    def calculate_indicator(self, indicator, parameters, data):
        # Implementation of indicator calculation
        if indicator == "RSI":
            period = parameters.get("period", 14)
            return self._calculate_rsi(data, period)
        # Handle other indicators
        pass
    
    def prepare_feature_matrix(self, indicators, data):
        # Implementation of feature matrix preparation
        # Uses multiprocessing for parallel computation
        with multiprocessing.Pool() as pool:
            results = pool.map(self._calculate_feature, indicators)
        # Combine results into a single feature matrix
        pass
```

### Code Agent

**Purpose**: Generate and execute strategy code based on user-defined parameters.

**Implementation**:
- **Pattern**: Code Generation Chain with Structured Output
- **Sandbox Integration**: Secure execution environment
- **Responsibilities**:
  - Generate executable Python code for strategies
  - Optimize code for performance
  - Execute code in secure sandbox
  - Provide debugging and error handling

**Code Structure**:
```python
class CodeAgent:
    def __init__(self):
        self.llm = Claude("claude-3-7-sonnet-20250219")
        
        # Code generation chain
        self.code_generation_chain = LLMChain(
            llm=self.llm,
            prompt=self.load_prompt("code_generation_prompt.txt"),
            output_parser=StructuredOutputParser.from_response_schemas(
                [ResponseSchema(name="code", description="Generated Python code")]
            )
        )
        
        # Code optimization chain
        self.code_optimization_chain = LLMChain(
            llm=self.llm,
            prompt=self.load_prompt("code_optimization_prompt.txt")
        )
        
        # Sandbox for code execution
        self.sandbox = CodeSandbox()
    
    def process(self, message, state):
        # Generate strategy code
        if message.get("action") == "generate_code":
            strategy = state.get("strategy", {})
            
            # Generate code
            result = self.code_generation_chain.run(
                strategy_type=strategy.get("strategy_type", ""),
                indicators=strategy.get("indicators", []),
                conditions=strategy.get("conditions", []),
                position_sizing=strategy.get("position_sizing", {}),
                risk_management=strategy.get("risk_management", {})
            )
            
            # Optimize code
            optimized_code = self.code_optimization_chain.run(
                original_code=result["code"]
            )
            
            return {
                "content": "Code generated successfully",
                "code": optimized_code
            }
        
        # Execute code
        elif message.get("action") == "execute_code":
            code = message.get("code", "")
            data = message.get("data", {})
            
            # Execute in sandbox
            try:
                result = self.sandbox.execute(code, data)
                return {
                    "content": "Code executed successfully",
                    "execution_result": result
                }
            except Exception as e:
                return {
                    "content": f"Error executing code: {str(e)}",
                    "error": str(e)
                }
```

### Feedback Agent

**Purpose**: Analyze backtest results and provide improvement suggestions.

**Implementation**:
- **Pattern**: Sequential Chain with StructuredOutput
- **Integration**: Performance analytics
- **Responsibilities**:
  - Analyze backtest performance
  - Identify strategy weaknesses
  - Suggest parameter improvements
  - Provide natural language explanations

**Code Structure**:
```python
class FeedbackAgent:
    def __init__(self):
        self.llm = Claude("claude-3-7-sonnet-20250219")
        
        # Analysis chain
        self.analysis_chain = LLMChain(
            llm=self.llm,
            prompt=self.load_prompt("performance_analysis_prompt.txt")
        )
        
        # Improvement suggestion chain
        self.suggestion_chain = LLMChain(
            llm=self.llm,
            prompt=self.load_prompt("improvement_suggestion_prompt.txt")
        )
    
    def process(self, message, state):
        # Analyze backtest results
        if message.get("action") == "analyze_backtest":
            backtest_results = message.get("backtest_results", {})
            strategy = state.get("strategy", {})
            
            # Analyze performance
            analysis = self.analysis_chain.run(
                performance=backtest_results.get("performance", {}),
                trades=backtest_results.get("trades", []),
                strategy=strategy
            )
            
            # Generate improvement suggestions
            suggestions = self.suggestion_chain.run(
                analysis=analysis,
                strategy=strategy
            )
            
            return {
                "content": f"Analysis: {analysis}\n\nSuggestions: {suggestions}",
                "analysis": analysis,
                "suggestions": suggestions
            }
```

## Implementation Guidelines

### Agent Integration

1. **Agent Creation**:
   - Implement each agent as a separate class
   - Use inheritance from a base Agent class for common functionality
   - Initialize all agents with appropriate LLM and tools

2. **Message Passing**:
   - Use the standardized message format for all inter-agent communication
   - Include message ID and timestamps for tracking
   - Maintain conversation context across messages

3. **State Management**:
   - Store conversation state in a shared context object
   - Pass relevant state to agents during processing
   - Update state with extracted information after processing

4. **Error Handling**:
   - Implement graceful error recovery for agent failures
   - Log all errors with context for debugging
   - Provide user-friendly error messages

### Prompt Engineering

1. **Specialized Prompts**:
   - Create distinct prompts for each agent and task
   - Include examples and constraints in prompts
   - Use structured output formats where appropriate

2. **Chain of Thought**:
   - Encourage step-by-step reasoning in prompts
   - Include validation steps in the reasoning process
   - Use ReAct patterns for complex decision-making

3. **Context Management**:
   - Include relevant context from previous interactions
   - Summarize long conversations to avoid token limits
   - Focus prompts on specific tasks to avoid confusion

### Security Considerations

1. **Input Validation**:
   - Validate all user inputs before processing
   - Sanitize inputs to prevent injection attacks
   - Use structured parsing to enforce constraints

2. **Code Execution**:
   - Run generated code in an isolated sandbox
   - Limit resource usage and execution time
   - Validate outputs before returning to users

3. **Data Access**:
   - Implement access controls for sensitive data
   - Verify user permissions before data operations
   - Log all data access for audit purposes

## Testing Approach

1. **Unit Testing**:
   - Test each agent in isolation with mock dependencies
   - Verify correct handling of various input types
   - Check error handling and edge cases

2. **Integration Testing**:
   - Test interaction between pairs of agents
   - Verify correct message passing and state updates
   - Test complete workflows with multiple agents

3. **LLM-Specific Testing**:
   - Test prompts with various inputs to ensure robustness
   - Verify structured output parsing works correctly
   - Test with different LLM versions for compatibility

By following this architecture, the Trading Strategy System can provide a coherent, intelligent experience for users while maintaining modularity and scalability.