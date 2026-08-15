import json
import uuid
from datetime import datetime, timezone, date, time
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from fastapi import HTTPException, status

from app.models.sync import Device, SyncOperation, SyncConflict
from app.models.employee import Employee, EmployeeStatus
from app.models.attendance import Attendance, AttendanceStatus
from app.models.leave import Leave, LeaveStatus
from app.models.department import Department
from app.models.holiday import Holiday
from app.models.user import User
from app.models.audit_log import AuditAction
from app.services.audit_service import AuditService
from app.services.attendance_service import AttendanceService


class SyncService:
    @staticmethod
    def register_or_heartbeat_device(
        db: Session,
        device_id: str,
        device_name: str,
        platform: str = "android",
        app_version: Optional[str] = "1.0.0",
        user: Optional[User] = None
    ) -> Device:
        """Register a new device installation or update last synchronization heartbeat."""
        device = db.query(Device).filter(Device.device_id == device_id).first()
        now = datetime.now(timezone.utc)

        if not device:
            device = Device(
                device_id=device_id,
                user_id=user.id if user else None,
                device_name=device_name,
                platform=platform,
                app_version=app_version,
                last_sync_at=now,
                is_active=True,
                created_at=now
            )
            db.add(device)
        else:
            device.device_name = device_name
            device.platform = platform
            if app_version:
                device.app_version = app_version
            if user:
                device.user_id = user.id
            device.last_sync_at = now

        db.commit()
        db.refresh(device)
        return device

    @staticmethod
    def get_registered_devices(db: Session) -> List[Device]:
        """Returns all registered devices."""
        return db.query(Device).order_by(Device.last_sync_at.desc().nullslast()).all()

    @staticmethod
    def push_sync_batch(
        db: Session,
        device_id: str,
        operations: List[Dict[str, Any]],
        user: User,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a batch of sync operations idempotently.
        Ensures duplicate operation_ids are ignored and conflicts are safely logged.
        """
        processed_count = 0
        skipped_count = 0
        conflicts_created = 0
        results = []

        # Heartbeat device
        SyncService.register_or_heartbeat_device(db, device_id, device_name=f"Device {device_id[:8]}", user=user)

        for op_data in operations:
            op_id = op_data.get("operation_id")
            if not op_id:
                op_id = str(uuid.uuid4())

            # 1. Idempotency check
            existing_op = db.query(SyncOperation).filter(SyncOperation.operation_id == op_id).first()
            if existing_op:
                skipped_count += 1
                results.append({
                    "operation_id": op_id,
                    "status": existing_op.status,
                    "message": "Already processed (idempotent skip)"
                })
                continue

            entity_type = op_data.get("entity_type")
            entity_id = str(op_data.get("entity_id") or "")
            action = op_data.get("operation", "CREATE").upper()
            payload = op_data.get("payload", {})

            try:
                if entity_type == "Attendance":
                    op_status, conflict_record = SyncService._sync_attendance(
                        db, device_id, action, payload, user, ip_address
                    )
                elif entity_type == "Leave":
                    op_status, conflict_record = SyncService._sync_leave(
                        db, device_id, action, payload, user, ip_address
                    )
                elif entity_type == "Employee":
                    op_status, conflict_record = SyncService._sync_employee(
                        db, device_id, action, payload, user, ip_address
                    )
                else:
                    op_status = "PROCESSED"
                    conflict_record = None

                # Log sync operation for idempotency
                sync_op = SyncOperation(
                    operation_id=op_id,
                    device_id=device_id,
                    user_id=user.id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    operation=action,
                    status=op_status,
                    processed_at=datetime.now(timezone.utc)
                )
                db.add(sync_op)
                db.commit()

                if op_status == "CONFLICT":
                    conflicts_created += 1
                    results.append({
                        "operation_id": op_id,
                        "status": "CONFLICT",
                        "conflict_id": conflict_record.conflict_id if conflict_record else None,
                        "message": "Conflict detected and preserved for manual review"
                    })
                else:
                    processed_count += 1
                    results.append({
                        "operation_id": op_id,
                        "status": "PROCESSED",
                        "message": "Synchronized successfully"
                    })

            except Exception as e:
                db.rollback()
                sync_op = SyncOperation(
                    operation_id=op_id,
                    device_id=device_id,
                    user_id=user.id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    operation=action,
                    status="FAILED",
                    error_message=str(e),
                    processed_at=datetime.now(timezone.utc)
                )
                db.add(sync_op)
                db.commit()
                results.append({
                    "operation_id": op_id,
                    "status": "FAILED",
                    "error": str(e)
                })

        return {
            "processed": processed_count,
            "skipped": skipped_count,
            "conflicts": conflicts_created,
            "total": len(operations),
            "results": results
        }

    @staticmethod
    def _sync_attendance(
        db: Session,
        device_id: str,
        action: str,
        payload: Dict[str, Any],
        user: User,
        ip_address: Optional[str]
    ) -> Tuple[str, Optional[SyncConflict]]:
        """Handles attendance synchronization with strict conflict detection."""
        emp_id = payload.get("employee_id")
        att_date_str = payload.get("attendance_date")
        if isinstance(att_date_str, str):
            att_date = datetime.strptime(att_date_str, "%Y-%m-%d").date()
        else:
            att_date = att_date_str

        # Check existing attendance record on server
        existing_att = db.query(Attendance).filter(
            Attendance.employee_id == emp_id,
            Attendance.attendance_date == att_date
        ).first()

        client_status = payload.get("status", "PRESENT")

        if existing_att:
            # Check if server state conflicts with incoming offline state
            if existing_att.status != client_status:
                # Concurrent conflict: Device A set PRESENT, Device B set ABSENT, etc.
                server_dict = {
                    "id": existing_att.id,
                    "employee_id": existing_att.employee_id,
                    "attendance_date": str(existing_att.attendance_date),
                    "status": existing_att.status,
                    "total_hours": existing_att.total_hours,
                    "check_in": str(existing_att.check_in_time) if existing_att.check_in_time else None,
                    "check_out": str(existing_att.check_out_time) if existing_att.check_out_time else None,
                    "updated_at": existing_att.updated_at.isoformat() if existing_att.updated_at else None
                }
                conflict = SyncConflict(
                    entity_type="Attendance",
                    entity_id=f"{emp_id}:{att_date}",
                    device_id=device_id,
                    user_id=user.id,
                    server_payload=json.dumps(server_dict),
                    client_payload=json.dumps(payload),
                    conflict_reason=f"Concurrent status discrepancy: Server has '{existing_att.status}' while Device '{device_id[:8]}' pushed '{client_status}'",
                    status="PENDING",
                    created_at=datetime.now(timezone.utc)
                )
                db.add(conflict)
                db.flush()
                return "CONFLICT", conflict

            # No conflicting status - update times / remarks cleanly
            existing_att.remarks = payload.get("remarks") or existing_att.remarks
            db.flush()
            return "PROCESSED", None

        # Clean insert
        new_att = Attendance(
            employee_id=emp_id,
            attendance_date=att_date,
            status=client_status,
            remarks=payload.get("remarks"),
            marked_by=user.id
        )
        if payload.get("check_in_time"):
            t_str = str(payload.get("check_in_time"))[:5]
            new_att.check_in_time = datetime.strptime(t_str, "%H:%M").time()
        if payload.get("check_out_time"):
            t_str = str(payload.get("check_out_time"))[:5]
            new_att.check_out_time = datetime.strptime(t_str, "%H:%M").time()

        if new_att.check_in_time and new_att.check_out_time:
            hours, ot, late, early = AttendanceService.calculate_hours_and_metrics(
                db, new_att.check_in_time, new_att.check_out_time, client_status
            )
            new_att.total_hours = hours
            new_att.overtime_hours = ot
            new_att.late_minutes = late
            new_att.early_departure_minutes = early

        db.add(new_att)
        db.flush()

        AuditService.log(
            db,
            action=AuditAction.ATTENDANCE_CREATED,
            description=f"Offline-synced attendance for employee #{emp_id} on {att_date} as {client_status} from device {device_id[:8]}",
            user_id=user.id,
            entity_type="Attendance",
            entity_id=str(new_att.id),
            ip_address=ip_address
        )
        return "PROCESSED", None

    @staticmethod
    def _sync_leave(
        db: Session,
        device_id: str,
        action: str,
        payload: Dict[str, Any],
        user: User,
        ip_address: Optional[str]
    ) -> Tuple[str, Optional[SyncConflict]]:
        emp_id = payload.get("employee_id")
        start_d = payload.get("start_date")
        end_d = payload.get("end_date")
        
        new_leave = Leave(
            employee_id=emp_id,
            leave_type=payload.get("leave_type", "CASUAL"),
            start_date=datetime.strptime(str(start_d), "%Y-%m-%d").date() if isinstance(start_d, str) else start_d,
            end_date=datetime.strptime(str(end_d), "%Y-%m-%d").date() if isinstance(end_d, str) else end_d,
            number_of_days=float(payload.get("number_of_days", 1.0)),
            reason=payload.get("reason", "Applied via offline sync"),
            status=payload.get("status", "PENDING")
        )
        db.add(new_leave)
        db.flush()
        return "PROCESSED", None

    @staticmethod
    def _sync_employee(
        db: Session,
        device_id: str,
        action: str,
        payload: Dict[str, Any],
        user: User,
        ip_address: Optional[str]
    ) -> Tuple[str, Optional[SyncConflict]]:
        email = payload.get("email")
        existing = db.query(Employee).filter(Employee.email == email).first()
        if existing:
            return "PROCESSED", None

        emp = Employee(
            employee_id=payload.get("employee_id") or f"EMP-{uuid.uuid4().hex[:6].upper()}",
            first_name=payload.get("first_name", "Employee"),
            last_name=payload.get("last_name", ""),
            full_name=f"{payload.get('first_name', '')} {payload.get('last_name', '')}".strip(),
            email=email,
            phone=payload.get("phone"),
            department_id=payload.get("department_id"),
            designation=payload.get("designation", "Staff"),
            joining_date=date.today(),
            status=payload.get("status", "ACTIVE")
        )
        db.add(emp)
        db.flush()
        return "PROCESSED", None

    @staticmethod
    def pull_server_deltas(db: Session, since_timestamp: Optional[str] = None) -> Dict[str, Any]:
        """Pull server master data and delta changes for local caching and synchronization."""
        employees = db.query(Employee).filter(Employee.deleted_at.is_(None)).all()
        departments = db.query(Department).all()
        holidays = db.query(Holiday).all()
        
        # Recent attendance (last 60 days)
        att_query = db.query(Attendance)
        if since_timestamp:
            try:
                dt = datetime.fromisoformat(since_timestamp.replace("Z", "+00:00"))
                att_query = att_query.filter(Attendance.updated_at >= dt)
            except Exception:
                pass
        attendance_records = att_query.order_by(Attendance.attendance_date.desc()).limit(500).all()
        
        # Pending leaves
        leaves = db.query(Leave).order_by(Leave.created_at.desc()).limit(100).all()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "employees": [
                {
                    "id": e.id,
                    "uuid": e.uuid,
                    "employee_id": e.employee_id,
                    "full_name": e.full_name,
                    "first_name": e.first_name,
                    "last_name": e.last_name,
                    "email": e.email,
                    "department_id": e.department_id,
                    "designation": e.designation,
                    "status": e.status
                }
                for e in employees
            ],
            "departments": [
                {
                    "id": d.id,
                    "uuid": d.uuid,
                    "name": d.name,
                    "description": d.description,
                    "is_active": d.is_active
                }
                for d in departments
            ],
            "holidays": [
                {
                    "id": h.id,
                    "uuid": h.uuid,
                    "name": h.name,
                    "date": str(h.date),
                    "description": h.description,
                    "is_active": h.is_active
                }
                for h in holidays
            ],
            "attendance": [
                {
                    "id": a.id,
                    "uuid": a.uuid,
                    "employee_id": a.employee_id,
                    "attendance_date": str(a.attendance_date),
                    "status": a.status,
                    "check_in": str(a.check_in_time) if a.check_in_time else None,
                    "check_out": str(a.check_out_time) if a.check_out_time else None,
                    "total_hours": a.total_hours,
                    "remarks": a.remarks
                }
                for a in attendance_records
            ],
            "leaves": [
                {
                    "id": l.id,
                    "uuid": l.uuid,
                    "employee_id": l.employee_id,
                    "leave_type": l.leave_type,
                    "start_date": str(l.start_date),
                    "end_date": str(l.end_date),
                    "number_of_days": l.number_of_days,
                    "status": l.status,
                    "reason": l.reason
                }
                for l in leaves
            ]
        }

    @staticmethod
    def get_pending_conflicts(db: Session) -> List[SyncConflict]:
        """Returns all unresolved sync conflicts."""
        return db.query(SyncConflict).filter(SyncConflict.status == "PENDING").order_by(SyncConflict.created_at.desc()).all()

    @staticmethod
    def resolve_conflict(
        db: Session,
        conflict_id: str,
        resolution_strategy: str,
        resolution_notes: str,
        user: User,
        ip_address: Optional[str] = None
    ) -> SyncConflict:
        """
        Resolves a conflict with authorized decision:
        'SERVER_WINS', 'CLIENT_WINS', or 'MANUAL_MERGE'
        """
        conflict = db.query(SyncConflict).filter(SyncConflict.conflict_id == conflict_id).first()
        if not conflict:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conflict record not found")

        if conflict.status == "RESOLVED":
            return conflict

        if resolution_strategy == "CLIENT_WINS":
            # Apply client payload over server state
            client_data = json.loads(conflict.client_payload)
            if conflict.entity_type == "Attendance":
                emp_id = client_data.get("employee_id")
                att_date = datetime.strptime(client_data.get("attendance_date"), "%Y-%m-%d").date()
                att = db.query(Attendance).filter(
                    Attendance.employee_id == emp_id,
                    Attendance.attendance_date == att_date
                ).first()
                if att:
                    att.status = client_data.get("status", att.status)
                    att.remarks = client_data.get("remarks") or att.remarks
                    db.flush()

        conflict.status = "RESOLVED"
        conflict.resolved_by_user_id = user.id
        conflict.resolution_strategy = resolution_strategy
        conflict.resolution_notes = resolution_notes
        conflict.resolved_at = datetime.now(timezone.utc)

        AuditService.log(
            db,
            action="CONFLICT_RESOLVED",
            description=f"Resolved sync conflict #{conflict.conflict_id} on {conflict.entity_type} using {resolution_strategy}",
            user_id=user.id,
            entity_type="SyncConflict",
            entity_id=conflict.conflict_id,
            ip_address=ip_address
        )

        db.commit()
        db.refresh(conflict)
        return conflict
