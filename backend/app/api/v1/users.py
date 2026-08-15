from typing import List
from fastapi import APIRouter, Depends, Request, status, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.common import APIResponse
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.models.user import User
from app.models.audit_log import AuditAction
from app.core.security import get_password_hash
from app.api.v1.deps import require_admin, get_client_ip

router = APIRouter(prefix="/users", tags=["Users (Admin)"])


@router.get("", response_model=APIResponse[List[UserResponse]])
def list_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.id.asc()).all()
    return APIResponse(
        success=True,
        message="Users list retrieved",
        data=[UserResponse.model_validate(u) for u in users]
    )


@router.post("", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def create_user(
    request: Request,
    user_in: UserCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    user = AuthService.create_user(db, user_in, creator=admin, ip_address=ip)
    return APIResponse(
        success=True,
        message=f"User {user.username} created successfully",
        data=UserResponse.model_validate(user)
    )


@router.put("/{user_id}", response_model=APIResponse[UserResponse])
def update_user(
    request: Request,
    user_id: int,
    user_in: UserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_in.full_name:
        user.full_name = user_in.full_name
    if user_in.email:
        existing = db.query(User).filter(User.email == user_in.email.lower(), User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already taken")
        user.email = user_in.email.lower()
    if user_in.role:
        user.role = user_in.role
    if user_in.is_active is not None:
        user.is_active = user_in.is_active
    if user_in.password:
        user.password_hash = get_password_hash(user_in.password)

    ip = get_client_ip(request)
    AuditService.log(
        db,
        action=AuditAction.USER_UPDATED,
        description=f"Updated user account {user.username}",
        user_id=admin.id,
        entity_type="User",
        entity_id=str(user.id),
        ip_address=ip
    )
    db.commit()
    db.refresh(user)
    return APIResponse(
        success=True,
        message="User updated successfully",
        data=UserResponse.model_validate(user)
    )
