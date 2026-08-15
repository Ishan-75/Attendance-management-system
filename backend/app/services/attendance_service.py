from datetime import date, time, datetime, timedelta, timezone
import calendar
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status
from app.models.attendance import Attendance, AttendanceStatus
from app.models.employee import Employee, EmployeeStatus
from app.models.department import Department
from app.models.holiday import Holiday
from app.models.leave import Leave, LeaveStatus
from app.models.setting import Setting
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceBulkCreate,
    AttendanceCorrection,
    AttendanceSheetItem,
    EmployeeMonthlyCalendarResponse,
    AttendanceDayCalendar,
    AttendanceResponse
)
from app.services.audit_service import AuditService
from app.core.timezone import get_current_date


class AttendanceService:
    @staticmethod
    def get_setting_value(db: Session, key: str, default: str) -> str:
        s = db.query(Setting).filter(Setting.key == key).first()
        return s.value if s else default

    @staticmethod
    def calculate_hours_and_metrics(
        db: Session,
        check_in: Optional[time],
        check_out: Optional[time],
        status_val: str
    ) -> Tuple[float, float, int, int]:
        """
        Calculate total hours, overtime hours, late minutes, and early departure minutes.
        Returns: (total_hours, overtime_hours, late_minutes, early_departure_minutes)
        """
        if status_val not in [AttendanceStatus.PRESENT, AttendanceStatus.HALF_DAY, AttendanceStatus.WORK_FROM_HOME]:
            return 0.0, 0.0, 0, 0

        if not check_in or not check_out:
            default_hours = 8.0 if status_val in [AttendanceStatus.PRESENT, AttendanceStatus.WORK_FROM_HOME] else (4.0 if status_val == AttendanceStatus.HALF_DAY else 0.0)
            return default_hours, 0.0, 0, 0

        # Retrieve system settings
        work_start_str = AttendanceService.get_setting_value(db, "work_start_time", "09:00")
        work_end_str = AttendanceService.get_setting_value(db, "work_end_time", "18:00")
        break_mins = int(AttendanceService.get_setting_value(db, "break_duration_minutes", "60"))
        standard_work_hours = float(AttendanceService.get_setting_value(db, "work_hours_per_day", "8.0"))
        grace_mins = int(AttendanceService.get_setting_value(db, "late_grace_period_minutes", "15"))

        # Convert times to minutes from midnight for easy math
        in_minutes = check_in.hour * 60 + check_in.minute
        out_minutes = check_out.hour * 60 + check_out.minute

        start_h, start_m = map(int, work_start_str.split(":"))
        end_h, end_m = map(int, work_end_str.split(":"))
        std_start_minutes = start_h * 60 + start_m
        std_end_minutes = end_h * 60 + end_m

        if out_minutes < in_minutes:
            # Shift spans midnight or invalid
            duration_minutes = (24 * 60 - in_minutes) + out_minutes
        else:
            duration_minutes = out_minutes - in_minutes

        # Deduct break time if worked more than 4 hours
        net_worked_minutes = max(0, duration_minutes - (break_mins if duration_minutes > 240 else 0))
        total_hours = round(net_worked_minutes / 60.0, 2)

        # Overtime
        overtime_hours = max(0.0, round(total_hours - standard_work_hours, 2))

        # Late arrival
        late_minutes = 0
        if in_minutes > (std_start_minutes + grace_mins):
            late_minutes = in_minutes - std_start_minutes

        # Early departure
        early_departure_minutes = 0
        if out_minutes < std_end_minutes:
            early_departure_minutes = std_end_minutes - out_minutes

        return total_hours, overtime_hours, late_minutes, early_departure_minutes

    @staticmethod
    def get_attendance_sheet(
        db: Session,
        attendance_date: date,
        department_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[AttendanceSheetItem]:
        """
        Fetch attendance marking sheet for all active employees on a specific date.
        Integrates approved leaves, existing attendance records, and active departments.
        """
        # 1. Fetch active employees
        emp_query = db.query(Employee).filter(
            Employee.deleted_at.is_(None),
            Employee.status == EmployeeStatus.ACTIVE
        )

        if department_id:
            emp_query = emp_query.filter(Employee.department_id == department_id)

        if search:
            search_term = f"%{search.strip()}%"
            emp_query = emp_query.filter(
                or_(
                    Employee.full_name.ilike(search_term),
                    Employee.employee_id.ilike(search_term)
                )
            )

        employees = emp_query.order_by(Employee.employee_id.asc()).all()

        # 2. Check if the date is a holiday or weekend
        holiday = db.query(Holiday).filter(Holiday.date == attendance_date, Holiday.is_active.is_(True)).first()
        day_name = calendar.day_name[attendance_date.weekday()]
        weekly_offs = AttendanceService.get_setting_value(db, "weekly_off_days", "Saturday,Sunday").split(",")
        is_weekend = day_name in [d.strip() for d in weekly_offs]

        # 3. Fetch existing attendance records for this date
        emp_ids = [e.id for e in employees]
        existing_records = {
            att.employee_id: att
            for att in db.query(Attendance).filter(
                Attendance.attendance_date == attendance_date,
                Attendance.employee_id.in_(emp_ids)
            ).all()
        }

        # 4. Fetch approved leaves covering this date
        approved_leaves = {
            leave.employee_id: leave
            for leave in db.query(Leave).filter(
                Leave.status == LeaveStatus.APPROVED,
                Leave.start_date <= attendance_date,
                Leave.end_date >= attendance_date,
                Leave.employee_id.in_(emp_ids)
            ).all()
        }

        sheet_items = []
        for emp in employees:
            att = existing_records.get(emp.id)
            leave = approved_leaves.get(emp.id)

            if att:
                # Record already exists
                sheet_items.append(
                    AttendanceSheetItem(
                        employee_id=emp.id,
                        employee_code=emp.employee_id,
                        full_name=emp.full_name,
                        department_name=emp.department.name if emp.department else "Unassigned",
                        designation=emp.designation,
                        attendance_id=att.id,
                        status=att.status,
                        check_in_time=att.check_in_time,
                        check_out_time=att.check_out_time,
                        total_hours=att.total_hours,
                        overtime_hours=att.overtime_hours,
                        remarks=att.remarks,
                        is_marked=True
                    )
                )
            elif leave:
                # Has approved leave
                sheet_items.append(
                    AttendanceSheetItem(
                        employee_id=emp.id,
                        employee_code=emp.employee_id,
                        full_name=emp.full_name,
                        department_name=emp.department.name if emp.department else "Unassigned",
                        designation=emp.designation,
                        attendance_id=None,
                        status=AttendanceStatus.LEAVE,
                        check_in_time=None,
                        check_out_time=None,
                        total_hours=0.0,
                        overtime_hours=0.0,
                        remarks=f"Approved {leave.leave_type} Leave",
                        is_marked=False
                    )
                )
            elif holiday:
                sheet_items.append(
                    AttendanceSheetItem(
                        employee_id=emp.id,
                        employee_code=emp.employee_id,
                        full_name=emp.full_name,
                        department_name=emp.department.name if emp.department else "Unassigned",
                        designation=emp.designation,
                        attendance_id=None,
                        status=AttendanceStatus.HOLIDAY,
                        check_in_time=None,
                        check_out_time=None,
                        total_hours=0.0,
                        overtime_hours=0.0,
                        remarks=f"Holiday: {holiday.name}",
                        is_marked=False
                    )
                )
            elif is_weekend:
                sheet_items.append(
                    AttendanceSheetItem(
                        employee_id=emp.id,
                        employee_code=emp.employee_id,
                        full_name=emp.full_name,
                        department_name=emp.department.name if emp.department else "Unassigned",
                        designation=emp.designation,
                        attendance_id=None,
                        status=AttendanceStatus.WEEK_OFF,
                        check_in_time=None,
                        check_out_time=None,
                        total_hours=0.0,
                        overtime_hours=0.0,
                        remarks="Weekly Off",
                        is_marked=False
                    )
                )
            else:
                # Default unmarked
                sheet_items.append(
                    AttendanceSheetItem(
                        employee_id=emp.id,
                        employee_code=emp.employee_id,
                        full_name=emp.full_name,
                        department_name=emp.department.name if emp.department else "Unassigned",
                        designation=emp.designation,
                        attendance_id=None,
                        status=AttendanceStatus.PRESENT,
                        check_in_time=time(9, 0),
                        check_out_time=time(18, 0),
                        total_hours=8.0,
                        overtime_hours=0.0,
                        remarks=None,
                        is_marked=False
                    )
                )

        return sheet_items

    @staticmethod
    def mark_single_attendance(
        db: Session,
        att_in: AttendanceCreate,
        user: User,
        ip_address: Optional[str] = None
    ) -> Attendance:
        """Mark single attendance record with unique constraint validation."""
        # 1. Verify employee exists
        employee = db.query(Employee).filter(
            Employee.id == att_in.employee_id,
            Employee.deleted_at.is_(None)
        ).first()
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

        # 2. Check if record already exists
        existing = db.query(Attendance).filter(
            Attendance.employee_id == att_in.employee_id,
            Attendance.attendance_date == att_in.attendance_date
        ).first()

        total_hours, overtime_hours, late_mins, early_mins = AttendanceService.calculate_hours_and_metrics(
            db, att_in.check_in_time, att_in.check_out_time, att_in.status
        )

        if existing:
            # Update existing
            existing.status = att_in.status
            existing.check_in_time = att_in.check_in_time
            existing.check_out_time = att_in.check_out_time
            existing.total_hours = total_hours
            existing.overtime_hours = overtime_hours
            existing.late_minutes = late_mins
            existing.early_departure_minutes = early_mins
            existing.remarks = att_in.remarks
            existing.marked_by = user.id
            record = existing
        else:
            # Create new
            record = Attendance(
                employee_id=att_in.employee_id,
                attendance_date=att_in.attendance_date,
                status=att_in.status,
                check_in_time=att_in.check_in_time,
                check_out_time=att_in.check_out_time,
                total_hours=total_hours,
                overtime_hours=overtime_hours,
                late_minutes=late_mins,
                early_departure_minutes=early_mins,
                remarks=att_in.remarks,
                marked_by=user.id
            )
            db.add(record)

        db.flush()

        AuditService.log(
            db,
            action=AuditAction.ATTENDANCE_CREATED if not existing else AuditAction.ATTENDANCE_UPDATED,
            description=f"Marked attendance for {employee.full_name} ({employee.employee_id}) on {att_in.attendance_date} as {att_in.status}",
            user_id=user.id,
            entity_type="Attendance",
            entity_id=str(record.id),
            new_value={"date": str(att_in.attendance_date), "status": att_in.status, "hours": total_hours},
            ip_address=ip_address
        )

        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def mark_bulk_attendance(
        db: Session,
        bulk_in: AttendanceBulkCreate,
        user: User,
        ip_address: Optional[str] = None
    ) -> List[Attendance]:
        """
        Mark attendance for multiple employees in an atomic transaction.
        Rolls back completely if any error occurs.
        """
        try:
            results = []
            att_date = bulk_in.attendance_date
            marked_count = 0

            for item in bulk_in.records:
                employee = db.query(Employee).filter(
                    Employee.id == item.employee_id,
                    Employee.deleted_at.is_(None)
                ).first()

                if not employee:
                    continue

                total_hours, overtime_hours, late_mins, early_mins = AttendanceService.calculate_hours_and_metrics(
                    db, item.check_in_time, item.check_out_time, item.status
                )

                existing = db.query(Attendance).filter(
                    Attendance.employee_id == item.employee_id,
                    Attendance.attendance_date == att_date
                ).first()

                if existing:
                    existing.status = item.status
                    existing.check_in_time = item.check_in_time
                    existing.check_out_time = item.check_out_time
                    existing.total_hours = total_hours
                    existing.overtime_hours = overtime_hours
                    existing.late_minutes = late_mins
                    existing.early_departure_minutes = early_mins
                    existing.remarks = item.remarks
                    existing.marked_by = user.id
                    results.append(existing)
                else:
                    new_att = Attendance(
                        employee_id=item.employee_id,
                        attendance_date=att_date,
                        status=item.status,
                        check_in_time=item.check_in_time,
                        check_out_time=item.check_out_time,
                        total_hours=total_hours,
                        overtime_hours=overtime_hours,
                        late_minutes=late_mins,
                        early_departure_minutes=early_mins,
                        remarks=item.remarks,
                        marked_by=user.id
                    )
                    db.add(new_att)
                    results.append(new_att)

                marked_count += 1

            db.flush()

            AuditService.log(
                db,
                action=AuditAction.ATTENDANCE_CREATED,
                description=f"Bulk attendance marked for {marked_count} employees on {att_date}",
                user_id=user.id,
                entity_type="Attendance",
                new_value={"date": str(att_date), "marked_count": marked_count},
                ip_address=ip_address
            )

            db.commit()
            return results
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save bulk attendance: {str(e)}"
            )

    @staticmethod
    def correct_attendance(
        db: Session,
        attendance_id: int,
        correction: AttendanceCorrection,
        user: User,
        ip_address: Optional[str] = None
    ) -> Attendance:
        """
        Correct an existing attendance record with a mandatory reason.
        Audits old status, new status, reason, manager, and timestamp.
        """
        att = db.query(Attendance).filter(Attendance.id == attendance_id).first()
        if not att:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found")

        old_data = {
            "status": att.status,
            "check_in": str(att.check_in_time) if att.check_in_time else None,
            "check_out": str(att.check_out_time) if att.check_out_time else None,
            "total_hours": att.total_hours,
            "remarks": att.remarks
        }

        total_hours, overtime_hours, late_mins, early_mins = AttendanceService.calculate_hours_and_metrics(
            db, correction.check_in_time, correction.check_out_time, correction.status
        )

        att.status = correction.status
        att.check_in_time = correction.check_in_time
        att.check_out_time = correction.check_out_time
        att.total_hours = total_hours
        att.overtime_hours = overtime_hours
        att.late_minutes = late_mins
        att.early_departure_minutes = early_mins
        att.remarks = f"[Corrected: {correction.reason}] " + (correction.remarks or "")
        att.marked_by = user.id

        new_data = {
            "status": att.status,
            "check_in": str(att.check_in_time) if att.check_in_time else None,
            "check_out": str(att.check_out_time) if att.check_out_time else None,
            "total_hours": att.total_hours,
            "reason": correction.reason
        }

        employee = att.employee
        AuditService.log(
            db,
            action=AuditAction.ATTENDANCE_CORRECTED,
            description=f"Attendance corrected for {employee.full_name} on {att.attendance_date}: {old_data['status']} -> {new_data['status']}. Reason: {correction.reason}",
            user_id=user.id,
            entity_type="Attendance",
            entity_id=str(att.id),
            old_value=old_data,
            new_value=new_data,
            ip_address=ip_address
        )

        db.commit()
        db.refresh(att)
        return att

    @staticmethod
    def get_employee_monthly_calendar(
        db: Session,
        employee_id: int,
        year: int,
        month: int
    ) -> EmployeeMonthlyCalendarResponse:
        """Generate monthly attendance summary and day-by-day calendar data for an employee."""
        employee = db.query(Employee).filter(
            Employee.id == employee_id,
            Employee.deleted_at.is_(None)
        ).first()
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

        num_days = calendar.monthrange(year, month)[1]
        start_date = date(year, month, 1)
        end_date = date(year, month, num_days)

        # Query attendance records
        records = db.query(Attendance).filter(
            Attendance.employee_id == employee_id,
            Attendance.attendance_date >= start_date,
            Attendance.attendance_date <= end_date
        ).all()
        record_map = {r.attendance_date: r for r in records}

        # Query holidays
        holidays = db.query(Holiday).filter(
            Holiday.date >= start_date,
            Holiday.date <= end_date,
            Holiday.is_active.is_(True)
        ).all()
        holiday_map = {h.date: h.name for h in holidays}

        # System settings for weekends
        weekly_offs = [d.strip() for d in AttendanceService.get_setting_value(db, "weekly_off_days", "Saturday,Sunday").split(",")]

        # Metrics accumulators
        present_days = 0
        absent_days = 0
        leave_days = 0
        week_off_days = 0
        half_days = 0
        holiday_days = 0
        wfh_days = 0
        total_hours = 0.0
        total_overtime = 0.0
        working_days_count = 0

        calendar_days = []
        today = get_current_date()

        for day in range(1, num_days + 1):
            curr_date = date(year, month, day)
            day_name = calendar.day_name[curr_date.weekday()]
            is_weekend = day_name in weekly_offs
            is_hol = curr_date in holiday_map

            if not is_weekend and not is_hol:
                working_days_count += 1

            att = record_map.get(curr_date)

            if att:
                status_str = att.status
                c_in = att.check_in_time
                c_out = att.check_out_time
                hrs = att.total_hours
                ot = att.overtime_hours
                rem = att.remarks

                if status_str == AttendanceStatus.PRESENT:
                    present_days += 1
                elif status_str == AttendanceStatus.ABSENT:
                    absent_days += 1
                elif status_str == AttendanceStatus.LEAVE:
                    leave_days += 1
                elif status_str == AttendanceStatus.WEEK_OFF:
                    week_off_days += 1
                elif status_str == AttendanceStatus.HALF_DAY:
                    half_days += 1
                elif status_str == AttendanceStatus.HOLIDAY:
                    holiday_days += 1
                elif status_str == AttendanceStatus.WORK_FROM_HOME:
                    wfh_days += 1

                total_hours += hrs
                total_overtime += ot
            else:
                # Unrecorded day
                if is_hol:
                    status_str = AttendanceStatus.HOLIDAY
                    holiday_days += 1
                elif is_weekend:
                    status_str = AttendanceStatus.WEEK_OFF
                    week_off_days += 1
                elif curr_date < today:
                    status_str = AttendanceStatus.ABSENT
                    absent_days += 1
                else:
                    status_str = None

                c_in, c_out, hrs, ot, rem = None, None, 0.0, 0.0, None

            calendar_days.append(
                AttendanceDayCalendar(
                    date=curr_date,
                    status=status_str,
                    check_in_time=c_in,
                    check_out_time=c_out,
                    total_hours=hrs,
                    overtime_hours=ot,
                    is_holiday=is_hol,
                    holiday_name=holiday_map.get(curr_date),
                    is_weekend=is_weekend,
                    remarks=rem
                )
            )

        # Calculate attendance percentage
        effective_present = present_days + wfh_days + (half_days * 0.5)
        att_percentage = round((effective_present / working_days_count * 100), 2) if working_days_count > 0 else 100.0

        return EmployeeMonthlyCalendarResponse(
            employee_id=employee.id,
            employee_code=employee.employee_id,
            employee_name=employee.full_name,
            year=year,
            month=month,
            total_working_days=working_days_count,
            present_days=present_days,
            absent_days=absent_days,
            leave_days=leave_days,
            week_off_days=week_off_days,
            half_days=half_days,
            holiday_days=holiday_days,
            work_from_home_days=wfh_days,
            total_hours_worked=round(total_hours, 2),
            total_overtime_hours=round(total_overtime, 2),
            attendance_percentage=att_percentage,
            calendar_days=calendar_days
        )
