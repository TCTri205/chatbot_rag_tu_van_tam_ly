"""
Admin system configuration API router.
Handles reading and updating system_settings table.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict
from pydantic import BaseModel, Field

from src.database import get_db
from src.models.user import User
from src.models.audit import SystemSetting
from src.api.deps import require_admin

router = APIRouter()


class ConfigResponse(BaseModel):
    """System configuration item."""
    key: str = Field(..., description="Configuration key")
    value: str = Field(..., description="Configuration value")
    description: str = Field(..., description="Configuration description")
    
    class Config:
        from_attributes = True


class ConfigUpdate(BaseModel):
    """Update configuration value."""
    value: str = Field(..., description="New configuration value")


@router.get("/", response_model=List[ConfigResponse])
async def get_all_configs(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Get all system configurations.
    
    Returns:
        List of all configuration items
        
    Requires:
        Admin role
    """
    result = await db.execute(select(SystemSetting))
    configs = result.scalars().all()
    
    return [
        ConfigResponse(
            key=config.key,
            value=config.value,
            description=config.description or ""
        )
        for config in configs
    ]


@router.get("/{key}", response_model=ConfigResponse)
async def get_config(
    key: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Get a specific configuration by key.
    
    Args:
        key: Configuration key
        
    Returns:
        Configuration details
        
    Raises:
        404: Configuration not found
        
    Requires:
        Admin role
    """
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == key)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration '{key}' not found"
        )
    
    return ConfigResponse(
        key=config.key,
        value=config.value,
        description=config.description or ""
    )


@router.put("/{key}", response_model=ConfigResponse)
async def update_config(
    key: str,
    update: ConfigUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Update a system configuration value.
    
    Args:
        key: Configuration key to update
        update: New configuration value
        
    Returns:
        Updated configuration
        
    Raises:
        404: Configuration not found
        400: Invalid configuration value
        
    Requires:
        Admin role
    """
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == key)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration '{key}' not found"
        )
    
    # Validate configuration value based on key type
    _validate_config_value(key, update.value)
    
    # Update value with timestamp
    config.value = update.value
    # updated_at is handled by SQLAlchemy's onupdate
    await db.commit()
    await db.refresh(config)
    
    return ConfigResponse(
        key=config.key,
        value=config.value,
        description=config.description or ""
    )


def _validate_config_value(key: str, value: str) -> None:
    """
    Validate configuration value based on key type.
    
    Args:
        key: Configuration key
        value: Configuration value to validate
        
    Raises:
        HTTPException(400): If value is invalid
    """
    import json
    
    # Validation rules for specific keys
    if key == "crisis_hotlines":
        # Must be valid JSON array
        try:
            hotlines = json.loads(value)
            if not isinstance(hotlines, list):
                raise ValueError("Must be a JSON array")
            
            # Validate hotline structure
            for hotline in hotlines:
                if not isinstance(hotline, dict):
                    raise ValueError("Each hotline must be an object")
                if "name" not in hotline or "number" not in hotline:
                    raise ValueError("Each hotline must have 'name' and 'number' fields")
                    
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid crisis_hotlines format: {str(e)}"
            )
    
    elif key == "sos_keywords":
        # Must be comma-separated values
        if not value or not value.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SOS keywords cannot be empty"
            )
        keywords = [k.strip() for k in value.split(",")]
        if len(keywords) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must have at least 3 SOS keywords for safety"
            )
    
    elif key == "sys_prompt":
        # System prompt must be non-empty and reasonable length
        if not value or len(value.strip()) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="System prompt must be at least 50 characters"
            )
        if len(value) > 5000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="System prompt too long (max 5000 characters)"
            )
