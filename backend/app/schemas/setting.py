from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class SettingResponse(BaseModel):
    id: int
    key: str
    value: str
    description: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SettingBulkUpdate(BaseModel):
    settings: List[dict]  # list of {"key": "...", "value": "..."}
