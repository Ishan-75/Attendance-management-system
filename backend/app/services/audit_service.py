import json
from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    def log(
        db: Session,
        action: str,
        description: str,
        user_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """Create an append-only audit log entry."""
        # Serialize dict/list if passed
        old_str = json.dumps(old_value, default=str) if isinstance(old_value, (dict, list)) else (str(old_value) if old_value is not None else None)
        new_str = json.dumps(new_value, default=str) if isinstance(new_value, (dict, list)) else (str(new_value) if new_value is not None else None)

        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            old_value=old_str,
            new_value=new_str,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent[:255] if user_agent else None,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(audit_entry)
        db.flush()
        return audit_entry
