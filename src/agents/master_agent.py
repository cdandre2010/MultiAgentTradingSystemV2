from typing import Dict, Any, Optional, List
from .base import Agent
from langchain_anthropic import ChatAnthropic
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from .data_feature_agent import DataFeatureAgent

class MasterAgent(Agent):
    """
    Master Agent that orchestrates the overall workflow and coordinates
    communication between specialized agents.
    
    Responsibilities:
    - Route user messages to appropriate specialized agents
    - Maintain conversation state and history
    - Coordinate the strategy creation workflow
    - Handle error recovery and fallbacks
    - Track progress through strategy creation steps
    """
    
    def __init__(self):
        """Initialize the Master Agent with specialized agents and LLM."""
        super().__init__(name="master_agent")
        
        # Initialize LLM (will be used for routing decisions)
        # For testing we'll use a dummy setup, in production we'd use actual Claude
        self.llm = ChatAnthropic(model_name="claude-3-7-sonnet-20250219")
        
        # Initialize state
        self.conversation_state = {}
        
        # Initialize specialized agents
        # For testing, we'll conditionally initialize to avoid DB connections in tests
        try:
            # Try to initialize DataFeatureAgent
            from ..database.influxdb import InfluxDBClient
            from ..services.indicators import IndicatorService
            from ..services.data_availability import DataAvailabilityService
            from ..services.data_retrieval import DataRetrievalService
            
            # Create services with shared dependencies
            influxdb_client = InfluxDBClient()
            indicator_service = IndicatorService()
            data_availability_service = DataAvailabilityService(influxdb_client=influxdb_client)
            data_retrieval_service = DataRetrievalService(
                influxdb_client=influxdb_client,
                indicator_service=indicator_service
            )
            
            # Initialize DataFeatureAgent with shared services
            data_agent = DataFeatureAgent(
                indicator_service=indicator_service,
                data_availability_service=data_availability_service,
                data_retrieval_service=data_retrieval_service
            )
        except Exception as e:
            # If initialization fails, use None for testing
            data_agent = None
            
        # Set up agent dictionary
        self.specialized_agents = {
            "conversation": None,  # ConversationalAgent(),
            "validation": None,    # ValidationAgent(),
            "data": data_agent,    # DataFeatureAgent
            "code": None,          # CodeAgent(),
            "feedback": None,      # FeedbackAgent()
        }
        
        # Initialize router chain
        self.router_prompt = PromptTemplate.from_template(
            """
            You are the Master Agent in a trading strategy system. Your job is to determine
            which specialized agent should handle the incoming message.
            
            Available agents:
            - conversation: For natural language interaction, explaining concepts, guiding users
            - validation: For checking if parameters and strategy components are valid
            - data: For retrieving market data, calculating indicators, checking data availability, and creating visualizations
            - code: For generating strategy code
            - feedback: For analyzing backtest results and providing improvement suggestions
            
            Current conversation state:
            {conversation_state}
            
            User message:
            {message}
            
            Which agent should handle this message? Respond with just the agent name.
            """
        )
        
        self.router_chain = LLMChain(llm=self.llm, prompt=self.router_prompt)
    
    def route_message(self, message: str, state: Dict[str, Any]) -> str:
        """
        Determine which agent should process the message.
        
        Args:
            message: The user's message
            state: Current conversation state
            
        Returns:
            Name of the agent that should handle the message
        """
        # Use keyword-based routing for now
        # In production, this would use the LLM for more sophisticated routing
        
        # Data/Feature Agent keywords
        data_keywords = [
            "market data", "price data", "historical data", "ohlcv", 
            "indicator", "indicators", "technical analysis", "calculate", "visualization",
            "chart", "graph", "plot", "data availability", "backtest data"
        ]
        
        # Check for data-related keywords
        message_lower = message.lower()
        if any(keyword in message_lower for keyword in data_keywords):
            return "data"
            
        # Add other agent keywords and routing in the future
        
        # Default to conversation agent
        return "conversation"
        
        # Production implementation would look like:
        # result = self.router_chain.run(
        #     message=message,
        #     conversation_state=str(state)
        # )
        # return result.strip().lower()
    
    def update_state(self, message: Dict[str, Any]) -> None:
        """
        Update the conversation state with information from a message.
        
        Args:
            message: Message containing information to update state
        """
        if "extracted_info" in message:
            for key, value in message["extracted_info"].items():
                self.conversation_state[key] = value
                
        if "current_step" in message:
            self.conversation_state["current_step"] = message["current_step"]
    
    def process(self, message: Dict[str, Any], state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process an incoming message by routing it to the appropriate agent.
        
        Args:
            message: The message to process
            state: External state (if provided, will override internal state)
            
        Returns:
            Response message from the appropriate agent
        """
        # Use provided state or fall back to internal state
        current_state = state if state is not None else self.conversation_state
        
        # Log incoming message
        self.log_message(message)
        
        # Update state with message
        self.update_state(message)
        
        # Determine which agent should handle this message
        if "content" in message:
            # Ensure content is in the expected format
            content_text = message["content"]
            if isinstance(content_text, str):
                # Convert string content to dict for the conversation agent
                message["content"] = {"text": content_text}
            
            destination = self.route_message(
                content_text if isinstance(content_text, str) else str(content_text), 
                current_state
            )
        else:
            # Default to conversation agent if no content
            destination = "conversation"
        
        # Check if agent exists
        if destination not in self.specialized_agents or self.specialized_agents[destination] is None:
            # Agent not available - create error response
            agent_name = "Data/Feature Agent" if destination == "data" else f"'{destination}' agent"
            response = self.create_message(
                recipient=message["sender"],
                message_type="error",
                content={
                    "error": f"{agent_name} not available",
                    "message": "The system is still being initialized. Try again later."
                },
                context=message.get("context", {})
            )
        else:
            # Forward to appropriate agent
            agent = self.specialized_agents[destination]
            response = agent.process(message, current_state)
            
            # Update state with response
            self.update_state(response)
        
        # Log outgoing message
        self.log_message(response, direction="sent")
        
        return response