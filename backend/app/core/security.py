from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings

security_scheme = HTTPBearer(auto_error=False)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8


class AdminIdentity:
    """Minimal identity information embedded in the JWT payload."""

    def __init__(
        self,
        admin_id: int,
        username: str,
        full_name: str,
        role: str | None = None,
        branch: str | None = None,
    ) -> None:
        self.id = admin_id
        self.username = username
        self.full_name = full_name
        self.role = role
        self.branch = branch


class StudentIdentity:
    """Minimal identity information for a student JWT payload."""

    def __init__(
        self,
        student_id: int,
        sis_id: str,
        full_name: str,
    ) -> None:
        self.id = student_id
        self.sis_id = sis_id
        self.full_name = full_name


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(admin_id: int, username: str, full_name: str) -> str:
    """Create a signed JWT token containing the admin identity."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(admin_id),
        "username": username,
        "full_name": full_name,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)).timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_student_access_token(student_id: int, sis_id: str, full_name: str) -> str:
    """Create a signed JWT token containing a student identity."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(student_id),
        "sis_id": sis_id,
        "full_name": full_name,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)).timestamp()),
        "type": "access",
        "student": True,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> AdminIdentity:
    """Validate a bearer token and return the signed-in admin identity."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    payload = decode_access_token(credentials.credentials)
    admin_id = payload.get("sub")
    username = payload.get("username")
    full_name = payload.get("full_name")

    if not isinstance(admin_id, str) or not isinstance(username, str) or not isinstance(full_name, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    return AdminIdentity(admin_id=int(admin_id), username=username, full_name=full_name)


def get_current_student(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> StudentIdentity:
    """Validate a bearer token and return the signed-in student identity."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    payload = decode_access_token(credentials.credentials)
    student_id = payload.get("sub")
    sis_id = payload.get("sis_id")
    full_name = payload.get("full_name")

    if not isinstance(student_id, str) or not isinstance(sis_id, str) or not isinstance(full_name, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    return StudentIdentity(student_id=int(student_id), sis_id=sis_id, full_name=full_name)


def require_admin_auth(current_admin: AdminIdentity = Depends(get_current_admin)) -> AdminIdentity:
    """Validate that the current request is authenticated as an admin."""
    return current_admin


def require_student_auth(current_student: StudentIdentity = Depends(get_current_student)) -> StudentIdentity:
    """Validate that the current request is authenticated as a student."""
    return current_student


# TODO: add refresh-token support later if the system needs session renewal.
