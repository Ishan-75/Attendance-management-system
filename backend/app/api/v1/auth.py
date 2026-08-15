from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    EmailVerificationRequest
)
from app.schemas.user import UserResponse
from app.schemas.common import APIResponse
from app.services.auth_service import AuthService
from app.core.rate_limit import check_auth_rate_limit
from app.api.v1.deps import get_current_user, get_client_ip, get_user_agent
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=APIResponse[TokenResponse])
def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    check_auth_rate_limit(request)
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    user, token = AuthService.authenticate_user(db, login_data, ip_address=ip, user_agent=ua)
    
    return APIResponse(
        success=True,
        message="Login successful",
        data=TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=480 * 60,
            user=UserResponse.model_validate(user)
        )
    )


@router.get("/me", response_model=APIResponse[UserResponse])
def get_me(current_user: User = Depends(get_current_user)):
    return APIResponse(
        success=True,
        message="Current user profile",
        data=UserResponse.model_validate(current_user)
    )


@router.post("/verify-email", response_model=APIResponse[bool])
def verify_email(
    request: Request,
    verify_data: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    check_auth_rate_limit(request)
    AuthService.verify_email(db, verify_data.token)
    return APIResponse(success=True, message="Email verified successfully", data=True)


@router.post("/forgot-password", response_model=APIResponse[bool])
def forgot_password(
    request: Request,
    forgot_data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    check_auth_rate_limit(request)
    AuthService.initiate_forgot_password(db, forgot_data.email)
    return APIResponse(
        success=True,
        message="If this email is registered, password reset instructions have been sent.",
        data=True
    )


@router.post("/reset-password", response_model=APIResponse[bool])
def reset_password(
    request: Request,
    reset_data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    check_auth_rate_limit(request)
    ip = get_client_ip(request)
    AuthService.reset_password(db, reset_data, ip_address=ip)
    return APIResponse(success=True, message="Password reset successfully. You can now log in.", data=True)


@router.post("/change-password", response_model=APIResponse[bool])
def change_password(
    request: Request,
    change_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    AuthService.change_password(db, current_user, change_data, ip_address=ip)
    return APIResponse(success=True, message="Password updated successfully", data=True)


@router.post("/logout", response_model=APIResponse[bool])
def logout(current_user: User = Depends(get_current_user)):
    return APIResponse(success=True, message="Logged out successfully", data=True)
