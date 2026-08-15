import uuid
from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Integer, Date, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class LeaveType:
    CASUAL = "CASUAL"
    SICK = "SICK"
    EMERGENCY = "EMERGENCY"
    ANNUAL = "ANNUAL"
    OTHER = "OTHER"

    ALL = [CASUAL, SICK, EMERGENCY, ANNUAL, OTHER]


class LeaveStatus:
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

    ALL = [PENDING, APPROVED, REJECTED, CANCELLED]


class Leave(Base, TimestampMixin):
    __tablename__ = "leaves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uuid: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type: Mapped[str] = mapped_column(String(30), default=LeaveType.CASUAL, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    number_of_days: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=LeaveStatus.PENDING, nullable=False, index=True)
    
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    employee = relationship("Employee", back_populates="leave_records")
    approver = relationship("User")
