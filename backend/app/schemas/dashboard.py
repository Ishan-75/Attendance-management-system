from datetime import date
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.leave import LeaveResponse


class DashboardSummary(BaseModel):
    total_employees: int
    active_employees: int
    present_today: int
    absent_today: int
    leave_today: int
    week_off_today: int
    half_day_today: int
    holiday_today: int
    wfh_today: int
    unmarked_today: int
    attendance_rate: float
    selected_date: date


class DepartmentAttendanceStat(BaseModel):
    department_id: int
    department_name: str
    total_employees: int
    present: int
    absent: int
    leave: int
    attendance_rate: float


class AttendanceTrendPoint(BaseModel):
    date: date
    formatted_date: str
    present: int
    absent: int
    leave: int
    attendance_rate: float


class RecentActivityItem(BaseModel):
    id: int
    action: str
    description: str
    user_name: Optional[str] = "System"
    timestamp: str


class DashboardData(BaseModel):
    summary: DashboardSummary
    trends: List[AttendanceTrendPoint]
    department_stats: List[DepartmentAttendanceStat]
    pending_leaves: List[LeaveResponse]
    recent_activities: List[RecentActivityItem]
