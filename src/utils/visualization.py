"""
Knowledge Graph Visualization Module

This module provides tools for visualizing the Neo4j knowledge graph 
used in the Trading Strategy System. It includes functions for generating
component relationship diagrams, compatibility score visualizations,
and strategy template visualizations.
"""

import json
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Tuple
import io
import base64

logger = logging.getLogger(__name__)

class KnowledgeGraphVisualizer:
    """
    Visualizes the Neo4j knowledge graph for trading strategy components.
    Supports various visualization types including relationship diagrams,
    compatibility matrices, and strategy component hierarchies.
    """
    
    def __init__(self, strategy_repository=None):
        """
        Initialize the visualizer with a strategy repository.
        
        Args:
            strategy_repository: Neo4j strategy repository instance
        """
        self.strategy_repository = strategy_repository
        self.node_colors = {
            "StrategyType": "#86CEFA",    # Light blue
            "Indicator": "#90EE90",       # Light green
            "Instrument": "#FFA07A",      # Light salmon
            "Frequency": "#E6E6FA",       # Lavender
            "Parameter": "#FFE4B5",       # Moccasin
            "Condition": "#D8BFD8",       # Thistle
            "PositionSizing": "#F0E68C",  # Khaki
            "RiskManagement": "#F08080",  # Light coral
            "BacktestingMethod": "#98FB98" # Pale green
        }
    
    def create_component_relationship_diagram(
        self, 
        strategy_type: str, 
        depth: int = 2,
        min_strength: float = 0.6,
        max_nodes: int = 15
    ) -> Tuple[plt.Figure, str]:
        """
        Generate a diagram showing relationships between components for a strategy type.
        
        Args:
            strategy_type: Type of trading strategy
            depth: Relationship depth to traverse
            min_strength: Minimum relationship strength to include
            max_nodes: Maximum number of nodes to display
            
        Returns:
            Tuple of Figure object and base64 encoded image
        """
        try:
            # Get relationship data from Neo4j
            relationships = self._fetch_component_relationships(
                strategy_type, depth, min_strength, max_nodes
            )
            
            # Create NetworkX graph
            G = nx.Graph()
            
            # Add center node (strategy type)
            G.add_node(strategy_type, node_type="StrategyType")
            
            # Add related nodes and edges
            for rel in relationships:
                source = rel["source"]
                target = rel["target"]
                rel_type = rel["relationship"]
                strength = rel.get("strength", 0.5)
                source_type = rel["source_type"]
                target_type = rel["target_type"]
                
                # Add nodes
                if source not in G:
                    G.add_node(source, node_type=source_type)
                if target not in G:
                    G.add_node(target, node_type=target_type)
                
                # Add edge with strength as weight
                G.add_edge(source, target, 
                          relationship=rel_type, 
                          weight=strength,
                          label=f"{rel_type} ({strength:.2f})")
            
            # Create visualization
            fig, ax = plt.subplots(figsize=(12, 10))
            
            # Define node colors based on type
            node_colors = [self.node_colors.get(G.nodes[n]["node_type"], "#CCCCCC") for n in G.nodes]
            
            # Define edge widths based on strength
            edge_widths = [G[u][v].get("weight", 1) * 2 for u, v in G.edges]
            
            # Define layout
            pos = nx.spring_layout(G, k=0.3, iterations=50)
            
            # Draw graph
            nx.draw_networkx_nodes(G, pos, node_size=1000, node_color=node_colors, alpha=0.8, ax=ax)
            nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.6, edge_color="gray", ax=ax)
            nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold", ax=ax)
            
            # Add edge labels (relationship types)
            edge_labels = {(u, v): G[u][v]["relationship"] for u, v in G.edges}
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, ax=ax)
            
            # Add legend for node types
            legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                              label=node_type, markerfacecolor=color, markersize=10)
                              for node_type, color in self.node_colors.items() 
                              if any(G.nodes[n].get("node_type") == node_type for n in G.nodes)]
            
            ax.legend(handles=legend_elements, loc='upper left', title="Component Types")
            
            # Set title and remove axis
            ax.set_title(f"Component Relationships for {strategy_type.title()} Strategy", fontsize=14)
            ax.axis('off')
            
            # Convert to base64 for easy embedding
            img_data = self._fig_to_base64(fig)
            
            return fig, img_data
            
        except Exception as e:
            logger.error(f"Error creating component relationship diagram: {str(e)}")
            # Return a simple error diagram
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, f"Error generating visualization:\n{str(e)}", 
                    ha='center', va='center', fontsize=12)
            ax.axis('off')
            img_data = self._fig_to_base64(fig)
            return fig, img_data
    
    def create_compatibility_matrix(
        self, 
        component_type: str,
        strategy_type: Optional[str] = None,
        top_n: int = 10
    ) -> Tuple[plt.Figure, str]:
        """
        Generate a compatibility matrix showing how different components work together.
        
        Args:
            component_type: Type of component (e.g., "Indicator", "PositionSizing")
            strategy_type: Optional strategy type to filter by
            top_n: Number of components to include
            
        Returns:
            Tuple of Figure object and base64 encoded image
        """
        try:
            # Fetch compatibility data from Neo4j
            compatibility_data = self._fetch_compatibility_data(
                component_type, strategy_type, top_n
            )
            
            # Convert to DataFrame for easier visualization
            df = pd.DataFrame(compatibility_data)
            
            # If empty, return an information message
            if df.empty:
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.text(0.5, 0.5, f"No compatibility data found for {component_type}", 
                        ha='center', va='center', fontsize=12)
                ax.axis('off')
                img_data = self._fig_to_base64(fig)
                return fig, img_data
            
            # Create pivot table
            pivot = df.pivot(index="source", columns="target", values="compatibility")
            
            # Fill NaN values with 0
            pivot = pivot.fillna(0)
            
            # Create heatmap
            fig, ax = plt.subplots(figsize=(12, 10))
            cmap = plt.cm.YlGnBu
            im = ax.imshow(pivot.values, cmap=cmap)
            
            # Add colorbar
            cbar = ax.figure.colorbar(im, ax=ax)
            cbar.ax.set_ylabel("Compatibility Score", rotation=-90, va="bottom")
            
            # Set ticks and labels
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_yticks(range(len(pivot.index)))
            ax.set_xticklabels(pivot.columns, rotation=45, ha="right")
            ax.set_yticklabels(pivot.index)
            
            # Add title
            title = f"Compatibility Matrix for {component_type}"
            if strategy_type:
                title += f" in {strategy_type.title()} Strategies"
            ax.set_title(title)
            
            # Add text annotations
            for i in range(len(pivot.index)):
                for j in range(len(pivot.columns)):
                    if pivot.values[i, j] > 0:
                        text = ax.text(j, i, f"{pivot.values[i, j]:.2f}",
                                      ha="center", va="center", 
                                      color="white" if pivot.values[i, j] > 0.5 else "black")
            
            fig.tight_layout()
            
            # Convert to base64
            img_data = self._fig_to_base64(fig)
            
            return fig, img_data
            
        except Exception as e:
            logger.error(f"Error creating compatibility matrix: {str(e)}")
            # Return a simple error diagram
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, f"Error generating compatibility matrix:\n{str(e)}", 
                    ha='center', va='center', fontsize=12)
            ax.axis('off')
            img_data = self._fig_to_base64(fig)
            return fig, img_data
    
    def create_strategy_template_visualization(
        self, 
        strategy_type: str,
        instrument: Optional[str] = None,
        timeframe: Optional[str] = None
    ) -> Tuple[plt.Figure, str]:
        """
        Generate a visualization of a strategy template based on the knowledge graph.
        
        Args:
            strategy_type: Type of trading strategy
            instrument: Optional instrument symbol
            timeframe: Optional timeframe
            
        Returns:
            Tuple of Figure object and base64 encoded image
        """
        try:
            # Get strategy template from repository
            if self.strategy_repository:
                template = self.strategy_repository.generate_strategy_template(
                    strategy_type, instrument, timeframe
                )
            else:
                # Mock data if repository not available
                template = self._mock_strategy_template(strategy_type)
            
            # Create a hierarchical graph
            G = nx.DiGraph()
            
            # Add main strategy node
            strategy_name = f"{strategy_type.title()} Strategy"
            if instrument:
                strategy_name += f" for {instrument}"
            if timeframe:
                strategy_name += f" ({timeframe})"
            
            G.add_node(strategy_name, node_type="Strategy")
            
            # Add category nodes
            categories = [
                "Indicators", "Entry Conditions", "Exit Conditions",
                "Position Sizing", "Risk Management", "Backtesting"
            ]
            
            for category in categories:
                G.add_node(category, node_type="Category")
                G.add_edge(strategy_name, category)
                
                # Add components for each category
                if category == "Indicators" and "indicators" in template:
                    for indicator in template["indicators"]:
                        node_name = f"{indicator['name']}"
                        if "parameters" in indicator:
                            params = ", ".join([f"{k}={v}" for k, v in indicator["parameters"].items()])
                            node_name += f" ({params})"
                        G.add_node(node_name, node_type="Indicator")
                        G.add_edge(category, node_name)
                
                elif category == "Entry Conditions" and "entry_conditions" in template:
                    for condition in template["entry_conditions"]:
                        G.add_node(condition, node_type="Condition")
                        G.add_edge(category, condition)
                
                elif category == "Exit Conditions" and "exit_conditions" in template:
                    for condition in template["exit_conditions"]:
                        G.add_node(condition, node_type="Condition")
                        G.add_edge(category, condition)
                
                elif category == "Position Sizing" and "position_sizing" in template:
                    pos_sizing = template["position_sizing"]
                    node_name = f"{pos_sizing['method']}"
                    if "parameters" in pos_sizing:
                        params = ", ".join([f"{k}={v}" for k, v in pos_sizing["parameters"].items()])
                        node_name += f" ({params})"
                    G.add_node(node_name, node_type="PositionSizing")
                    G.add_edge(category, node_name)
                
                elif category == "Risk Management" and "risk_management" in template:
                    risk_mgmt = template["risk_management"]
                    for method, params in risk_mgmt.items():
                        if isinstance(params, dict):
                            param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
                            node_name = f"{method} ({param_str})"
                        else:
                            node_name = f"{method}: {params}"
                        G.add_node(node_name, node_type="RiskManagement")
                        G.add_edge(category, node_name)
                
                elif category == "Backtesting" and "backtesting" in template:
                    bt = template["backtesting"]
                    node_name = f"{bt['method']}"
                    if "parameters" in bt:
                        params = ", ".join([f"{k}={v}" for k, v in bt["parameters"].items()])
                        node_name += f" ({params})"
                    G.add_node(node_name, node_type="BacktestingMethod")
                    G.add_edge(category, node_name)
            
            # Create visualization
            fig, ax = plt.subplots(figsize=(14, 10))
            
            # Define node colors based on type
            node_colors = [self.node_colors.get(G.nodes[n].get("node_type", ""), "#CCCCCC") for n in G.nodes]
            
            # Define layout (hierarchical)
            pos = nx.nx_agraph.graphviz_layout(G, prog="dot")
            
            # Draw graph
            nx.draw_networkx_nodes(G, pos, node_size=2000, node_color=node_colors, alpha=0.8, ax=ax)
            nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.6, edge_color="gray", arrows=True, ax=ax)
            nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold", ax=ax)
            
            # Add title and remove axis
            ax.set_title(f"Strategy Template: {strategy_name}", fontsize=14)
            ax.axis('off')
            
            # Add legend for node types
            legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                              label=node_type, markerfacecolor=color, markersize=10)
                              for node_type, color in self.node_colors.items() 
                              if any(G.nodes[n].get("node_type") == node_type for n in G.nodes)]
            
            ax.legend(handles=legend_elements, loc='upper right', title="Component Types")
            
            fig.tight_layout()
            
            # Convert to base64
            img_data = self._fig_to_base64(fig)
            
            return fig, img_data
            
        except Exception as e:
            logger.error(f"Error creating strategy template visualization: {str(e)}")
            # Return a simple error diagram
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.text(0.5, 0.5, f"Error generating template visualization:\n{str(e)}", 
                    ha='center', va='center', fontsize=12)
            ax.axis('off')
            img_data = self._fig_to_base64(fig)
            return fig, img_data
    
    def _fetch_component_relationships(
        self, 
        strategy_type: str, 
        depth: int = 2,
        min_strength: float = 0.6,
        max_nodes: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Fetch component relationships from Neo4j.
        
        If strategy_repository is not available, returns mock data.
        """
        if self.strategy_repository:
            try:
                # This would be implemented in the repository
                return self.strategy_repository.get_component_relationships(
                    strategy_type, depth, min_strength, max_nodes
                )
            except Exception as e:
                logger.warning(f"Error fetching from Neo4j: {str(e)}. Using mock data.")
                return self._mock_component_relationships(strategy_type)
        else:
            # Return mock data for demonstration purposes
            return self._mock_component_relationships(strategy_type)
    
    def _fetch_compatibility_data(
        self, 
        component_type: str,
        strategy_type: Optional[str] = None,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch compatibility data from Neo4j.
        
        If strategy_repository is not available, returns mock data.
        """
        if self.strategy_repository:
            try:
                # This would be implemented in the repository
                return self.strategy_repository.get_compatibility_matrix(
                    component_type, strategy_type, top_n
                )
            except Exception as e:
                logger.warning(f"Error fetching from Neo4j: {str(e)}. Using mock data.")
                return self._mock_compatibility_data(component_type, strategy_type)
        else:
            # Return mock data for demonstration purposes
            return self._mock_compatibility_data(component_type, strategy_type)
    
    def _mock_component_relationships(self, strategy_type: str) -> List[Dict[str, Any]]:
        """
        Generate mock relationship data for demonstration purposes.
        """
        if strategy_type.lower() == "momentum":
            return [
                {"source": "momentum", "target": "RSI", "relationship": "COMMONLY_USES", 
                 "strength": 0.85, "source_type": "StrategyType", "target_type": "Indicator"},
                {"source": "momentum", "target": "MACD", "relationship": "COMMONLY_USES", 
                 "strength": 0.75, "source_type": "StrategyType", "target_type": "Indicator"},
                {"source": "momentum", "target": "CCI", "relationship": "COMMONLY_USES", 
                 "strength": 0.65, "source_type": "StrategyType", "target_type": "Indicator"},
                {"source": "momentum", "target": "percent_risk", "relationship": "RECOMMENDS", 
                 "strength": 0.80, "source_type": "StrategyType", "target_type": "PositionSizing"},
                {"source": "momentum", "target": "trailing_stop", "relationship": "RECOMMENDS", 
                 "strength": 0.90, "source_type": "StrategyType", "target_type": "RiskManagement"},
                {"source": "RSI", "target": "period", "relationship": "HAS_PARAMETER", 
                 "strength": 1.0, "source_type": "Indicator", "target_type": "Parameter"},
                {"source": "RSI", "target": "oversold", "relationship": "HAS_PARAMETER", 
                 "strength": 1.0, "source_type": "Indicator", "target_type": "Parameter"},
                {"source": "MACD", "target": "fast_period", "relationship": "HAS_PARAMETER", 
                 "strength": 1.0, "source_type": "Indicator", "target_type": "Parameter"},
                {"source": "MACD", "target": "slow_period", "relationship": "HAS_PARAMETER", 
                 "strength": 1.0, "source_type": "Indicator", "target_type": "Parameter"},
                {"source": "MACD", "target": "signal_period", "relationship": "HAS_PARAMETER", 
                 "strength": 1.0, "source_type": "Indicator", "target_type": "Parameter"},
            ]
        elif strategy_type.lower() == "mean_reversion":
            return [
                {"source": "mean_reversion", "target": "Bollinger_Bands", "relationship": "COMMONLY_USES", 
                 "strength": 0.90, "source_type": "StrategyType", "target_type": "Indicator"},
                {"source": "mean_reversion", "target": "RSI", "relationship": "COMMONLY_USES", 
                 "strength": 0.80, "source_type": "StrategyType", "target_type": "Indicator"},
                {"source": "mean_reversion", "target": "Stochastic", "relationship": "COMMONLY_USES", 
                 "strength": 0.75, "source_type": "StrategyType", "target_type": "Indicator"},
                {"source": "mean_reversion", "target": "fixed_dollar", "relationship": "RECOMMENDS", 
                 "strength": 0.65, "source_type": "StrategyType", "target_type": "PositionSizing"},
                {"source": "mean_reversion", "target": "take_profit", "relationship": "RECOMMENDS", 
                 "strength": 0.85, "source_type": "StrategyType", "target_type": "RiskManagement"},
                {"source": "Bollinger_Bands", "target": "period", "relationship": "HAS_PARAMETER", 
                 "strength": 1.0, "source_type": "Indicator", "target_type": "Parameter"},
                {"source": "Bollinger_Bands", "target": "std_dev", "relationship": "HAS_PARAMETER", 
                 "strength": 1.0, "source_type": "Indicator", "target_type": "Parameter"},
            ]
        else:
            # Generic demo relationships
            return [
                {"source": strategy_type, "target": "Indicator1", "relationship": "COMMONLY_USES", 
                 "strength": 0.80, "source_type": "StrategyType", "target_type": "Indicator"},
                {"source": strategy_type, "target": "Indicator2", "relationship": "COMMONLY_USES", 
                 "strength": 0.70, "source_type": "StrategyType", "target_type": "Indicator"},
                {"source": strategy_type, "target": "PositionSizing1", "relationship": "RECOMMENDS", 
                 "strength": 0.75, "source_type": "StrategyType", "target_type": "PositionSizing"},
                {"source": strategy_type, "target": "RiskMethod1", "relationship": "RECOMMENDS", 
                 "strength": 0.85, "source_type": "StrategyType", "target_type": "RiskManagement"},
                {"source": "Indicator1", "target": "param1", "relationship": "HAS_PARAMETER", 
                 "strength": 1.0, "source_type": "Indicator", "target_type": "Parameter"},
                {"source": "Indicator1", "target": "param2", "relationship": "HAS_PARAMETER", 
                 "strength": 1.0, "source_type": "Indicator", "target_type": "Parameter"},
            ]
    
    def _mock_compatibility_data(
        self, 
        component_type: str,
        strategy_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate mock compatibility data for demonstration purposes.
        """
        if component_type.lower() == "indicator":
            indicators = ["RSI", "MACD", "Bollinger_Bands", "CCI", "ATR", "Stochastic"]
            result = []
            
            for i, source in enumerate(indicators):
                for j, target in enumerate(indicators):
                    if i != j:  # Don't compare indicator to itself
                        # Generate a realistic compatibility score
                        if source == "RSI" and target == "MACD":
                            score = 0.85
                        elif source == "RSI" and target == "Stochastic":
                            score = 0.75
                        elif source == "MACD" and target == "ATR":
                            score = 0.60
                        elif source == "Bollinger_Bands" and target == "RSI":
                            score = 0.90
                        else:
                            # Random score for other combinations
                            import random
                            score = round(random.uniform(0.3, 0.9), 2)
                        
                        result.append({
                            "source": source,
                            "target": target,
                            "compatibility": score
                        })
            
            return result
            
        elif component_type.lower() == "positionsizing":
            methods = ["percent_risk", "fixed_dollar", "volatility_based", "equity_percent", "martingale"]
            result = []
            
            for i, source in enumerate(methods):
                for j, target in enumerate(methods):
                    if i != j:
                        if source == "percent_risk" and target == "equity_percent":
                            score = 0.80
                        elif source == "volatility_based" and target == "percent_risk":
                            score = 0.70
                        elif source == "martingale" and target == "fixed_dollar":
                            score = 0.30  # Intentionally low
                        else:
                            import random
                            score = round(random.uniform(0.2, 0.8), 2)
                        
                        result.append({
                            "source": source,
                            "target": target,
                            "compatibility": score
                        })
            
            return result
            
        else:
            # Generic compatibility data
            items = [f"{component_type}1", f"{component_type}2", f"{component_type}3", 
                    f"{component_type}4", f"{component_type}5"]
            result = []
            
            for i, source in enumerate(items):
                for j, target in enumerate(items):
                    if i != j:
                        import random
                        score = round(random.uniform(0.3, 0.9), 2)
                        
                        result.append({
                            "source": source,
                            "target": target,
                            "compatibility": score
                        })
            
            return result
    
    def _mock_strategy_template(self, strategy_type: str) -> Dict[str, Any]:
        """
        Generate a mock strategy template for demonstration purposes.
        """
        if strategy_type.lower() == "momentum":
            return {
                "strategy_type": "momentum",
                "indicators": [
                    {"name": "RSI", "parameters": {"period": 14, "oversold": 30, "overbought": 70}},
                    {"name": "MACD", "parameters": {"fast_period": 12, "slow_period": 26, "signal_period": 9}}
                ],
                "entry_conditions": [
                    "RSI crosses above 30",
                    "MACD line crosses above signal line"
                ],
                "exit_conditions": [
                    "RSI crosses above 70",
                    "MACD line crosses below signal line",
                    "Trailing stop at 2 ATR"
                ],
                "position_sizing": {
                    "method": "percent_risk",
                    "parameters": {"risk_percent": 1.0}
                },
                "risk_management": {
                    "stop_loss": {"type": "ATR", "multiplier": 2.0},
                    "take_profit": {"type": "risk_multiple", "multiplier": 2.0},
                    "trailing_stop": {"type": "ATR", "multiplier": 2.5}
                },
                "backtesting": {
                    "method": "walk_forward",
                    "parameters": {"in_sample_pct": 70, "out_sample_pct": 30}
                }
            }
        elif strategy_type.lower() == "mean_reversion":
            return {
                "strategy_type": "mean_reversion",
                "indicators": [
                    {"name": "Bollinger_Bands", "parameters": {"period": 20, "std_dev": 2.0}},
                    {"name": "RSI", "parameters": {"period": 14, "oversold": 30, "overbought": 70}}
                ],
                "entry_conditions": [
                    "Price touches lower Bollinger Band",
                    "RSI below 30"
                ],
                "exit_conditions": [
                    "Price touches middle Bollinger Band",
                    "RSI above 50",
                    "Take profit at upper Bollinger Band"
                ],
                "position_sizing": {
                    "method": "fixed_dollar",
                    "parameters": {"position_size": 1000}
                },
                "risk_management": {
                    "stop_loss": {"type": "fixed_percent", "percent": 2.0},
                    "take_profit": {"type": "band_touch", "band": "upper"}
                },
                "backtesting": {
                    "method": "monte_carlo",
                    "parameters": {"iterations": 1000, "confidence_level": 0.95}
                }
            }
        else:
            # Generic template
            return {
                "strategy_type": strategy_type,
                "indicators": [
                    {"name": "Indicator1", "parameters": {"param1": 10, "param2": 20}},
                    {"name": "Indicator2", "parameters": {"param1": 30, "param2": 40}}
                ],
                "entry_conditions": [
                    "Condition 1",
                    "Condition 2"
                ],
                "exit_conditions": [
                    "Exit Condition 1",
                    "Exit Condition 2"
                ],
                "position_sizing": {
                    "method": "PositionMethod1",
                    "parameters": {"param1": 1.0, "param2": 2.0}
                },
                "risk_management": {
                    "method1": {"param1": 1.0},
                    "method2": {"param1": 2.0}
                },
                "backtesting": {
                    "method": "Method1",
                    "parameters": {"param1": 70, "param2": 30}
                }
            }
    
    def _fig_to_base64(self, fig: plt.Figure) -> str:
        """
        Convert a matplotlib figure to a base64 encoded string.
        
        Args:
            fig: Matplotlib figure
            
        Returns:
            Base64 encoded string
        """
        # Save figure to a bytes buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        
        # Encode as base64
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return img_str


# Utility functions for easily generating visualizations

def create_component_relationship_diagram(
    strategy_repository, 
    strategy_type: str,
    depth: int = 2,
    min_strength: float = 0.6,
    max_nodes: int = 15
) -> str:
    """
    Generate a diagram showing relationships between components for a strategy type.
    
    Args:
        strategy_repository: Neo4j strategy repository instance
        strategy_type: Type of trading strategy
        depth: Relationship depth to traverse
        min_strength: Minimum relationship strength to include
        max_nodes: Maximum number of nodes to display
        
    Returns:
        Base64 encoded image
    """
    visualizer = KnowledgeGraphVisualizer(strategy_repository)
    _, img_data = visualizer.create_component_relationship_diagram(
        strategy_type, depth, min_strength, max_nodes
    )
    return img_data

def create_compatibility_matrix(
    strategy_repository,
    component_type: str,
    strategy_type: Optional[str] = None,
    top_n: int = 10
) -> str:
    """
    Generate a compatibility matrix showing how different components work together.
    
    Args:
        strategy_repository: Neo4j strategy repository instance
        component_type: Type of component (e.g., "Indicator", "PositionSizing")
        strategy_type: Optional strategy type to filter by
        top_n: Number of components to include
        
    Returns:
        Base64 encoded image
    """
    visualizer = KnowledgeGraphVisualizer(strategy_repository)
    _, img_data = visualizer.create_compatibility_matrix(
        component_type, strategy_type, top_n
    )
    return img_data

def create_strategy_template_visualization(
    strategy_repository,
    strategy_type: str,
    instrument: Optional[str] = None,
    timeframe: Optional[str] = None
) -> str:
    """
    Generate a visualization of a strategy template based on the knowledge graph.
    
    Args:
        strategy_repository: Neo4j strategy repository instance
        strategy_type: Type of trading strategy
        instrument: Optional instrument symbol
        timeframe: Optional timeframe
        
    Returns:
        Base64 encoded image
    """
    visualizer = KnowledgeGraphVisualizer(strategy_repository)
    _, img_data = visualizer.create_strategy_template_visualization(
        strategy_type, instrument, timeframe
    )
    return img_data

"""
Example HTML template for embedding visualizations:

```html
<img src="data:image/png;base64,{{ visualization_data }}" alt="Knowledge Graph Visualization">
```
"""