"""
Audit log and system settings models.
"""
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime

from src.database import Base
from src.models.base import UUIDMixin


class AuditLog(Base, UUIDMixin):
    """Audit log model for security tracking."""
    __tablename__ = "audit_logs"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    # Note: 'metadata' is a reserved word in SQLAlchemy Declarative API
    # Use 'extra_data' as Python attribute, but map to 'metadata' column in DB
    extra_data = Column("metadata", JSONB, nullable=True)  # Additional context data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<AuditLog {self.action} - {self.created_at}>"


class SystemSetting(Base):
    """System settings model for dynamic configuration."""
    __tablename__ = "system_settings"
    
    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<SystemSetting {self.key}>"
