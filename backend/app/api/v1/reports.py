from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.report import AttendanceReportRow, ReportFilter
from app.schemas.common import APIResponse
from app.services.report_service import ReportService
from app.api.v1.deps import require_manager
from app.models.user import User
from app.core.timezone import get_current_date

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/attendance", response_model=APIResponse[List[AttendanceReportRow]])
def get_attendance_report(
    start_date: date = Query(...),
    end_date: date = Query(...),
    department_id: Optional[int] = Query(None),
    employee_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    filters = ReportFilter(
        start_date=start_date,
        end_date=end_date,
        department_id=department_id,
        employee_id=employee_id,
        status=status_filter
    )
    rows = ReportService.get_attendance_report(db, filters)
    return APIResponse(
        success=True,
        message=f"Report generated with {len(rows)} records",
        data=rows
    )


@router.get("/export-csv")
def export_attendance_csv(
    start_date: date = Query(...),
    end_date: date = Query(...),
    department_id: Optional[int] = Query(None),
    employee_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    filters = ReportFilter(
        start_date=start_date,
        end_date=end_date,
        department_id=department_id,
        employee_id=employee_id,
        status=status_filter
    )
    csv_stream = ReportService.export_attendance_csv(db, filters)
    filename = f"attendance_report_{start_date}_to_{end_date}.csv"
    
    return Response(
        content=csv_stream.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )


@router.get("/export-excel")
def export_attendance_excel(
    start_date: date = Query(...),
    end_date: date = Query(...),
    department_id: Optional[int] = Query(None),
    employee_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    filters = ReportFilter(
        start_date=start_date,
        end_date=end_date,
        department_id=department_id,
        employee_id=employee_id,
        status=status_filter
    )
    excel_stream = ReportService.export_attendance_excel(db, filters)
    filename = f"attendance_report_{start_date}_to_{end_date}.xlsx"
    
    return Response(
        content=excel_stream.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
    )


@router.get("/export-json")
def export_attendance_json(
    start_date: date = Query(...),
    end_date: date = Query(...),
    department_id: Optional[int] = Query(None),
    employee_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    filters = ReportFilter(
        start_date=start_date,
        end_date=end_date,
        department_id=department_id,
        employee_id=employee_id,
        status=status_filter
    )
    json_content = ReportService.export_attendance_json(db, filters)
    filename = f"attendance_report_{start_date}_to_{end_date}.json"
    
    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/json; charset=utf-8"
        }
    )


@router.get("/export-html")
def export_attendance_html(
    start_date: date = Query(...),
    end_date: date = Query(...),
    department_id: Optional[int] = Query(None),
    employee_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    filters = ReportFilter(
        start_date=start_date,
        end_date=end_date,
        department_id=department_id,
        employee_id=employee_id,
        status=status_filter
    )
    html_content = ReportService.export_attendance_html(db, filters)
    
    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Type": "text/html; charset=utf-8"
        }
    )
