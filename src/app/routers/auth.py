"""
Authentication router for the Multi-Agent Trading System.
"""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..auth import authenticate_user, create_access_token, get_current_user, get_password_hash
from ..config import settings
from ...models.user import User, UserCreate, Token, UserLogin
from ...database.connection import get_db_manager
from ...database.repositories.user_repository import UserRepository


router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db_manager = Depends(get_db_manager)
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # The OAuth2PasswordRequestForm uses 'username' field, but our authenticate_user
    # expects an email. Here we assume the user is entering their email in the username field.
    email = form_data.username  # This could be either username or email
    user = await authenticate_user(email, form_data.password, db_manager)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_id": str(user.id)
    }


@router.post("/register", response_model=Token)
async def register(
    user_in: UserCreate,
    db_manager = Depends(get_db_manager)
) -> Any:
    """
    Register a new user.
    """
    user_repo = UserRepository(db_manager)
    
    # Check if user with this email already exists
    existing_user = await user_repo.get_user_by_email(user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    hashed_password = get_password_hash(user_in.password)
    
    # Create the user
    user = await user_repo.create_user(user_in, hashed_password)
    
    # Generate access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_id": str(user.id)
    }


@router.post("/logout")
async def logout() -> Any:
    """
    Logout the current user.
    """
    # Note: With JWT, we don't need to do anything on the server side for logout
    # The client should just forget the token
    return {"status": "success", "message": "Successfully logged out"}


@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)) -> Any:
    """
    Get current user.
    """
    return current_user