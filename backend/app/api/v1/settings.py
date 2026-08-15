from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.setting import SettingResponse, SettingBulkUpdate
from app.schemas.common import APIResponse
from app.services.setting_service import SettingService
from app.api.v1.deps import require_admin, require_manager, get_client_ip
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=APIResponse[List[SettingResponse]])
def get_settings(
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    settings = SettingService.get_all_settings(db)
    return APIResponse(
        success=True,
        message="Settings retrieved",
        data=[SettingResponse.model_validate(s) for s in settings]
    )


@router.put("", response_model=APIResponse[List[SettingResponse]])
def update_settings(
    request: Request,
    updates: SettingBulkUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    updated = SettingService.update_settings(db, updates.settings, user=admin, ip_address=ip)
    return APIResponse(
        success=True,
        message="Settings updated successfully",
        data=[SettingResponse.model_validate(s) for s in updated]
    )
