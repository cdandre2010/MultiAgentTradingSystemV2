#!/bin/bash

# Helper script for development tasks

function show_help() {
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Available commands:"
    echo "  setup       - Set up development environment"
    echo "  server      - Run the FastAPI server"
    echo "  test        - Run all tests"
    echo "  test:unit   - Run unit tests"
    echo "  lint        - Run linting checks"
    echo "  format      - Format code with black"
    echo "  typecheck   - Run type checking with mypy"
    echo "  clean       - Clean up temporary files"
    echo "  help        - Show this help message"
}

case "$1" in
    setup)
        echo "Setting up development environment..."
        pip install -e ".[dev]"
        ;;
    server)
        echo "Starting FastAPI server..."
        uvicorn src.app.main:app --reload
        ;;
    test)
        echo "Running all tests..."
        pytest
        ;;
    test:unit)
        echo "Running unit tests..."
        pytest tests/unit/
        ;;
    lint)
        echo "Running linting checks..."
        flake8 src/ tests/
        ;;
    format)
        echo "Formatting code..."
        black src/ tests/
        ;;
    typecheck)
        echo "Running type checking..."
        mypy src/ tests/
        ;;
    clean)
        echo "Cleaning up temporary files..."
        find . -type d -name "__pycache__" -exec rm -rf {} +
        find . -type d -name "*.egg-info" -exec rm -rf {} +
        find . -type d -name ".pytest_cache" -exec rm -rf {} +
        find . -type f -name "*.pyc" -delete
        find . -type f -name "*.pyo" -delete
        find . -type f -name "*.pyd" -delete
        ;;
    help|*)
        show_help
        ;;
esac