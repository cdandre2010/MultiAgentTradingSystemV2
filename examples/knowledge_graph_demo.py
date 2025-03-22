"""
Example script demonstrating the knowledge graph integration with agents and visualizations.

This script shows:
1. How the ConversationalAgent uses the Neo4j knowledge graph to enhance strategy creation
2. How to generate visualizations of the knowledge graph for better understanding
"""

import sys
import os
import logging
from pprint import pprint
from pathlib import Path
import matplotlib.pyplot as plt

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import required modules
from src.agents.conversational_agent import ConversationalAgent
from src.database.strategy_repository import get_strategy_repository
from src.agents.knowledge_integration import (
    get_knowledge_recommendations,
    enhance_strategy_with_knowledge
)
# Import visualization modules
from src.utils.visualization import (
    KnowledgeGraphVisualizer,
    create_component_relationship_diagram,
    create_compatibility_matrix,
    create_strategy_template_visualization
)


def save_visualization(fig, filename):
    """Save a matplotlib figure to a file."""
    try:
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / filename
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Saved visualization to {output_path}")
        return str(output_path)
    except Exception as e:
        logger.error(f"Error saving visualization: {e}")
        return None


def run_knowledge_integration_demo(repo):
    """Run the knowledge integration part of the demo."""
    # Create the conversational agent
    logger.info("Creating ConversationalAgent...")
    agent = ConversationalAgent()
    
    # 1. Get knowledge recommendations for different strategy types
    strategy_types = ["momentum", "mean_reversion", "trend_following"]
    
    logger.info("\n=== Knowledge-Driven Recommendations ===")
    for strategy_type in strategy_types:
        logger.info(f"\nRecommendations for {strategy_type} strategy:")
        recommendations = get_knowledge_recommendations(repo, strategy_type)
        print(f"- Recommended indicators: {recommendations['indicators']}")
        print(f"- Recommended position sizing: {recommendations['position_sizing']}")
        print(f"- Recommended risk management: {recommendations['risk_management']}")
        print(f"- Explanation: {recommendations['explanation']}")
    
    # 2. Enhance strategy parameters with knowledge
    logger.info("\n=== Strategy Parameter Enhancement ===")
    
    # Basic strategy parameters
    basic_params = {
        "strategy_type": "momentum",
        "parameters": {
            "lookback_period": 14,
            "threshold": 0.05
        }
    }
    
    logger.info("Basic strategy parameters:")
    pprint(basic_params)
    
    # Enhance parameters with knowledge
    logger.info("\nEnhanced strategy parameters:")
    enhanced_params = enhance_strategy_with_knowledge(repo, basic_params)
    pprint(enhanced_params)
    
    # 3. Process a user message with knowledge-driven recommendations
    logger.info("\n=== ConversationalAgent with Knowledge Graph ===")
    
    # Create a test message
    message = {
        "sender": "user",
        "message_type": "request",
        "content": {
            "text": "I want to create a momentum strategy for BTC/USDT with RSI"
        },
        "context": {
            "session_id": "demo-session",
            "extract_params": True,
            "use_knowledge_graph": True
        }
    }
    
    # Process the message
    logger.info("Processing user message...")
    response = agent.process_message(message)
    
    # Print the response
    logger.info("\nAgent response:")
    if "knowledge_recommendations" in response["content"]:
        logger.info("Knowledge-driven recommendations were provided!")
        recommendations = response["content"]["knowledge_recommendations"]
        print(f"- Recommended indicators: {recommendations['indicators']}")
        print(f"- Recommended position sizing: {recommendations['position_sizing']}")
        print(f"- Recommended risk management: {recommendations['risk_management']}")
    else:
        logger.info("No knowledge-driven recommendations (Neo4j might be unavailable).")


def run_visualization_demo(repo):
    """Run the visualization part of the demo."""
    logger.info("\n=== Knowledge Graph Visualizations ===")
    
    # Create a visualizer instance
    visualizer = KnowledgeGraphVisualizer(repo)
    
    # 1. Component Relationship Diagram for Momentum Strategy
    logger.info("\nGenerating component relationship diagram for momentum strategy...")
    fig1, _ = visualizer.create_component_relationship_diagram(
        strategy_type="momentum",
        depth=2,
        min_strength=0.6,
        max_nodes=15
    )
    save_visualization(fig1, "momentum_relationships.png")
    
    # 2. Compatibility Matrix for Indicators
    logger.info("\nGenerating compatibility matrix for indicators...")
    fig2, _ = visualizer.create_compatibility_matrix(
        component_type="Indicator",
        strategy_type=None,
        top_n=6
    )
    save_visualization(fig2, "indicator_compatibility.png")
    
    # 3. Strategy Template Visualization for Momentum
    logger.info("\nGenerating strategy template visualization for momentum strategy...")
    fig3, _ = visualizer.create_strategy_template_visualization(
        strategy_type="momentum",
        instrument="BTCUSDT",
        timeframe="1h"
    )
    save_visualization(fig3, "momentum_strategy_template.png")


def main():
    """Run the knowledge graph integration and visualization demo."""
    show_interactive = "--show" in sys.argv
    visualization_only = "--viz-only" in sys.argv
    
    # Get the strategy repository
    logger.info("Getting StrategyRepository...")
    try:
        repo = get_strategy_repository()
        logger.info("Successfully connected to repository")
    except Exception as e:
        logger.error(f"Error connecting to Neo4j: {e}")
        logger.info("Using mock data for visualizations")
        repo = None
    
    # Run the appropriate demos
    if not visualization_only:
        run_knowledge_integration_demo(repo)
    
    run_visualization_demo(repo)
    
    if show_interactive:
        # Create a visualizer instance for interactive display
        visualizer = KnowledgeGraphVisualizer(repo)
        
        # Display component relationship diagram
        logger.info("\nDisplaying component relationship diagram for momentum strategy...")
        fig, _ = visualizer.create_component_relationship_diagram(
            strategy_type="momentum",
            depth=2,
            min_strength=0.6,
            max_nodes=15
        )
        plt.show()
    
    logger.info("\nDemo completed successfully!")
    
    if not show_interactive:
        logger.info("\nTip: Run with '--show' to display interactive visualizations")
        logger.info("Tip: Run with '--viz-only' to only run the visualization part")
        logger.info("Check the 'examples/output' directory for saved visualizations")


if __name__ == "__main__":
    main()