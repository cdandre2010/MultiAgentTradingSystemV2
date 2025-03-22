# Knowledge Graph Visualization

This document describes the visualization tools developed for the Neo4j knowledge graph in the Multi-Agent Trading System V2.

## Overview

The knowledge graph visualization module provides tools for generating intuitive visual representations of the trading strategy knowledge stored in Neo4j. These visualizations help users understand component relationships, compatibility scores, and strategy structures.

## Visualization Types

### 1. Component Relationship Diagrams

Component relationship diagrams show how different trading strategy components are connected to each other.

**Features:**
- Interactive network graph visualization
- Color-coded nodes by component type (indicators, position sizing, risk management, etc.)
- Relationship edges with type labels and strength scores
- Customizable depth and strength filtering
- Automatic layout optimization for readability

**Usage Examples:**
- Understanding which indicators work well with a specific strategy type
- Exploring parameter requirements for indicators
- Visualizing the ecosystem of components around a strategy type

### 2. Compatibility Matrices

Compatibility matrices provide a heatmap visualization of how well different components work together.

**Features:**
- Color gradient representing compatibility scores
- Numerical annotations for precise score inspection
- Filtering by strategy type and component category
- Interactive tooltips with relationship explanations
- Customizable component selection

**Usage Examples:**
- Finding the most compatible indicator combinations
- Identifying potential conflicts between components
- Optimizing strategy component selection

### 3. Strategy Template Visualizations

Strategy template visualizations provide a hierarchical view of complete strategy templates.

**Features:**
- Tree-like hierarchical structure
- Category-based organization (indicators, entry/exit conditions, position sizing, etc.)
- Parameter display for each component
- Color-coded nodes by component type
- Comprehensive overview of strategy design

**Usage Examples:**
- Visualizing complete strategy templates
- Understanding component organization within strategies
- Comparing different strategy structures

## Technical Implementation

The visualization module is implemented in the `src/utils/visualization.py` file and consists of:

1. **KnowledgeGraphVisualizer Class:**
   - Main class for generating all visualization types
   - Handles Neo4j data retrieval via the StrategyRepository
   - Supports both interactive and static visualization generation
   - Provides graceful fallback to mock data when Neo4j is unavailable

2. **Utility Functions:**
   - `create_component_relationship_diagram()`: Simplified function for generating relationship diagrams
   - `create_compatibility_matrix()`: Simplified function for generating compatibility matrices
   - `create_strategy_template_visualization()`: Simplified function for generating template visualizations

3. **Integration with StrategyRepository:**
   - `get_component_relationships()`: Fetches relationship data from Neo4j
   - `get_compatibility_matrix()`: Fetches compatibility data for matrices
   - `get_strategy_type_visualization_data()`: Fetches comprehensive visualization data

## Usage in Agent System

The visualization tools enhance the agent system in several ways:

1. **ConversationalAgent Integration:**
   - Embeds relationship diagrams in strategy explanations
   - Uses compatibility matrices to justify recommendations
   - Provides visual strategy templates to guide users

2. **ValidationAgent Integration:**
   - Visualizes component compatibility during validation
   - Highlights incompatible components in relationship diagrams
   - Shows alternative options in compatibility matrices

3. **Frontend Integration:**
   - Embeds visualizations in web UI
   - Provides interactive exploration of the knowledge graph
   - Enhances strategy creation workflow with visual guidance

## Example Code

```python
# Creating a component relationship diagram
from src.utils.visualization import KnowledgeGraphVisualizer
from src.database.strategy_repository import get_strategy_repository

# Get repository and create visualizer
repo = get_strategy_repository()
visualizer = KnowledgeGraphVisualizer(repo)

# Generate a component relationship diagram
fig, img_data = visualizer.create_component_relationship_diagram(
    strategy_type="momentum",
    depth=2,
    min_strength=0.6,
    max_nodes=15
)

# Display or save the visualization
import matplotlib.pyplot as plt
plt.show()  # For interactive display

# Save to file
fig.savefig("momentum_relationships.png", dpi=300, bbox_inches='tight')

# Or get base64 data for embedding in HTML/frontend
# The img_data variable contains the base64 encoded image
html_embed = f'<img src="data:image/png;base64,{img_data}" alt="Component Relationships">'
```

## Future Enhancements

Planned enhancements for the visualization module include:

1. **Interactive Web Visualizations:**
   - Convert static visualizations to interactive D3.js or Plotly.js
   - Allow users to explore the knowledge graph in the browser
   - Implement zoom, pan, and filtering capabilities

2. **Real-time Knowledge Graph Updates:**
   - Visualize changes to the knowledge graph as they happen
   - Show how compatibility scores evolve based on user feedback
   - Implement animated transitions between states

3. **3D Visualizations:**
   - Develop 3D visualizations for complex relationship structures
   - Implement VR/AR compatible knowledge graph exploration
   - Create immersive data exploration experiences

4. **Comparative Visualizations:**
   - Side-by-side comparison of different strategy types
   - Before/after visualizations for strategy optimization
   - Multi-strategy compatibility analysis

## Related Documentation

- [Neo4j Setup Guide](./database_schema.md#neo4j-graph-database): Detailed Neo4j setup instructions
- [Strategy Repository](./database_schema.md#knowledge-graph-integration-with-agents): Repository for Neo4j operations
- [Knowledge Integration](./knowledge_graph_integration.md): Knowledge integration module documentation