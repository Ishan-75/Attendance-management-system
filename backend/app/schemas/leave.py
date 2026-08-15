from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.employee import EmployeeSummary


class LeaveBase(BaseModel):
    employee_id: int
    leave_type: str = Field(..., description="CASUAL, SICK, EMERGENCY, ANNUAL, OTHER")
    start_date: date
    end_date: date
    number_of_days: float = Field(..., gt=0)
    reason: str = Field(..., min_length=3)


class LeaveCreate(LeaveBase):
    pass


class LeaveUpdate(BaseModel):
    leave_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    number_of_days: Optional[float] = None
    reason: Optional[str] = None


class LeaveDecision(BaseModel):
    reason: Optional[str] = Field(None, description="Optional note or rejection reason")


class LeaveResponse(LeaveBase):
    id: int
    status: str
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    employee: Optional[EmployeeSummary] = None
    approver_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
