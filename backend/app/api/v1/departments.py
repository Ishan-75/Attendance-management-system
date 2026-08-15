from typing import List
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.schemas.common import APIResponse
from app.services.department_service import DepartmentService
from app.api.v1.deps import require_manager, require_admin, get_client_ip
from app.models.user import User

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=APIResponse[List[DepartmentResponse]])
def get_departments(
    active_only: bool = False,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    depts = DepartmentService.get_departments(db, active_only=active_only)
    return APIResponse(
        success=True,
        message="Departments retrieved",
        data=depts
    )


@router.post("", response_model=APIResponse[DepartmentResponse], status_code=status.HTTP_201_CREATED)
def create_department(
    request: Request,
    dept_in: DepartmentCreate,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    dept = DepartmentService.create_department(db, dept_in, user=user, ip_address=ip)
    return APIResponse(
        success=True,
        message=f"Department '{dept.name}' created successfully",
        data=DepartmentResponse.model_validate(dept)
    )


@router.put("/{department_id}", response_model=APIResponse[DepartmentResponse])
def update_department(
    request: Request,
    department_id: int,
    dept_in: DepartmentUpdate,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    dept = DepartmentService.update_department(db, department_id, dept_in, user=user, ip_address=ip)
    return APIResponse(
        success=True,
        message="Department updated successfully",
        data=DepartmentResponse.model_validate(dept)
    )


@router.delete("/{department_id}", response_model=APIResponse[bool])
def delete_department(
    request: Request,
    department_id: int,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    DepartmentService.delete_department(db, department_id, user=user, ip_address=ip)
    return APIResponse(
        success=True,
        message="Department deleted successfully",
        data=True
    )
