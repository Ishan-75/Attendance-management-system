from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import APIResponse
from app.services.email_service import EmailService
from app.api.v1.deps import require_admin, get_client_ip
from app.models.user import User
from app.services.audit_service import AuditService

router = APIRouter(prefix="/system", tags=["System Diagnostics & SMTP"])


class TestEmailRequest(BaseModel):
    target_email: Optional[str] = "attendancesystem55@gmail.com"


@router.get("/smtp-status", response_model=APIResponse[Dict[str, Any]])
def get_smtp_status(
    admin: User = Depends(require_admin)
):
    """Returns safe, non-revealing SMTP configuration parameters for Admin."""
    status_info = EmailService.get_smtp_status()
    return APIResponse(
        success=True,
        message="SMTP status retrieved",
        data=status_info
    )


@router.post("/test-email", response_model=APIResponse[Dict[str, Any]])
def send_test_email(
    request: Request,
    payload: TestEmailRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Connects to Gmail SMTP (smtp.gmail.com:587) with STARTTLS,
    authenticates using environment credentials, and sends a live verification email.
    """
    ip = get_client_ip(request)
    target = payload.target_email or "attendancesystem55@gmail.com"
    success, msg = EmailService.test_smtp_connection(target)

    # Log action to audit trail
    AuditService.log(
        db,
        action="SMTP_TEST_SENT" if success else "SMTP_TEST_FAILED",
        description=f"Admin {admin.username} triggered SMTP test email to {target}: {'Success' if success else 'Failed'}",
        user_id=admin.id,
        entity_type="System",
        ip_address=ip
    )
    db.commit()

    return APIResponse(
        success=success,
        message=msg,
        data={"recipient": target, "delivered": success}
    )
