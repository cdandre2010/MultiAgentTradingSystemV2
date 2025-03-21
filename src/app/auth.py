"""
Authentication module for the Multi-Agent Trading System.
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from .config import settings
from ..models.user import TokenPayload, User, UserInDB
from ..database.connection import get_db_manager
from ..database.repositories.user_repository import UserRepository


# Password hashing - using bcrypt directly instead of through passlib
import bcrypt

# OAuth2 with password flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    try:
        # Print debug info
        print(f"Verifying password: {plain_password[:2]}... against hash: {hashed_password[:10]}...")
        
        result = bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
        print(f"Password verification result: {result}")
        return result
    except Exception as e:
        print(f"Error verifying password: {str(e)}")
        # Return False on any error
        return False


def get_password_hash(password: str) -> str:
    """Hash a password."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db_manager = Depends(get_db_manager)
) -> User:
    """Get the current user from a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(sub=payload["sub"], exp=payload["exp"])
        
        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                               detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                           detail="Could not validate credentials")
    
    user_repo = UserRepository(db_manager)
    user = await user_repo.get_user_by_id(token_data.sub)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                           detail="User not found")
    
    # Convert UserInDB to User model
    return User(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at
    )


async def authenticate_user(
    identifier: str, 
    password: str,
    db_manager = Depends(get_db_manager)
) -> Optional[User]:
    """
    Authenticate a user by email/username and password.
    
    Args:
        identifier: Email or username
        password: Password to verify
        db_manager: Database manager instance
        
    Returns:
        User if authenticated, None otherwise
    """
    try:
        print(f"Authenticating user: {identifier}")
        user_repo = UserRepository(db_manager)
        
        # Try to find user by email first
        user_db = await user_repo.get_user_by_email(identifier)
        print(f"Found by email: {user_db is not None}")
        
        # If not found by email, try by username
        if not user_db:
            user_db = await user_repo.get_user_by_username(identifier)
            print(f"Found by username: {user_db is not None}")
            
        # If still not found, return None
        if not user_db:
            print("User not found")
            return None
        
        print(f"User found: {user_db.username}, {user_db.email}")
        
        # Use our verify_password function (which logs debug info)
        if not verify_password(password, user_db.password_hash):
            print("Password verification failed")
            return None
        
        # Update last login timestamp
        print("Updating last login timestamp")
        await user_repo.update_last_login(user_db.id)
        
        # Convert UserInDB to User model
        user = User(
            id=user_db.id,
            username=user_db.username,
            email=user_db.email,
            is_active=user_db.is_active,
            created_at=user_db.created_at
        )
        print(f"Authentication successful for user: {user.username}")
        return user
    except Exception as e:
        print(f"Error in authenticate_user: {str(e)}")
        import traceback
        traceback.print_exc()
        return None