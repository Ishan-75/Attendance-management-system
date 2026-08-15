import uuid
from datetime import date, datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class EmploymentType:
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERN = "INTERN"


class EmployeeStatus:
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    RESIGNED = "RESIGNED"
    TERMINATED = "TERMINATED"
    ON_NOTICE = "ON_NOTICE"


class Employee(Base, TimestampMixin):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uuid: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    employee_id: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    department_id: Mapped[int] = mapped_column(Integer, ForeignKey("departments.id"), nullable=False, index=True)
    designation: Mapped[str] = mapped_column(String(100), nullable=False)
    joining_date: Mapped[date] = mapped_column(Date, nullable=False)
    employment_type: Mapped[str] = mapped_column(String(30), default=EmploymentType.FULL_TIME, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default=EmployeeStatus.ACTIVE, nullable=False, index=True)
    
    profile_photo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    department = relationship("Department", back_populates="employees")
    attendance_records = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")
    leave_records = relationship("Leave", back_populates="employee", cascade="all, delete-orphan")
