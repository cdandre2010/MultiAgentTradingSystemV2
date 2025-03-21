from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class UserBase(BaseModel):
    """Base user model with common attributes."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    

class UserCreate(UserBase):
    """User creation model with password."""
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """User login credentials."""
    username: str
    password: str


class UserInDB(UserBase):
    """User model as stored in the database."""
    id: str
    password_hash: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    
    model_config = {
        "from_attributes": True
    }


class User(UserBase):
    """User model returned to clients (no sensitive data)."""
    id: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    
    model_config = {
        "from_attributes": True
    }


class UserPreferences(BaseModel):
    """User preferences model."""
    theme: str = "light"
    default_instrument: Optional[str] = None
    default_frequency: Optional[str] = None
    email_notifications: bool = True


class UserWithPreferences(User):
    """User model with preferences."""
    preferences: UserPreferences


class Token(BaseModel):
    """JWT token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 hours in seconds
    user_id: str


class TokenPayload(BaseModel):
    """JWT token payload model."""
    sub: str
    exp: int