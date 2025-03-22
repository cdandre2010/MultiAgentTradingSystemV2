# Multi-Agent Trading System V2 Examples

This directory contains example scripts to demonstrate various aspects of the Multi-Agent Trading System V2.

## Knowledge Graph Integration Demo

The `knowledge_graph_demo.py` script demonstrates how the ConversationalAgent uses the Neo4j knowledge graph to enhance strategy creation with knowledge-driven recommendations.

To run the example:
```bash
python examples/knowledge_graph_demo.py
```

This example demonstrates:
1. Getting knowledge-driven recommendations for different strategy types
2. Enhancing strategy parameters with knowledge from Neo4j
3. Processing a user message with knowledge-driven recommendations

## Requirements

- Neo4j must be running and initialized with the enhanced schema
- The ConversationalAgent must be properly configured
- Environment variables must be set correctly

See the [Neo4j Setup Guide](../docs/neo4j_setup.md) and [Knowledge Graph Integration](../docs/knowledge_graph_integration.md) documentation for more details.