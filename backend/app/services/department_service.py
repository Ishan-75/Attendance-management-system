from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.department import Department
from app.models.employee import Employee
from app.models.user import User
from app.models.audit_log import AuditAction
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.services.audit_service import AuditService


class DepartmentService:
    @staticmethod
    def get_departments(db: Session, active_only: bool = False) -> List[DepartmentResponse]:
        query = db.query(Department)
        if active_only:
            query = query.filter(Department.is_active.is_(True))
        
        departments = query.order_by(Department.name.asc()).all()
        
        result = []
        for d in departments:
            count = db.query(Employee).filter(
                Employee.department_id == d.id,
                Employee.deleted_at.is_(None)
            ).count()
            
            result.append(
                DepartmentResponse(
                    id=d.id,
                    name=d.name,
                    description=d.description,
                    is_active=d.is_active,
                    employee_count=count,
                    created_at=d.created_at,
                    updated_at=d.updated_at
                )
            )
        return result

    @staticmethod
    def create_department(db: Session, dept_in: DepartmentCreate, user: User, ip_address: Optional[str] = None) -> Department:
        existing = db.query(Department).filter(Department.name.ilike(dept_in.name.strip())).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A department with this name already exists.")

        dept = Department(
            name=dept_in.name.strip(),
            description=dept_in.description.strip() if dept_in.description else None,
            is_active=dept_in.is_active
        )
        db.add(dept)
        db.flush()

        AuditService.log(
            db,
            action=AuditAction.DEPARTMENT_CREATED,
            description=f"Created department '{dept.name}'",
            user_id=user.id,
            entity_type="Department",
            entity_id=str(dept.id),
            new_value={"name": dept.name},
            ip_address=ip_address
        )
        db.commit()
        db.refresh(dept)
        return dept

    @staticmethod
    def update_department(db: Session, dept_id: int, dept_in: DepartmentUpdate, user: User, ip_address: Optional[str] = None) -> Department:
        dept = db.query(Department).filter(Department.id == dept_id).first()
        if not dept:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

        if dept_in.name:
            existing = db.query(Department).filter(
                Department.name.ilike(dept_in.name.strip()),
                Department.id != dept_id
            ).first()
            if existing:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Another department with this name exists.")
            dept.name = dept_in.name.strip()

        if dept_in.description is not None:
            dept.description = dept_in.description.strip() if dept_in.description else None

        if dept_in.is_active is not None:
            dept.is_active = dept_in.is_active

        AuditService.log(
            db,
            action=AuditAction.DEPARTMENT_UPDATED,
            description=f"Updated department '{dept.name}'",
            user_id=user.id,
            entity_type="Department",
            entity_id=str(dept.id),
            ip_address=ip_address
        )
        db.commit()
        db.refresh(dept)
        return dept

    @staticmethod
    def delete_department(db: Session, dept_id: int, user: User, ip_address: Optional[str] = None) -> bool:
        dept = db.query(Department).filter(Department.id == dept_id).first()
        if not dept:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

        # Check if active or non-deleted employees are assigned
        assigned_count = db.query(Employee).filter(
            Employee.department_id == dept_id,
            Employee.deleted_at.is_(None)
        ).count()
        if assigned_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete department '{dept.name}' because {assigned_count} employee(s) are assigned to it. Please reassign them first or mark the department as inactive."
            )

        dept_name = dept.name
        db.delete(dept)
        AuditService.log(
            db,
            action=AuditAction.DEPARTMENT_DELETED,
            description=f"Deleted department '{dept_name}'",
            user_id=user.id,
            entity_type="Department",
            entity_id=str(dept_id),
            ip_address=ip_address
        )
        db.commit()
        return True
