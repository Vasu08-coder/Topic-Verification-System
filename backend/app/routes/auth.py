from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.security import (
    AdminIdentity,
    create_access_token,
    get_current_admin,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.admin import AdminUser

router = APIRouter(prefix="/api/auth", tags=["authentication"])
limiter = Limiter(key_func=get_remote_address)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    full_name: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class ChangePasswordResponse(BaseModel):
    message: str


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Authenticate an admin and issue a signed JWT access token."""
    try:
        admin = db.query(AdminUser).filter(AdminUser.username == payload.username).one_or_none()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from None

    if admin is None or not verify_password(payload.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token(admin.id, admin.username, admin.full_name)
    return LoginResponse(access_token=token, full_name=admin.full_name)


@router.post("/change-password", response_model=ChangePasswordResponse)
def change_password(
    payload: ChangePasswordRequest,
    current_admin: AdminIdentity = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ChangePasswordResponse:
    """Update the current admin password after verifying the existing one."""
    try:
        admin = db.query(AdminUser).filter(AdminUser.id == current_admin.id).one_or_none()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from None

    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not verify_password(payload.current_password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if len(payload.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )

    admin.password_hash = hash_password(payload.new_password)
    db.commit()

    return ChangePasswordResponse(message="Password updated successfully")


# TODO: add a forgot-password email flow once SMTP is configured.
