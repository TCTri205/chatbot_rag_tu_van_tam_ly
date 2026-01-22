"""
Admin User Management API Router (Sprint 3).
Provides endpoints for listing, banning, and unbanning users.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_
from typing import Optional, List
import uuid

from src.database import get_db
from src.models.user import User, UserRole
from src.models.audit import AuditLog
from src.core.redis import get_redis
from src.api.deps import require_admin, require_super_admin
from pydantic import BaseModel

router = APIRouter()


# ============================================
# Request/Response Schemas
# ============================================

class UserListItem(BaseModel):
    """User list item schema."""
    id: uuid.UUID
    username: Optional[str]
    email: Optional[str]
    role: UserRole
    is_active: bool
    is_anonymous: bool
    created_at: str
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """User list response schema."""
    users: List[UserListItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class UserActionResponse(BaseModel):
    """Response for user actions (ban/unban)."""
    message: str
    user_id: uuid.UUID
    is_active: bool


class UserRoleResponse(BaseModel):
    """Response for role change actions."""
    message: str
    user_id: uuid.UUID
    role: UserRole


# ============================================
# Endpoints
# ============================================

@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by username or email"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """
    List all users with pagination and filtering.
    
    **Admin only**
    """
    # Build query - exclude anonymous users
    query = select(User).where(User.is_anonymous == False)
    
    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                User.username.ilike(search_pattern),
                User.email.ilike(search_pattern)
            )
        )
    
    if role:
        query = query.where(User.role == role)
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(desc(User.created_at)).limit(page_size).offset(offset)
    
    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Convert created_at to ISO string
    user_list = []
    for user in users:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "is_anonymous": user.is_anonymous,
            "created_at": user.created_at.isoformat() if user.created_at else ""
        }
        user_list.append(UserListItem(**user_dict))
    
    return UserListResponse(
        users=user_list,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total
    )


@router.post("/{user_id}/ban", response_model=UserActionResponse)
async def ban_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis),
    current_admin: User = Depends(require_admin)
):
    """
    Ban a user (set is_active = False).
    
    **Admin only**
    
    This will:
    1. Set user's is_active to False
    2. Invalidate all user's sessions in Redis
    3. Log audit trail
    """
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent banning admin/super_admin
    if user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot ban admin users"
        )
    
    # Already banned
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already banned"
        )
    
    # Ban user
    user.is_active = False
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="USER_BANNED",
        ip_address="N/A",  # TODO: Extract from request
        extra_data={"banned_user_id": str(user_id)}
    )
    db.add(audit_log)
    
    await db.commit()
    
    # Invalidate user sessions in Redis (non-critical operation)
    if redis is not None:
        try:
            cursor = 0
            sessions_invalidated = 0
            while True:
                cursor, keys = await redis.scan(cursor, match="session:*", count=100)
                for key in keys:
                    # Redis decode_responses=True, so keys are already strings
                    session_data = await redis.hgetall(key)
                    
                    # Redis decode_responses=True, so values are already strings
                    stored_user_id = session_data.get('user_id')
                    
                    if stored_user_id == str(user_id):
                        await redis.delete(key)
                        sessions_invalidated += 1
                        print(f"✅ Invalidated session {key} for banned user {user_id}")
                
                if cursor == 0:
                    break
            
            if sessions_invalidated > 0:
                print(f"✅ Successfully invalidated {sessions_invalidated} session(s) for user {user_id}")
            else:
                print(f"ℹ️ No active sessions found for user {user_id}")
                
        except Exception as e:
            # Log error but don't fail the request - user is still banned in database
            print(f"⚠️ Warning: Could not invalidate Redis sessions for user {user_id}: {e}")
            print(f"⚠️ User is still banned in database, but active sessions may persist until they naturally expire")
    else:
        # Redis not available - log warning but continue
        print(f"⚠️ Warning: Redis not available. User {user_id} is banned in database, but active sessions cannot be invalidated")
        print(f"⚠️ Active sessions will persist until they naturally expire or user logs out")
    
    return UserActionResponse(
        message="User banned successfully",
        user_id=user_id,
        is_active=False
    )


@router.post("/{user_id}/unban", response_model=UserActionResponse)
async def unban_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_admin)
):
    """
    Unban a user (set is_active = True).
    
    **Admin only**
    """
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Already active
    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already active"
        )
    
    # Unban user
    user.is_active = True
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="USER_UNBANNED",
        ip_address="N/A",  # TODO: Extract from request
        extra_data={"unbanned_user_id": str(user_id)}
    )
    db.add(audit_log)
    
    await db.commit()
    
    return UserActionResponse(
        message="User unbanned successfully",
        user_id=user_id,
        is_active=True
    )


@router.post("/{user_id}/promote", response_model=UserRoleResponse)
async def promote_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_super_admin)
):
    """
    Promote a user to admin role.
    
    **Super Admin only**
    """
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Cannot promote self
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    # Already admin or super_admin
    if user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already an admin"
        )
    
    # Promote to admin
    user.role = UserRole.ADMIN
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="USER_PROMOTED",
        ip_address="N/A",
        extra_data={"promoted_user_id": str(user_id), "new_role": "admin"}
    )
    db.add(audit_log)
    
    await db.commit()
    
    return UserRoleResponse(
        message="User promoted to admin successfully",
        user_id=user_id,
        role=UserRole.ADMIN
    )


@router.post("/{user_id}/demote", response_model=UserRoleResponse)
async def demote_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_super_admin)
):
    """
    Demote an admin to regular user role.
    
    **Super Admin only**
    """
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Cannot demote self
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    # Cannot demote super_admin
    if user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot demote super admin"
        )
    
    # Not an admin
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not an admin"
        )
    
    # Demote to user
    user.role = UserRole.USER
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="USER_DEMOTED",
        ip_address="N/A",
        extra_data={"demoted_user_id": str(user_id), "new_role": "user"}
    )
    db.add(audit_log)
    
    await db.commit()
    
    return UserRoleResponse(
        message="User demoted to regular user successfully",
        user_id=user_id,
        role=UserRole.USER
    )
