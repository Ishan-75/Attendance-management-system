from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceBulkCreate,
    AttendanceCorrection,
    AttendanceResponse,
    AttendanceSheetItem,
    EmployeeMonthlyCalendarResponse
)
from app.schemas.common import APIResponse
from app.services.attendance_service import AttendanceService
from app.api.v1.deps import require_manager, get_client_ip
from app.models.user import User
from app.core.timezone import get_current_date

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("/sheet", response_model=APIResponse[List[AttendanceSheetItem]])
def get_daily_attendance_sheet(
    date_val: Optional[date] = Query(None, alias="date"),
    department_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    target_date = date_val or get_current_date()
    items = AttendanceService.get_attendance_sheet(
        db,
        attendance_date=target_date,
        department_id=department_id,
        search=search
    )
    return APIResponse(
        success=True,
        message=f"Attendance sheet for {target_date} retrieved",
        data=items
    )


@router.post("", response_model=APIResponse[AttendanceResponse])
def mark_single_attendance(
    request: Request,
    att_in: AttendanceCreate,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    att = AttendanceService.mark_single_attendance(db, att_in, user=user, ip_address=ip)
    
    return APIResponse(
        success=True,
        message="Attendance recorded successfully",
        data=AttendanceResponse(
            id=att.id,
            employee_id=att.employee_id,
            employee_code=att.employee.employee_id if att.employee else None,
            employee_name=att.employee.full_name if att.employee else None,
            department_name=att.employee.department.name if att.employee and att.employee.department else None,
            attendance_date=att.attendance_date,
            status=att.status,
            check_in_time=att.check_in_time,
            check_out_time=att.check_out_time,
            total_hours=att.total_hours,
            overtime_hours=att.overtime_hours,
            late_minutes=att.late_minutes,
            early_departure_minutes=att.early_departure_minutes,
            remarks=att.remarks,
            marked_by=att.marked_by,
            created_at=att.created_at,
            updated_at=att.updated_at
        )
    )


@router.post("/bulk", response_model=APIResponse[int])
def mark_bulk_attendance(
    request: Request,
    bulk_in: AttendanceBulkCreate,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    results = AttendanceService.mark_bulk_attendance(db, bulk_in, user=user, ip_address=ip)
    return APIResponse(
        success=True,
        message=f"Successfully marked attendance for {len(results)} employees on {bulk_in.attendance_date}",
        data=len(results)
    )


@router.put("/{attendance_id}/correct", response_model=APIResponse[AttendanceResponse])
def correct_attendance(
    request: Request,
    attendance_id: int,
    correction: AttendanceCorrection,
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    att = AttendanceService.correct_attendance(db, attendance_id, correction, user=user, ip_address=ip)
    return APIResponse(
        success=True,
        message="Attendance correction applied and audit logged",
        data=AttendanceResponse(
            id=att.id,
            employee_id=att.employee_id,
            employee_code=att.employee.employee_id if att.employee else None,
            employee_name=att.employee.full_name if att.employee else None,
            department_name=att.employee.department.name if att.employee and att.employee.department else None,
            attendance_date=att.attendance_date,
            status=att.status,
            check_in_time=att.check_in_time,
            check_out_time=att.check_out_time,
            total_hours=att.total_hours,
            overtime_hours=att.overtime_hours,
            late_minutes=att.late_minutes,
            early_departure_minutes=att.early_departure_minutes,
            remarks=att.remarks,
            marked_by=att.marked_by,
            created_at=att.created_at,
            updated_at=att.updated_at
        )
    )


@router.get("/employee/{employee_id}/calendar", response_model=APIResponse[EmployeeMonthlyCalendarResponse])
def get_employee_monthly_calendar(
    employee_id: int,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    data = AttendanceService.get_employee_monthly_calendar(db, employee_id, year, month)
    return APIResponse(
        success=True,
        message=f"Monthly attendance calendar for {month}/{year} retrieved",
        data=data
    )
