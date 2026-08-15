from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, UserRole
from app.models.audit_log import AuditAction
from app.core.security import verify_password, get_password_hash, create_access_token, generate_secure_token
from app.core.config import settings
from app.services.audit_service import AuditService
from app.services.email_service import EmailService
from app.schemas.auth import LoginRequest, ChangePasswordRequest, ResetPasswordRequest
from app.schemas.user import UserCreate


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Helper to ensure datetime is timezone-aware UTC for safe comparisons."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class AuthService:
    @staticmethod
    def authenticate_user(
        db: Session,
        login_data: LoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[User, str]:
        """Authenticate user credentials, enforce account lockout, issue JWT, and audit log."""
        identifier = login_data.username_or_email.strip()
        now = datetime.now(timezone.utc)

        user = db.query(User).filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if not user:
            AuditService.log(
                db,
                action=AuditAction.FAILED_LOGIN,
                description=f"Failed login attempt for non-existent identifier: {identifier}",
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username/email or password"
            )

        # Check account lockout with timezone-safe comparison
        locked_until = ensure_utc(user.locked_until)
        if locked_until and locked_until > now:
            minutes_left = int((locked_until - now).total_seconds() / 60) + 1
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is temporarily locked due to multiple failed login attempts. Try again in {minutes_left} minutes."
            )

        # Check if active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This account has been deactivated. Please contact an administrator."
            )

        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            user.failed_login_attempts += 1
            
            # Check if threshold reached for lockout
            if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=settings.ACCOUNT_LOCKOUT_MINUTES)
                AuditService.log(
                    db,
                    action=AuditAction.ACCOUNT_LOCKED,
                    description=f"Account {user.username} locked for {settings.ACCOUNT_LOCKOUT_MINUTES} minutes after {user.failed_login_attempts} failed attempts",
                    user_id=user.id,
                    entity_type="User",
                    entity_id=str(user.id),
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            else:
                AuditService.log(
                    db,
                    action=AuditAction.FAILED_LOGIN,
                    description=f"Failed password attempt for user {user.username} (Attempt {user.failed_login_attempts})",
                    user_id=user.id,
                    entity_type="User",
                    entity_id=str(user.id),
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username/email or password"
            )

        # Successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = now
        
        token = create_access_token(subject=user.id, role=user.role)

        AuditService.log(
            db,
            action=AuditAction.LOGIN,
            description=f"User {user.username} logged in successfully",
            user_id=user.id,
            entity_type="User",
            entity_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.commit()
        db.refresh(user)
        return user, token

    @staticmethod
    def create_user(
        db: Session,
        user_in: UserCreate,
        creator: Optional[User] = None,
        ip_address: Optional[str] = None
    ) -> User:
        """Create new system user/manager with uniqueness validation."""
        # Check duplicate username
        if db.query(User).filter(User.username == user_in.username).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this username already exists."
            )

        # Check duplicate email
        if db.query(User).filter(User.email == user_in.email.lower()).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists."
            )

        verification_token = generate_secure_token()
        now = datetime.now(timezone.utc)

        new_user = User(
            username=user_in.username,
            full_name=user_in.full_name,
            email=user_in.email.lower(),
            password_hash=get_password_hash(user_in.password),
            role=user_in.role,
            is_active=user_in.is_active,
            is_email_verified=False,
            email_verification_token=verification_token,
            created_at=now,
            updated_at=now
        )
        db.add(new_user)
        db.flush()

        AuditService.log(
            db,
            action=AuditAction.USER_CREATED,
            description=f"Created user {new_user.username} with role {new_user.role}",
            user_id=creator.id if creator else None,
            entity_type="User",
            entity_id=str(new_user.id),
            new_value={"username": new_user.username, "email": new_user.email, "role": new_user.role},
            ip_address=ip_address
        )

        # Trigger email verification token
        EmailService.send_verification_email(new_user.email, new_user.username, verification_token)

        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def verify_email(db: Session, token: str) -> bool:
        """Validate single-use email verification token."""
        user = db.query(User).filter(User.email_verification_token == token).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token."
            )

        user.is_email_verified = True
        user.email_verification_token = None
        db.commit()
        return True

    @staticmethod
    def initiate_forgot_password(db: Session, email: str) -> bool:
        """Send password reset token without leaking email existence."""
        user = db.query(User).filter(User.email == email.lower()).first()
        if user and user.is_active:
            token = generate_secure_token()
            user.password_reset_token = token
            user.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
            db.commit()
            EmailService.send_password_reset_email(user.email, user.username, token)
        return True

    @staticmethod
    def reset_password(db: Session, reset_data: ResetPasswordRequest, ip_address: Optional[str] = None) -> bool:
        """Reset password using secure single-use token."""
        now = datetime.now(timezone.utc)
        user = db.query(User).filter(User.password_reset_token == reset_data.token).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset link. Please request a new one."
            )

        expires_at = ensure_utc(user.password_reset_expires_at)
        if not expires_at or expires_at <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token has expired. Please request a new one."
            )

        user.password_hash = get_password_hash(reset_data.new_password)
        user.password_reset_token = None
        user.password_reset_expires_at = None
        user.failed_login_attempts = 0
        user.locked_until = None

        AuditService.log(
            db,
            action=AuditAction.PASSWORD_RESET,
            description=f"Password was successfully reset for user {user.username}",
            user_id=user.id,
            entity_type="User",
            entity_id=str(user.id),
            ip_address=ip_address
        )
        db.commit()
        return True

    @staticmethod
    def change_password(db: Session, user: User, change_data: ChangePasswordRequest, ip_address: Optional[str] = None) -> bool:
        """Change current user's password."""
        if not verify_password(change_data.current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect."
            )

        user.password_hash = get_password_hash(change_data.new_password)
        AuditService.log(
            db,
            action=AuditAction.PASSWORD_CHANGED,
            description=f"User {user.username} changed their password",
            user_id=user.id,
            entity_type="User",
            entity_id=str(user.id),
            ip_address=ip_address
        )
        db.commit()
        return True
