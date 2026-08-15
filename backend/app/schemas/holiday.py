from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class HolidayBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    date: date
    description: Optional[str] = None
    is_active: bool = True


class HolidayCreate(HolidayBase):
    pass


class HolidayUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    date: Optional[date] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class HolidayResponse(HolidayBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
