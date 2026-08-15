from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.holiday import Holiday
from app.models.user import User
from app.models.audit_log import AuditAction
from app.schemas.holiday import HolidayCreate, HolidayUpdate
from app.services.audit_service import AuditService


class HolidayService:
    @staticmethod
    def get_holidays(db: Session, year: Optional[int] = None, active_only: bool = False) -> List[Holiday]:
        query = db.query(Holiday)
        if active_only:
            query = query.filter(Holiday.is_active.is_(True))
        if year:
            query = query.filter(Holiday.date >= f"{year}-01-01", Holiday.date <= f"{year}-12-31")
        return query.order_by(Holiday.date.asc()).all()

    @staticmethod
    def create_holiday(db: Session, hol_in: HolidayCreate, user: User, ip_address: Optional[str] = None) -> Holiday:
        existing = db.query(Holiday).filter(Holiday.date == hol_in.date).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A holiday is already scheduled on {hol_in.date} ({existing.name})"
            )

        holiday = Holiday(
            name=hol_in.name.strip(),
            date=hol_in.date,
            description=hol_in.description.strip() if hol_in.description else None,
            is_active=hol_in.is_active
        )
        db.add(holiday)
        db.flush()

        AuditService.log(
            db,
            action=AuditAction.HOLIDAY_CREATED,
            description=f"Created holiday '{holiday.name}' on {holiday.date}",
            user_id=user.id,
            entity_type="Holiday",
            entity_id=str(holiday.id),
            new_value={"name": holiday.name, "date": str(holiday.date)},
            ip_address=ip_address
        )
        db.commit()
        db.refresh(holiday)
        return holiday

    @staticmethod
    def update_holiday(db: Session, hol_id: int, hol_in: HolidayUpdate, user: User, ip_address: Optional[str] = None) -> Holiday:
        holiday = db.query(Holiday).filter(Holiday.id == hol_id).first()
        if not holiday:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")

        if hol_in.date and hol_in.date != holiday.date:
            existing = db.query(Holiday).filter(
                Holiday.date == hol_in.date,
                Holiday.id != hol_id
            ).first()
            if existing:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A holiday is already scheduled on this date.")
            holiday.date = hol_in.date

        if hol_in.name:
            holiday.name = hol_in.name.strip()
        if hol_in.description is not None:
            holiday.description = hol_in.description.strip() if hol_in.description else None
        if hol_in.is_active is not None:
            holiday.is_active = hol_in.is_active

        AuditService.log(
            db,
            action=AuditAction.HOLIDAY_UPDATED,
            description=f"Updated holiday '{holiday.name}' ({holiday.date})",
            user_id=user.id,
            entity_type="Holiday",
            entity_id=str(holiday.id),
            ip_address=ip_address
        )
        db.commit()
        db.refresh(holiday)
        return holiday

    @staticmethod
    def delete_holiday(db: Session, hol_id: int, user: User, ip_address: Optional[str] = None) -> bool:
        holiday = db.query(Holiday).filter(Holiday.id == hol_id).first()
        if not holiday:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")

        name = holiday.name
        d = holiday.date
        db.delete(holiday)

        AuditService.log(
            db,
            action=AuditAction.HOLIDAY_UPDATED,
            description=f"Deleted holiday '{name}' on {d}",
            user_id=user.id,
            entity_type="Holiday",
            entity_id=str(hol_id),
            ip_address=ip_address
        )
        db.commit()
        return True
