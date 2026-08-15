from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogResponse
from app.schemas.common import APIResponse, PaginatedResponse
from app.api.v1.deps import require_admin
from app.models.user import User

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs (Admin)"])


@router.get("", response_model=APIResponse[PaginatedResponse[AuditLogResponse]])
def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if start_date:
        query = query.filter(AuditLog.timestamp >= f"{start_date} 00:00:00")
    if end_date:
        query = query.filter(AuditLog.timestamp <= f"{end_date} 23:59:59")

    total = query.count()
    skip = (page - 1) * page_size
    items = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(page_size).all()
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    formatted = [
        AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_name=log.user.full_name if log.user else "System",
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            old_value=log.old_value,
            new_value=log.new_value,
            description=log.description,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            timestamp=log.timestamp
        )
        for log in items
    ]

    return APIResponse(
        success=True,
        message="Audit logs retrieved",
        data=PaginatedResponse(
            items=formatted,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )
