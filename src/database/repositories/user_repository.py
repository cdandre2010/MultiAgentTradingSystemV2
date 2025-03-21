"""
User repository for database operations.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime

from src.database.connection import DatabaseManager
from src.models.user import UserInDB, UserCreate


class UserRepository:
    """Repository for user-related database operations."""

    def __init__(self, db_manager: DatabaseManager):
        """Initialize with database manager instance.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email.

        Args:
            email: User email

        Returns:
            User if found, None otherwise
        """
        query = "SELECT * FROM users WHERE email = ?"
        conn = self.db_manager.get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute(query, (email,))
        user_data = cursor.fetchone()
        
        if not user_data:
            return None
            
        # Convert row to dict with column names
        columns = [col[0] for col in cursor.description]
        user_dict = {columns[i]: user_data[i] for i in range(len(columns))}
        
        return UserInDB(**user_dict)
        
    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """Get user by username.

        Args:
            username: Username

        Returns:
            User if found, None otherwise
        """
        query = "SELECT * FROM users WHERE username = ?"
        conn = self.db_manager.get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute(query, (username,))
        user_data = cursor.fetchone()
        
        if not user_data:
            return None
            
        # Convert row to dict with column names
        columns = [col[0] for col in cursor.description]
        user_dict = {columns[i]: user_data[i] for i in range(len(columns))}
        
        return UserInDB(**user_dict)

    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        query = "SELECT * FROM users WHERE id = ?"
        conn = self.db_manager.get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute(query, (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            return None
            
        # Convert row to dict with column names
        columns = [col[0] for col in cursor.description]
        user_dict = {columns[i]: user_data[i] for i in range(len(columns))}
        
        return UserInDB(**user_dict)

    async def create_user(self, user: UserCreate, hashed_password: str) -> UserInDB:
        """Create a new user.

        Args:
            user: User data
            hashed_password: Hashed password

        Returns:
            Created user
        """
        import uuid
        
        # Generate a random user ID
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        
        query = """
        INSERT INTO users (id, email, username, password_hash, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        conn = self.db_manager.get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute(
            query, 
            (
                user_id,
                user.email,
                user.username,
                hashed_password,
                True,
                now
            )
        )
        conn.commit()
        
        # Get the inserted user with ID
        return await self.get_user_by_email(user.email)

    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp.

        Args:
            user_id: User ID
        """
        now = datetime.utcnow().isoformat()
        query = "UPDATE users SET last_login = ? WHERE id = ?"
        conn = self.db_manager.get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute(query, (now, user_id))
        conn.commit()