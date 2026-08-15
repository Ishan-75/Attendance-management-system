from datetime import datetime, date, timedelta, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.leave import Leave, LeaveStatus
from app.models.employee import Employee
from app.models.attendance import Attendance, AttendanceStatus
from app.models.holiday import Holiday
from app.models.setting import Setting
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.leave import LeaveCreate, LeaveUpdate, LeaveDecision
from app.services.audit_service import AuditService


class LeaveService:
    @staticmethod
    def get_leaves(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        employee_id: Optional[int] = None,
        department_id: Optional[int] = None,
        status_filter: Optional[str] = None
    ) -> Tuple[List[Leave], int]:
        """Fetch list of leave requests with filters."""
        query = db.query(Leave).join(Employee)

        if employee_id:
            query = query.filter(Leave.employee_id == employee_id)

        if department_id:
            query = query.filter(Employee.department_id == department_id)

        if status_filter:
            query = query.filter(Leave.status == status_filter)

        total = query.count()
        items = query.order_by(Leave.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def get_leave_by_id(db: Session, leave_id: int) -> Leave:
        leave = db.query(Leave).filter(Leave.id == leave_id).first()
        if not leave:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
        return leave

    @staticmethod
    def apply_leave(
        db: Session,
        leave_in: LeaveCreate,
        user: Optional[User] = None,
        ip_address: Optional[str] = None
    ) -> Leave:
        """Create a new leave request."""
        # 1. Verify employee
        employee = db.query(Employee).filter(
            Employee.id == leave_in.employee_id,
            Employee.deleted_at.is_(None)
        ).first()
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

        # 2. Date validation
        if leave_in.end_date < leave_in.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date cannot be earlier than start date."
            )

        # 3. Check for overlapping approved/pending leaves
        overlapping = db.query(Leave).filter(
            Leave.employee_id == leave_in.employee_id,
            Leave.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED]),
            Leave.start_date <= leave_in.end_date,
            Leave.end_date >= leave_in.start_date
        ).first()

        if overlapping:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A leave request already exists covering this date range ({overlapping.start_date} to {overlapping.end_date})"
            )

        new_leave = Leave(
            employee_id=leave_in.employee_id,
            leave_type=leave_in.leave_type,
            start_date=leave_in.start_date,
            end_date=leave_in.end_date,
            number_of_days=leave_in.number_of_days,
            reason=leave_in.reason,
            status=LeaveStatus.PENDING
        )

        db.add(new_leave)
        db.flush()

        AuditService.log(
            db,
            action=AuditAction.LEAVE_APPLIED,
            description=f"Leave applied for {employee.full_name}: {leave_in.leave_type} ({leave_in.start_date} to {leave_in.end_date}, {leave_in.number_of_days} days)",
            user_id=user.id if user else None,
            entity_type="Leave",
            entity_id=str(new_leave.id),
            new_value={"start_date": str(leave_in.start_date), "end_date": str(leave_in.end_date), "type": leave_in.leave_type},
            ip_address=ip_address
        )

        db.commit()
        db.refresh(new_leave)
        return new_leave

    @staticmethod
    def approve_leave(
        db: Session,
        leave_id: int,
        user: User,
        decision: Optional[LeaveDecision] = None,
        ip_address: Optional[str] = None
    ) -> Leave:
        """
        Approve leave request and automatically synchronize attendance records.
        """
        leave = LeaveService.get_leave_by_id(db, leave_id)
        if leave.status != LeaveStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve leave that is already {leave.status}"
            )

        now = datetime.now(timezone.utc)
        leave.status = LeaveStatus.APPROVED
        leave.approved_by = user.id
        leave.approved_at = now

        # Automatically update/create attendance records for all dates in the range
        curr_d = leave.start_date
        while curr_d <= leave.end_date:
            existing_att = db.query(Attendance).filter(
                Attendance.employee_id == leave.employee_id,
                Attendance.attendance_date == curr_d
            ).first()

            if existing_att:
                existing_att.status = AttendanceStatus.LEAVE
                existing_att.check_in_time = None
                existing_att.check_out_time = None
                existing_att.total_hours = 0.0
                existing_att.overtime_hours = 0.0
                existing_att.remarks = f"Approved {leave.leave_type} Leave"
                existing_att.marked_by = user.id
            else:
                new_att = Attendance(
                    employee_id=leave.employee_id,
                    attendance_date=curr_d,
                    status=AttendanceStatus.LEAVE,
                    check_in_time=None,
                    check_out_time=None,
                    total_hours=0.0,
                    overtime_hours=0.0,
                    remarks=f"Approved {leave.leave_type} Leave",
                    marked_by=user.id
                )
                db.add(new_att)

            curr_d += timedelta(days=1)

        db.flush()

        employee = leave.employee
        AuditService.log(
            db,
            action=AuditAction.LEAVE_APPROVED,
            description=f"Approved {leave.leave_type} leave for {employee.full_name} ({leave.start_date} to {leave.end_date})",
            user_id=user.id,
            entity_type="Leave",
            entity_id=str(leave.id),
            new_value={"status": "APPROVED", "approver": user.username},
            ip_address=ip_address
        )

        db.commit()
        db.refresh(leave)
        return leave

    @staticmethod
    def reject_leave(
        db: Session,
        leave_id: int,
        user: User,
        decision: LeaveDecision,
        ip_address: Optional[str] = None
    ) -> Leave:
        """Reject a leave request with a mandatory or optional reason."""
        leave = LeaveService.get_leave_by_id(db, leave_id)
        if leave.status != LeaveStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reject leave that is already {leave.status}"
            )

        now = datetime.now(timezone.utc)
        leave.status = LeaveStatus.REJECTED
        leave.approved_by = user.id
        leave.approved_at = now
        leave.rejection_reason = decision.reason or "Rejected by manager"

        employee = leave.employee
        AuditService.log(
            db,
            action=AuditAction.LEAVE_REJECTED,
            description=f"Rejected {leave.leave_type} leave for {employee.full_name}. Reason: {leave.rejection_reason}",
            user_id=user.id,
            entity_type="Leave",
            entity_id=str(leave.id),
            new_value={"status": "REJECTED", "reason": leave.rejection_reason},
            ip_address=ip_address
        )

        db.commit()
        db.refresh(leave)
        return leave
