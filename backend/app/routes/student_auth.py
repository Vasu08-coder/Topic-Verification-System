from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import (
    StudentIdentity,
    create_student_access_token,
    hash_password,
    require_admin_auth,
    require_student_auth,
    verify_password,
    AdminIdentity,
)
from app.db.session import get_db
from app.models.student import Student
from app.models.branch import Branch
from app.routes.auth import limiter

# Student-facing router: register and login
router = APIRouter(prefix="/api/students", tags=["student_auth"])

# Admin-only router: manage students
admin_router = APIRouter(prefix="/api/admin", tags=["admin_students"])


class RegisterRequest(BaseModel):
    sis_id: str = Field(..., min_length=1, max_length=255)
    full_name: str = Field(..., min_length=1, max_length=255)
    branch_id: int | None = Field(default=None)
    branch: str | None = Field(default=None, max_length=255)
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    sis_id: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    student_id: int
    sis_id: str
    full_name: str


class StudentListResponse(BaseModel):
    id: int
    sis_id: str
    full_name: str
    branch_id: int
    branch_name: str | None
    has_password: bool


class ResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8)


class ResetPasswordResponse(BaseModel):
    message: str


@router.post("/register", response_model=LoginResponse, status_code=201)
@limiter.limit("5/minute")
def register(
    request: Request,
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Register or update a student account with a password."""
    try:
        student = db.query(Student).filter(Student.sis_id == payload.sis_id).one_or_none()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        ) from exc

    # If student exists and already has a password, reject
    if student is not None and student.password_hash is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already registered, please log in instead.",
        )

    hashed_password = hash_password(payload.password)

    # If student exists but has no password, update them
    if student is not None:
        student.full_name = payload.full_name
        student.password_hash = hashed_password

        # Update branch_id if provided
        branch_id = None
        if payload.branch_id is not None:
            branch_id = payload.branch_id
        elif payload.branch is not None:
            # Resolve branch by code or name
            branch_row = db.query(Branch).filter(
                (Branch.code == payload.branch) | (Branch.name == payload.branch)
            ).one_or_none()
            if branch_row is not None:
                branch_id = branch_row.id

        if branch_id is not None:
            student.branch_id = branch_id

        db.commit()
    else:
        # Create new student
        branch_id = payload.branch_id
        if branch_id is None and payload.branch is not None:
            branch_row = db.query(Branch).filter(
                (Branch.code == payload.branch) | (Branch.name == payload.branch)
            ).one_or_none()
            if branch_row is not None:
                branch_id = branch_row.id

        if branch_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="branch_id or a valid branch is required",
            )

        student = Student(
            sis_id=payload.sis_id,
            full_name=payload.full_name,
            branch_id=branch_id,
            password_hash=hashed_password,
        )
        db.add(student)
        db.commit()

    token = create_student_access_token(student.id, student.sis_id, student.full_name)
    return LoginResponse(
        access_token=token,
        student_id=student.id,
        sis_id=student.sis_id,
        full_name=student.full_name,
    )


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Authenticate a student and issue a signed JWT access token."""
    try:
        student = db.query(Student).filter(Student.sis_id == payload.sis_id).one_or_none()
    except SQLAlchemyError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from None

    if student is None or student.password_hash is None or not verify_password(payload.password, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_student_access_token(student.id, student.sis_id, student.full_name)
    return LoginResponse(
        access_token=token,
        student_id=student.id,
        sis_id=student.sis_id,
        full_name=student.full_name,
    )


@admin_router.get("/students", response_model=list[StudentListResponse])
def list_students(
    current_admin: AdminIdentity = Depends(require_admin_auth),
    db: Session = Depends(get_db),
) -> list[StudentListResponse]:
    """List all students with password registration status (admin-only)."""
    
    try:
        student = db.query(Student).filter(
            Student.sis_id == payload.sis_id
        ).one_or_none()
    except SQLAlchemyError as exc:
        print("REGISTRATION DATABASE ERROR:", repr(exc))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error. Check backend terminal.",
        ) from exc


    result = []
    for student in students:
        branch = db.query(Branch).filter(Branch.id == student.branch_id).one_or_none()
        result.append(
            StudentListResponse(
                id=student.id,
                sis_id=student.sis_id,
                full_name=student.full_name,
                branch_id=student.branch_id,
                branch_name=branch.name if branch else None,
                has_password=student.password_hash is not None,
            )
        )

    return result


@admin_router.put("/students/{student_id}/reset-password", response_model=ResetPasswordResponse)
def reset_password(
    student_id: int,
    payload: ResetPasswordRequest,
    current_admin: AdminIdentity = Depends(require_admin_auth),
    db: Session = Depends(get_db),
) -> ResetPasswordResponse:
    """Reset a student's password (admin-only)."""
    try:
        student = db.query(Student).filter(Student.id == student_id).one_or_none()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error",
        ) from exc

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    student.password_hash = hash_password(payload.new_password)
    db.commit()

    return ResetPasswordResponse(message="Password reset successfully")
