import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    device_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    device_name: Mapped[str] = mapped_column(String(100), nullable=False)
    platform: Mapped[str] = mapped_column(String(30), default="android")  # android, web, windows, ios
    app_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])


class SyncOperation(Base):
    """Idempotency log tracking every unique client sync operation to prevent duplicate processing."""
    __tablename__ = "sync_operations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    operation_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    device_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Attendance, Employee, Leave, etc.
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    operation: Mapped[str] = mapped_column(String(20), nullable=False)  # CREATE, UPDATE, DELETE
    status: Mapped[str] = mapped_column(String(20), default="PROCESSED")  # PROCESSED, CONFLICT, FAILED
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )


class SyncConflict(Base):
    """Preserves conflicting changes from multiple devices for transparent manual resolution."""
    __tablename__ = "sync_conflicts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conflict_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: str(uuid.uuid4())
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    server_payload: Mapped[str] = mapped_column(Text, nullable=False)
    client_payload: Mapped[str] = mapped_column(Text, nullable=False)
    conflict_reason: Mapped[str] = mapped_column(Text, nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)  # PENDING, RESOLVED
    resolved_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_strategy: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # SERVER_WINS, CLIENT_WINS, MANUAL_MERGE
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    resolved_by = relationship("User", foreign_keys=[resolved_by_user_id])
