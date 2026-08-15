from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.dashboard import DashboardData
from app.schemas.common import APIResponse
from app.services.dashboard_service import DashboardService
from app.api.v1.deps import require_manager
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/data", response_model=APIResponse[DashboardData])
def get_dashboard_data(
    target_date: Optional[date] = Query(None, alias="date"),
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    data = DashboardService.get_dashboard_data(db, target_date=target_date)
    return APIResponse(
        success=True,
        message="Dashboard data retrieved",
        data=data
    )
