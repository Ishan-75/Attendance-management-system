from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class AuditAction:
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    FAILED_LOGIN = "FAILED_LOGIN"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    PASSWORD_RESET = "PASSWORD_RESET"
    
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    ROLE_CHANGED = "ROLE_CHANGED"
    
    EMPLOYEE_CREATED = "EMPLOYEE_CREATED"
    EMPLOYEE_UPDATED = "EMPLOYEE_UPDATED"
    EMPLOYEE_DEACTIVATED = "EMPLOYEE_DEACTIVATED"
    EMPLOYEE_REACTIVATED = "EMPLOYEE_REACTIVATED"
    
    ATTENDANCE_CREATED = "ATTENDANCE_CREATED"
    ATTENDANCE_UPDATED = "ATTENDANCE_UPDATED"
    ATTENDANCE_CORRECTED = "ATTENDANCE_CORRECTED"
    
    LEAVE_APPLIED = "LEAVE_APPLIED"
    LEAVE_APPROVED = "LEAVE_APPROVED"
    LEAVE_REJECTED = "LEAVE_REJECTED"
    LEAVE_CANCELLED = "LEAVE_CANCELLED"
    
    DEPARTMENT_CREATED = "DEPARTMENT_CREATED"
    DEPARTMENT_UPDATED = "DEPARTMENT_UPDATED"
    DEPARTMENT_DELETED = "DEPARTMENT_DELETED"
    
    HOLIDAY_CREATED = "HOLIDAY_CREATED"
    HOLIDAY_UPDATED = "HOLIDAY_UPDATED"
    HOLIDAY_DELETED = "HOLIDAY_DELETED"
    
    SETTINGS_CHANGED = "SETTINGS_CHANGED"
    
    BACKUP_CREATED = "BACKUP_CREATED"
    BACKUP_RESTORED = "BACKUP_RESTORED"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    # Relationships
    user = relationship("User", back_populates="audit_logs")
