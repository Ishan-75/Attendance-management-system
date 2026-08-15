from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.schemas.department import DepartmentResponse


class EmployeeBase(BaseModel):
    employee_id: Optional[str] = Field(None, max_length=30, description="Auto-generated if omitted (e.g. EMP-0001)")
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    department_id: int
    designation: str = Field(..., min_length=2, max_length=100)
    joining_date: date
    employment_type: str = Field(default="FULL_TIME", description="FULL_TIME, PART_TIME, CONTRACT, INTERN")
    status: str = Field(default="ACTIVE", description="ACTIVE, INACTIVE, RESIGNED, TERMINATED, ON_NOTICE")
    profile_photo: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    department_id: Optional[int] = None
    designation: Optional[str] = None
    joining_date: Optional[date] = None
    employment_type: Optional[str] = None
    status: Optional[str] = None
    profile_photo: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None


class EmployeeStatusUpdate(BaseModel):
    status: str = Field(..., description="ACTIVE, INACTIVE, RESIGNED, TERMINATED, ON_NOTICE")
    reason: Optional[str] = Field(None, description="Reason for status change")


class EmployeeResponse(EmployeeBase):
    id: int
    full_name: str
    employee_id: str
    department: Optional[DepartmentResponse] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeSummary(BaseModel):
    id: int
    employee_id: str
    full_name: str
    email: str
    department_name: Optional[str] = None
    designation: str
    status: str
    
    model_config = ConfigDict(from_attributes=True)
