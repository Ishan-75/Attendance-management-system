from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.holiday import HolidayCreate, HolidayUpdate, HolidayResponse
from app.schemas.common import APIResponse
from app.services.holiday_service import HolidayService
from app.api.v1.deps import require_manager, require_admin, get_client_ip
from app.models.user import User

router = APIRouter(prefix="/holidays", tags=["Holidays"])


@router.get("", response_model=APIResponse[List[HolidayResponse]])
def get_holidays(
    year: Optional[int] = Query(None),
    active_only: bool = False,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    holidays = HolidayService.get_holidays(db, year=year, active_only=active_only)
    return APIResponse(
        success=True,
        message="Holidays retrieved",
        data=[HolidayResponse.model_validate(h) for h in holidays]
    )


@router.post("", response_model=APIResponse[HolidayResponse], status_code=status.HTTP_201_CREATED)
def create_holiday(
    request: Request,
    hol_in: HolidayCreate,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    hol = HolidayService.create_holiday(db, hol_in, user=user, ip_address=ip)
    return APIResponse(
        success=True,
        message=f"Holiday '{hol.name}' scheduled for {hol.date}",
        data=HolidayResponse.model_validate(hol)
    )


@router.put("/{holiday_id}", response_model=APIResponse[HolidayResponse])
def update_holiday(
    request: Request,
    holiday_id: int,
    hol_in: HolidayUpdate,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    hol = HolidayService.update_holiday(db, holiday_id, hol_in, user=user, ip_address=ip)
    return APIResponse(
        success=True,
        message="Holiday updated successfully",
        data=HolidayResponse.model_validate(hol)
    )


@router.delete("/{holiday_id}", response_model=APIResponse[bool])
def delete_holiday(
    request: Request,
    holiday_id: int,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    HolidayService.delete_holiday(db, holiday_id, user=user, ip_address=ip)
    return APIResponse(
        success=True,
        message="Holiday deleted successfully",
        data=True
    )
