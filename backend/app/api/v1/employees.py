from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeStatusUpdate,
    EmployeeResponse,
    EmployeeSummary
)
from app.schemas.common import APIResponse, PaginatedResponse
from app.services.employee_service import EmployeeService
from app.api.v1.deps import require_manager, get_current_user, get_client_ip, require_admin
from app.models.user import User

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.get("", response_model=APIResponse[PaginatedResponse[EmployeeResponse]])
def get_employees(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    department_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    skip = (page - 1) * page_size
    items, total = EmployeeService.get_employees(
        db,
        skip=skip,
        limit=page_size,
        department_id=department_id,
        status_filter=status_filter,
        search=search
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return APIResponse(
        success=True,
        message="Employees retrieved",
        data=PaginatedResponse(
            items=[EmployeeResponse.model_validate(e) for e in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    )


@router.post("", response_model=APIResponse[EmployeeResponse], status_code=status.HTTP_201_CREATED)
def create_employee(
    request: Request,
    emp_in: EmployeeCreate,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    emp = EmployeeService.create_employee(db, emp_in, user=user, ip_address=ip)
    return APIResponse(
        success=True,
        message=f"Employee {emp.full_name} ({emp.employee_id}) created successfully",
        data=EmployeeResponse.model_validate(emp)
    )


@router.get("/{employee_id}", response_model=APIResponse[EmployeeResponse])
def get_employee(
    employee_id: int,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    emp = EmployeeService.get_employee_by_id(db, employee_id)
    return APIResponse(
        success=True,
        message="Employee details retrieved",
        data=EmployeeResponse.model_validate(emp)
    )


@router.put("/{employee_id}", response_model=APIResponse[EmployeeResponse])
def update_employee(
    request: Request,
    employee_id: int,
    emp_in: EmployeeUpdate,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    emp = EmployeeService.update_employee(db, employee_id, emp_in, user=user, ip_address=ip)
    return APIResponse(
        success=True,
        message="Employee updated successfully",
        data=EmployeeResponse.model_validate(emp)
    )


@router.patch("/{employee_id}/status", response_model=APIResponse[EmployeeResponse])
def update_employee_status(
    request: Request,
    employee_id: int,
    status_in: EmployeeStatusUpdate,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    emp = EmployeeService.update_status(db, employee_id, status_in, user=user, ip_address=ip)
    return APIResponse(
        success=True,
        message=f"Status updated to {emp.status}",
        data=EmployeeResponse.model_validate(emp)
    )


@router.delete("/{employee_id}", response_model=APIResponse[bool])
def delete_employee(
    request: Request,
    employee_id: int,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    EmployeeService.delete_employee(db, employee_id, user=user, ip_address=ip)
    return APIResponse(
        success=True,
        message="Employee deleted successfully",
        data=True
    )
