"""
Authentication endpoints for user registration and login.
"""
import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database import get_db
from src.core.redis import get_redis
from src.schemas.auth import UserCreate, UserLogin, Token, UserProfileUpdate
from src.schemas.user import UserResponse
from src.models.user import User, UserRole
from src.core.security import get_password_hash, verify_password, create_access_token
from src.api.deps import get_current_active_user
from src.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register/", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Register a new user account.
    
    Args:
        user_data: User registration data (email, password, username)
        db: Database session
    
    Returns:
        JWT access token
    
    Raises:
        400: Email already registered
    """
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        role=UserRole.USER,
        is_anonymous=False,
        is_active=True
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Generate access token
    access_token = create_access_token(
        data={"sub": str(new_user.id), "role": new_user.role.value}
    )
    
    # Update session if provided (upgrade from guest to authenticated)
    if x_session_id and redis:
        try:
            session_key = f"session:{x_session_id}"
            exists = await redis.exists(session_key)
            if exists:
                await redis.hset(session_key, "user_id", str(new_user.id))
                logger.info(f"Updated session {x_session_id} with new user {new_user.id}")
        except Exception as e:
            # Don't fail registration if session update fails
            logger.warning(f"Failed to update session during registration: {str(e)}")
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": str(new_user.id),
            "email": new_user.email,
            "username": new_user.username,
            "role": new_user.role.value,
            "is_active": new_user.is_active
        }
    }


@router.post("/login/", response_model=Token)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    Authenticate user and return JWT token.
    
    Args:
        credentials: Login credentials (email, password)
        db: Database session
    
    Returns:
        JWT access token
    
    Raises:
        401: Invalid credentials or inactive account
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Generate access token
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
    
    # Update session if provided (upgrade from guest to authenticated)
    if x_session_id and redis:
        try:
            session_key = f"session:{x_session_id}"
            exists = await redis.exists(session_key)
            if exists:
                await redis.hset(session_key, "user_id", str(user.id))
                logger.info(f"Updated session {x_session_id} with user {user.id}")
        except Exception as e:
            # Don't fail login if session update fails
            logger.warning(f"Failed to update session during login: {str(e)}")
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role.value,
            "is_active": user.is_active
        }
    }


@router.get("/me/", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Authenticated user from token
    
    Returns:
        User profile data
    """
    return current_user


@router.put("/me/", response_model=UserResponse)
async def update_current_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current authenticated user profile.
    
    Args:
        profile_data: Profile update data (username)
        current_user: Authenticated user from token
        db: Database session
    
    Returns:
        Updated user profile data
    """
    # Update username if provided
    if profile_data.username is not None:
        current_user.username = profile_data.username
    
    await db.commit()
    await db.refresh(current_user)
    
    logger.info(f"User {current_user.id} updated profile: username={current_user.username}")
    
    return current_user

