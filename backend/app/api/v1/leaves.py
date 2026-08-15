from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.leave import LeaveCreate, LeaveUpdate, LeaveDecision, LeaveResponse
from app.schemas.common import APIResponse, PaginatedResponse
from app.services.leave_service import LeaveService
from app.api.v1.deps import require_manager, get_current_user, get_client_ip
from app.models.user import User

router = APIRouter(prefix="/leaves", tags=["Leaves"])


@router.get("", response_model=APIResponse[PaginatedResponse[LeaveResponse]])
def get_leaves(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    employee_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None),
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    skip = (page - 1) * page_size
    items, total = LeaveService.get_leaves(
        db,
        skip=skip,
        limit=page_size,
        employee_id=employee_id,
        department_id=department_id,
        status_filter=status_filter
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    formatted_items = []
    for l in items:
        formatted_items.append(
            LeaveResponse(
                id=l.id,
                employee_id=l.employee_id,
                leave_type=l.leave_type,
                start_date=l.start_date,
                end_date=l.end_date,
                number_of_days=l.number_of_days,
                reason=l.reason,
                status=l.status,
                approved_by=l.approved_by,
                approved_at=l.approved_at,
                rejection_reason=l.rejection_reason,
                employee={
                    "id": l.employee.id,
                    "employee_id": l.employee.employee_id,
                    "full_name": l.employee.full_name,
                    "email": l.employee.email,
                    "department_name": l.employee.department.name if l.employee.department else None,
                    "designation": l.employee.designation,
                    "status": l.employee.status
                },
                approver_name=l.approver.full_name if l.approver else None,
                created_at=l.created_at,
                updated_at=l.updated_at
            )
        )

    return APIResponse(
        success=True,
        message="Leave requests retrieved",
        data=PaginatedResponse(
            items=formatted_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )


@router.post("", response_model=APIResponse[LeaveResponse], status_code=status.HTTP_201_CREATED)
def apply_leave(
    request: Request,
    leave_in: LeaveCreate,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    leave = LeaveService.apply_leave(db, leave_in, user=user, ip_address=ip)
    return APIResponse(
        success=True,
        message="Leave request submitted successfully",
        data=LeaveResponse.model_validate(leave)
    )


@router.patch("/{leave_id}/approve", response_model=APIResponse[LeaveResponse])
def approve_leave(
    request: Request,
    leave_id: int,
    decision: Optional[LeaveDecision] = None,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    leave = LeaveService.approve_leave(db, leave_id, user=user, decision=decision, ip_address=ip)
    return APIResponse(
        success=True,
        message=f"Leave request #{leave.id} approved and attendance updated",
        data=LeaveResponse.model_validate(leave)
    )


@router.patch("/{leave_id}/reject", response_model=APIResponse[LeaveResponse])
def reject_leave(
    request: Request,
    leave_id: int,
    decision: LeaveDecision,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    leave = LeaveService.reject_leave(db, leave_id, user=user, decision=decision, ip_address=ip)
    return APIResponse(
        success=True,
        message=f"Leave request #{leave.id} rejected",
        data=LeaveResponse.model_validate(leave)
    )
