from setuptools import setup, find_packages

setup(
    name="multi_agent_trading_system",
    version="2.0.0",
    packages=find_packages(where="src"),
    package_dir={"":"src"},
    install_requires=[
        "fastapi>=0.88.0",
        "uvicorn>=0.15.0",
        "langchain>=0.0.267",
        "langchain-anthropic>=0.1.23",
        "anthropic>=0.5.0",
        "neo4j>=4.4.0",
        "influxdb-client>=1.26.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-jose>=3.3.0",
        "passlib>=1.7.4",
        "python-multipart>=0.0.5",
        "websockets>=10.0",
        "pandas>=1.3.5",
        "numpy>=1.21.0",
        "redis>=4.3.0",
        "bcrypt>=4.3.0",
        # Data source connectors
        "aiohttp>=3.8.0",
        "yfinance>=0.2.0",
        "python-binance>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=2.12.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "mypy>=0.910",
            "flake8>=4.0.0"
        ],
    },
    python_requires=">=3.9",
)