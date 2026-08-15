from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class BackupMetadata(BaseModel):
    id: str  # sanitized filename or identifier
    filename: str
    size_bytes: int
    size_human: str
    created_at: datetime
    creator_name: Optional[str] = "Admin"
    db_type: str = "sqlite"


class BackupRestoreRequest(BaseModel):
    backup_id: str
    confirm: bool = False


class SettingItem(BaseModel):
    key: str
    value: str
    description: Optional[str] = None


class SettingsUpdate(BaseModel):
    settings: List[SettingItem]
