from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class AttendanceBase(BaseModel):
    employee_id: int
    attendance_date: date
    status: str = Field(default="PRESENT", description="PRESENT, ABSENT, LEAVE, WEEK_OFF, HALF_DAY, HOLIDAY, WORK_FROM_HOME, INACTIVE")
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    remarks: Optional[str] = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceBulkItem(BaseModel):
    employee_id: int
    status: str = "PRESENT"
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    remarks: Optional[str] = None


class AttendanceBulkCreate(BaseModel):
    attendance_date: date
    records: List[AttendanceBulkItem]


class AttendanceUpdate(BaseModel):
    status: Optional[str] = None
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    remarks: Optional[str] = None


class AttendanceCorrection(BaseModel):
    status: str
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    remarks: Optional[str] = None
    reason: str = Field(..., min_length=5, description="Mandatory reason for attendance correction")


class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    employee_code: Optional[str] = None
    employee_name: Optional[str] = None
    department_name: Optional[str] = None
    attendance_date: date
    status: str
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    total_hours: float
    overtime_hours: float
    late_minutes: int
    early_departure_minutes: int
    remarks: Optional[str] = None
    marked_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceDayCalendar(BaseModel):
    date: date
    status: Optional[str] = None
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    total_hours: float = 0.0
    overtime_hours: float = 0.0
    is_holiday: bool = False
    holiday_name: Optional[str] = None
    is_weekend: bool = False
    remarks: Optional[str] = None


class EmployeeMonthlyCalendarResponse(BaseModel):
    employee_id: int
    employee_code: str
    employee_name: str
    year: int
    month: int
    total_working_days: int
    present_days: int
    absent_days: int
    leave_days: int
    week_off_days: int
    half_days: int
    holiday_days: int
    work_from_home_days: int
    total_hours_worked: float
    total_overtime_hours: float
    attendance_percentage: float
    calendar_days: List[AttendanceDayCalendar]


class AttendanceSheetItem(BaseModel):
    employee_id: int
    employee_code: str
    full_name: str
    department_name: str
    designation: str
    attendance_id: Optional[int] = None
    status: Optional[str] = "PRESENT"
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    total_hours: float = 0.0
    overtime_hours: float = 0.0
    remarks: Optional[str] = None
    is_marked: bool = False
