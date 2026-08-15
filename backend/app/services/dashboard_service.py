from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.employee import Employee, EmployeeStatus
from app.models.attendance import Attendance, AttendanceStatus
from app.models.department import Department
from app.models.leave import Leave, LeaveStatus
from app.models.audit_log import AuditLog
from app.schemas.dashboard import (
    DashboardSummary,
    DepartmentAttendanceStat,
    AttendanceTrendPoint,
    RecentActivityItem,
    DashboardData
)
from app.schemas.leave import LeaveResponse
from app.core.timezone import get_current_date


class DashboardService:
    @staticmethod
    def get_dashboard_data(db: Session, target_date: Optional[date] = None) -> DashboardData:
        """Fetch all aggregated metrics, trend points, department stats, and recent activities."""
        today = target_date or get_current_date()

        # 1. Total and Active Employees
        total_employees = db.query(Employee).filter(Employee.deleted_at.is_(None)).count()
        active_employees = db.query(Employee).filter(
            Employee.deleted_at.is_(None),
            Employee.status == EmployeeStatus.ACTIVE
        ).count()

        # 2. Today's attendance counts
        records = db.query(Attendance).join(Employee).filter(
            Attendance.attendance_date == today,
            Employee.deleted_at.is_(None),
            Employee.status == EmployeeStatus.ACTIVE
        ).all()

        present_count = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
        absent_count = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
        leave_count = sum(1 for r in records if r.status == AttendanceStatus.LEAVE)
        week_off_count = sum(1 for r in records if r.status == AttendanceStatus.WEEK_OFF)
        half_day_count = sum(1 for r in records if r.status == AttendanceStatus.HALF_DAY)
        holiday_count = sum(1 for r in records if r.status == AttendanceStatus.HOLIDAY)
        wfh_count = sum(1 for r in records if r.status == AttendanceStatus.WORK_FROM_HOME)

        marked_total = len(records)
        unmarked_count = max(0, active_employees - marked_total)

        effective_present = present_count + wfh_count + (half_day_count * 0.5)
        # Working pool excludes week off and holiday
        working_pool = max(1, active_employees - (week_off_count + holiday_count))
        attendance_rate = round((effective_present / working_pool * 100), 1) if marked_total > 0 else 0.0

        summary = DashboardSummary(
            total_employees=total_employees,
            active_employees=active_employees,
            present_today=present_count,
            absent_today=absent_count,
            leave_today=leave_count,
            week_off_today=week_off_count,
            half_day_today=half_day_count,
            holiday_today=holiday_count,
            wfh_today=wfh_count,
            unmarked_today=unmarked_count,
            attendance_rate=min(100.0, attendance_rate),
            selected_date=today
        )

        # 3. Last 7 Days Trend
        trends = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            d_records = db.query(Attendance).join(Employee).filter(
                Attendance.attendance_date == d,
                Employee.deleted_at.is_(None),
                Employee.status == EmployeeStatus.ACTIVE
            ).all()

            p = sum(1 for r in d_records if r.status in [AttendanceStatus.PRESENT, AttendanceStatus.WORK_FROM_HOME])
            ab = sum(1 for r in d_records if r.status == AttendanceStatus.ABSENT)
            lv = sum(1 for r in d_records if r.status == AttendanceStatus.LEAVE)
            hd = sum(1 for r in d_records if r.status == AttendanceStatus.HALF_DAY)

            eff_p = p + (hd * 0.5)
            d_total = len(d_records)
            rate = round((eff_p / d_total * 100), 1) if d_total > 0 else 0.0

            trends.append(
                AttendanceTrendPoint(
                    date=d,
                    formatted_date=d.strftime("%b %d"),
                    present=p + hd,
                    absent=ab,
                    leave=lv,
                    attendance_rate=rate
                )
            )

        # 4. Department breakdown
        dept_stats = []
        departments = db.query(Department).filter(Department.is_active.is_(True)).all()
        for dept in departments:
            dept_active_emps = db.query(Employee).filter(
                Employee.department_id == dept.id,
                Employee.deleted_at.is_(None),
                Employee.status == EmployeeStatus.ACTIVE
            ).count()

            if dept_active_emps == 0:
                continue

            dept_records = db.query(Attendance).join(Employee).filter(
                Attendance.attendance_date == today,
                Employee.department_id == dept.id,
                Employee.deleted_at.is_(None),
                Employee.status == EmployeeStatus.ACTIVE
            ).all()

            d_pres = sum(1 for r in dept_records if r.status in [AttendanceStatus.PRESENT, AttendanceStatus.WORK_FROM_HOME, AttendanceStatus.HALF_DAY])
            d_abs = sum(1 for r in dept_records if r.status == AttendanceStatus.ABSENT)
            d_lv = sum(1 for r in dept_records if r.status == AttendanceStatus.LEAVE)
            d_rate = round((d_pres / dept_active_emps * 100), 1) if dept_records else 0.0

            dept_stats.append(
                DepartmentAttendanceStat(
                    department_id=dept.id,
                    department_name=dept.name,
                    total_employees=dept_active_emps,
                    present=d_pres,
                    absent=d_abs,
                    leave=d_lv,
                    attendance_rate=d_rate
                )
            )

        # 5. Pending Leaves
        pending_leaves_db = db.query(Leave).filter(
            Leave.status == LeaveStatus.PENDING
        ).order_by(Leave.created_at.desc()).limit(5).all()

        pending_leaves = [
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
                created_at=l.created_at,
                updated_at=l.updated_at
            )
            for l in pending_leaves_db
        ]

        # 6. Recent Activity
        recent_logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(8).all()
        recent_activities = [
            RecentActivityItem(
                id=log.id,
                action=log.action,
                description=log.description,
                user_name=log.user.full_name if log.user else "System",
                timestamp=log.timestamp.strftime("%Y-%m-%d %H:%M")
            )
            for log in recent_logs
        ]

        return DashboardData(
            summary=summary,
            trends=trends,
            department_stats=dept_stats,
            pending_leaves=pending_leaves,
            recent_activities=recent_activities
        )
