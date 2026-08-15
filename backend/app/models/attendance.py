import uuid
from datetime import date, time
from typing import Optional
from sqlalchemy import String, Integer, Date, Time, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class AttendanceStatus:
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LEAVE = "LEAVE"
    WEEK_OFF = "WEEK_OFF"
    HALF_DAY = "HALF_DAY"
    HOLIDAY = "HOLIDAY"
    WORK_FROM_HOME = "WORK_FROM_HOME"
    INACTIVE = "INACTIVE"

    ALL = [PRESENT, ABSENT, LEAVE, WEEK_OFF, HALF_DAY, HOLIDAY, WORK_FROM_HOME, INACTIVE]


class Attendance(Base, TimestampMixin):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uuid: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default=AttendanceStatus.PRESENT, nullable=False, index=True)
    
    check_in_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    check_out_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    total_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    overtime_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    late_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    early_departure_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    remarks: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    marked_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    employee = relationship("Employee", back_populates="attendance_records")
    marker = relationship("User")

    __table_args__ = (
        UniqueConstraint("employee_id", "attendance_date", name="uq_employee_date_attendance"),
    )
