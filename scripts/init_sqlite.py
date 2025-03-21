"""
Script to initialize SQLite database for the Multi-Agent Trading System.
"""
import os
import sqlite3
from pathlib import Path

# Get the script path
script_path = Path(__file__).parent.parent / "src" / "database" / "scripts" / "sqlite_init.sql"
db_path = Path(__file__).parent.parent / "trading_system.db"

# Check if the SQL file exists
if not script_path.exists():
    print(f"SQL script not found at {script_path}")
    exit(1)

# Connect to database
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
print(f"Connected to database at {db_path}")

# Read SQL script
with open(script_path, "r") as f:
    sql_script = f.read()

# Execute script
try:
    conn.executescript(sql_script)
    conn.commit()
    print("SQLite database initialized successfully")
except Exception as e:
    print(f"Error initializing SQLite database: {e}")
finally:
    conn.close()