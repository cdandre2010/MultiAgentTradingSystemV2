import pytest
import os
import sqlite3
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.database.connection import DatabaseManager
from src.database.repositories.user_repository import UserRepository
from src.models.user import UserCreate
from src.app.auth import get_password_hash


@pytest.fixture
def setup_test_db():
    """Create a test in-memory SQLite database with the required schema."""
    # Create in-memory database
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE users (
        id VARCHAR(36) PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        last_login TEXT
    )
    ''')
    
    conn.commit()
    return conn


@pytest.fixture
def mock_db_manager(setup_test_db):
    """Create a mock database manager with the test database."""
    # Create a real DatabaseManager with the test connection
    from src.database.connection import DatabaseManager
    
    db_manager = DatabaseManager()
    db_manager.get_sqlite_connection = MagicMock(return_value=setup_test_db)
    return db_manager


@pytest.mark.asyncio
async def test_create_user(mock_db_manager):
    """Test creating a user in the database."""
    # Create repository with mock db manager
    repo = UserRepository(mock_db_manager)
    
    # Create test user
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="securepassword"
    )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user in database
    user = await repo.create_user(user_data, hashed_password)
    
    # Verify user was created with correct data
    assert user is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.id.startswith("user_")
    assert user.is_active is True
    assert user.password_hash == hashed_password


@pytest.mark.asyncio
async def test_get_user_by_email(mock_db_manager):
    """Test retrieving a user by email."""
    # Create repository with mock db manager
    repo = UserRepository(mock_db_manager)
    
    # Create test user
    user_data = UserCreate(
        username="emailuser",
        email="email@example.com",
        password="securepassword"
    )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user in database
    created_user = await repo.create_user(user_data, hashed_password)
    
    # Retrieve user by email
    retrieved_user = await repo.get_user_by_email("email@example.com")
    
    # Verify user was retrieved correctly
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.username == "emailuser"
    assert retrieved_user.email == "email@example.com"
    assert retrieved_user.password_hash == hashed_password


@pytest.mark.asyncio
async def test_get_user_by_id(mock_db_manager):
    """Test retrieving a user by ID."""
    # Create repository with mock db manager
    repo = UserRepository(mock_db_manager)
    
    # Create test user
    user_data = UserCreate(
        username="iduser",
        email="id@example.com",
        password="securepassword"
    )
    
    # Hash password
    hashed_password = get_password_hash(user_data.password)
    
    # Create user in database
    created_user = await repo.create_user(user_data, hashed_password)
    
    # Retrieve user by ID
    retrieved_user = await repo.get_user_by_id(created_user.id)
    
    # Verify user was retrieved correctly
    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.username == "iduser"
    assert retrieved_user.email == "id@example.com"
    assert retrieved_user.password_hash == hashed_password