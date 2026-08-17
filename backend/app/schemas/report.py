from datetime import date
from typing import Optional, List
from pydantic import BaseModel


class ReportFilter(BaseModel):
    start_date: date
    end_date: date
    department_id: Optional[int] = None
    employee_id: Optional[int] = None
    status: Optional[str] = None


class AttendanceReportRow(BaseModel):
    employee_code: str
    employee_name: str
    department_name: str
    designation: Optional[str] = "Staff"
    attendance_date: date
    status: str
    check_in: str
    check_out: str
    total_hours: float
    overtime_hours: float
    late_minutes: int
    early_departure_minutes: int
    remarks: str


class EmployeeAttendanceSummaryRow(BaseModel):
    employee_code: str
    employee_name: str
    department_name: str
    total_working_days: int
    present_days: int
    absent_days: int
    leave_days: int
    half_days: int
    week_off_days: int
    holiday_days: int
    wfh_days: int
    total_hours: float
    total_overtime: float
    attendance_percentage: float
