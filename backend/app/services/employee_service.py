from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from fastapi import HTTPException, status
from app.models.employee import Employee, EmployeeStatus
from app.models.department import Department
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeStatusUpdate
from app.services.audit_service import AuditService


class EmployeeService:
    @staticmethod
    def generate_next_employee_id(db: Session) -> str:
        """Generate next sequential employee code e.g. EMP-0001, EMP-0002."""
        latest = db.query(Employee).order_by(desc(Employee.id)).first()
        next_num = (latest.id + 1) if latest else 1
        return f"EMP-{next_num:04d}"

    @staticmethod
    def get_employees(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        department_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None,
        include_deleted: bool = False
    ) -> Tuple[List[Employee], int]:
        """Fetch filtered and paginated employee list."""
        query = db.query(Employee)

        if not include_deleted:
            query = query.filter(Employee.deleted_at.is_(None))

        if department_id:
            query = query.filter(Employee.department_id == department_id)

        if status_filter:
            query = query.filter(Employee.status == status_filter)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Employee.full_name.ilike(search_term),
                    Employee.employee_id.ilike(search_term),
                    Employee.email.ilike(search_term),
                    Employee.designation.ilike(search_term)
                )
            )

        total = query.count()
        items = query.order_by(Employee.employee_id.asc()).offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def get_employee_by_id(db: Session, employee_id: int) -> Employee:
        employee = db.query(Employee).filter(
            Employee.id == employee_id,
            Employee.deleted_at.is_(None)
        ).first()
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        return employee

    @staticmethod
    def get_employee_by_code(db: Session, code: str) -> Employee:
        employee = db.query(Employee).filter(
            Employee.employee_id == code,
            Employee.deleted_at.is_(None)
        ).first()
        if not employee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Employee {code} not found")
        return employee

    @staticmethod
    def create_employee(
        db: Session,
        emp_in: EmployeeCreate,
        user: User,
        ip_address: Optional[str] = None
    ) -> Employee:
        """Create new employee with validation and audit logging."""
        # 1. Verify Department exists and is active
        dept = db.query(Department).filter(Department.id == emp_in.department_id).first()
        if not dept:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department does not exist")

        # 2. Determine or validate employee_id
        emp_code = emp_in.employee_id.strip() if emp_in.employee_id else EmployeeService.generate_next_employee_id(db)
        
        # Check duplicate employee_id
        if db.query(Employee).filter(Employee.employee_id == emp_code).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee with ID '{emp_code}' already exists."
            )

        # Check duplicate email
        if db.query(Employee).filter(Employee.email == emp_in.email.lower()).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Employee with email '{emp_in.email}' already exists."
            )

        full_name = f"{emp_in.first_name.strip()} {emp_in.last_name.strip()}".strip()

        employee = Employee(
            employee_id=emp_code,
            first_name=emp_in.first_name.strip(),
            last_name=emp_in.last_name.strip(),
            full_name=full_name,
            email=emp_in.email.lower(),
            phone=emp_in.phone.strip() if emp_in.phone else None,
            department_id=emp_in.department_id,
            designation=emp_in.designation.strip(),
            joining_date=emp_in.joining_date,
            employment_type=emp_in.employment_type,
            status=emp_in.status,
            profile_photo=emp_in.profile_photo,
            address=emp_in.address,
            emergency_contact=emp_in.emergency_contact
        )

        db.add(employee)
        db.flush()

        AuditService.log(
            db,
            action=AuditAction.EMPLOYEE_CREATED,
            description=f"Created employee {employee.full_name} ({employee.employee_id}) in department {dept.name}",
            user_id=user.id,
            entity_type="Employee",
            entity_id=str(employee.id),
            new_value={
                "employee_id": employee.employee_id,
                "full_name": employee.full_name,
                "email": employee.email,
                "department_id": employee.department_id,
                "status": employee.status
            },
            ip_address=ip_address
        )

        db.commit()
        db.refresh(employee)
        return employee

    @staticmethod
    def update_employee(
        db: Session,
        employee_id: int,
        emp_in: EmployeeUpdate,
        user: User,
        ip_address: Optional[str] = None
    ) -> Employee:
        """Update employee details with audit logging."""
        employee = EmployeeService.get_employee_by_id(db, employee_id)
        old_data = {
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "email": employee.email,
            "phone": employee.phone,
            "department_id": employee.department_id,
            "designation": employee.designation,
            "status": employee.status
        }

        # Check unique email if changing
        if emp_in.email and emp_in.email.lower() != employee.email:
            existing = db.query(Employee).filter(
                Employee.email == emp_in.email.lower(),
                Employee.id != employee_id
            ).first()
            if existing:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already used by another employee")
            employee.email = emp_in.email.lower()

        if emp_in.department_id and emp_in.department_id != employee.department_id:
            dept = db.query(Department).filter(Department.id == emp_in.department_id).first()
            if not dept:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department does not exist")
            employee.department_id = emp_in.department_id

        if emp_in.first_name:
            employee.first_name = emp_in.first_name.strip()
        if emp_in.last_name:
            employee.last_name = emp_in.last_name.strip()
        employee.full_name = f"{employee.first_name} {employee.last_name}".strip()

        if emp_in.phone is not None:
            employee.phone = emp_in.phone.strip() if emp_in.phone else None
        if emp_in.designation:
            employee.designation = emp_in.designation.strip()
        if emp_in.joining_date:
            employee.joining_date = emp_in.joining_date
        if emp_in.employment_type:
            employee.employment_type = emp_in.employment_type
        if emp_in.status:
            employee.status = emp_in.status
        if emp_in.profile_photo is not None:
            employee.profile_photo = emp_in.profile_photo
        if emp_in.address is not None:
            employee.address = emp_in.address
        if emp_in.emergency_contact is not None:
            employee.emergency_contact = emp_in.emergency_contact

        AuditService.log(
            db,
            action=AuditAction.EMPLOYEE_UPDATED,
            description=f"Updated details for employee {employee.full_name} ({employee.employee_id})",
            user_id=user.id,
            entity_type="Employee",
            entity_id=str(employee.id),
            old_value=old_data,
            new_value={
                "first_name": employee.first_name,
                "last_name": employee.last_name,
                "email": employee.email,
                "phone": employee.phone,
                "department_id": employee.department_id,
                "designation": employee.designation,
                "status": employee.status
            },
            ip_address=ip_address
        )

        db.commit()
        db.refresh(employee)
        return employee

    @staticmethod
    def update_status(
        db: Session,
        employee_id: int,
        status_in: EmployeeStatusUpdate,
        user: User,
        ip_address: Optional[str] = None
    ) -> Employee:
        """Update employee employment status (ACTIVE, INACTIVE, RESIGNED, etc.)"""
        employee = EmployeeService.get_employee_by_id(db, employee_id)
        old_status = employee.status
        employee.status = status_in.status

        action = AuditAction.EMPLOYEE_DEACTIVATED if status_in.status == EmployeeStatus.INACTIVE else (
            AuditAction.EMPLOYEE_REACTIVATED if status_in.status == EmployeeStatus.ACTIVE else AuditAction.EMPLOYEE_UPDATED
        )

        AuditService.log(
            db,
            action=action,
            description=f"Changed status of {employee.full_name} from {old_status} to {status_in.status}. Reason: {status_in.reason or 'N/A'}",
            user_id=user.id,
            entity_type="Employee",
            entity_id=str(employee.id),
            old_value={"status": old_status},
            new_value={"status": status_in.status, "reason": status_in.reason},
            ip_address=ip_address
        )

        db.commit()
        db.refresh(employee)
        return employee

    @staticmethod
    def delete_employee(db: Session, employee_id: int, user: User, ip_address: Optional[str] = None) -> bool:
        """Soft delete employee."""
        employee = EmployeeService.get_employee_by_id(db, employee_id)
        employee.deleted_at = datetime.now(timezone.utc)
        employee.status = EmployeeStatus.INACTIVE

        AuditService.log(
            db,
            action=AuditAction.EMPLOYEE_DEACTIVATED,
            description=f"Soft deleted employee {employee.full_name} ({employee.employee_id})",
            user_id=user.id,
            entity_type="Employee",
            entity_id=str(employee.id),
            ip_address=ip_address
        )
        db.commit()
        return True
