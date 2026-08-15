from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = "System"
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    description: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
