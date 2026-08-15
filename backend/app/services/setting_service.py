from typing import List, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.setting import Setting
from app.models.user import User
from app.models.audit_log import AuditAction
from app.services.audit_service import AuditService


class SettingService:
    @staticmethod
    def get_all_settings(db: Session) -> List[Setting]:
        return db.query(Setting).all()

    @staticmethod
    def get_setting_dict(db: Session) -> Dict[str, str]:
        settings = db.query(Setting).all()
        return {s.key: s.value for s in settings}

    @staticmethod
    def update_settings(db: Session, updates: List[Dict[str, str]], user: User, ip_address: str = None) -> List[Setting]:
        changed = []
        for item in updates:
            key = item.get("key")
            value = item.get("value")
            if not key:
                continue

            setting = db.query(Setting).filter(Setting.key == key).first()
            if setting:
                old_val = setting.value
                setting.value = str(value)
                changed.append({"key": key, "old": old_val, "new": value})
            else:
                new_s = Setting(key=key, value=str(value))
                db.add(new_s)
                changed.append({"key": key, "old": None, "new": value})

        AuditService.log(
            db,
            action=AuditAction.SETTINGS_CHANGED,
            description=f"System settings updated by {user.username} ({len(changed)} keys modified)",
            user_id=user.id,
            entity_type="Setting",
            new_value=changed,
            ip_address=ip_address
        )
        db.commit()
        return db.query(Setting).all()
