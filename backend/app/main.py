from __future__ import annotations

import logging
import traceback
from time import perf_counter
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging_config import logger
from app.db.session import SessionLocal
from app.routes.admin_export import router as admin_export_router
from app.routes.admin_import import router as admin_import_router
from app.routes.admin_ledger import router as admin_ledger_router
from app.routes.admin_submissions import router as admin_submissions_router
from app.routes.archive import router as archive_router
from app.routes.auth import limiter, router as auth_router
from app.routes.student_auth import admin_router as student_admin_router, router as student_auth_router
from app.routes.submissions import limiter as submissions_limiter, router as submissions_router

DEFAULT_RATE_LIMIT_MESSAGE = "Too many requests, please try again later"

app = FastAPI(
    title="Topic Verifier API",
    version="0.1.0",
    description="Backend for seminar and final-year project topic verification.",
)

# 1. CORS Middleware MUST be added FIRST so it can intercept and handle 
# browser preflight OPTIONS requests before any rate limiter or route logic checks them.
# Keep the local Vite dev-server origins aligned with the frontend port used in development.
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]
origins = list(dict.fromkeys(default_origins))

# If your settings.ALLOWED_ORIGINS has values, combine them safely
if hasattr(settings, "ALLOWED_ORIGINS") and settings.ALLOWED_ORIGINS:
    extra_origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
    origins.extend(extra_origins)
    origins = list(dict.fromkeys(origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(origins)),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# 2. Add SlowAPI Rate Limiter Middleware AFTER CORS
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Include routers
app.include_router(auth_router)
app.include_router(student_auth_router)
app.include_router(student_admin_router)
app.include_router(submissions_router)
app.include_router(admin_submissions_router)
app.include_router(admin_import_router)
app.include_router(admin_export_router)
app.include_router(admin_ledger_router)
app.include_router(archive_router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started_at = perf_counter()
    response = await call_next(request)
    duration_ms = round((perf_counter() - started_at) * 1000, 2)
    logger.info(
        "request_completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": True, "message": exc.detail, "code": exc.code},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors: list[dict[str, Any]] = []
    for error in exc.errors():
        field = ".".join(str(part) for part in error.get("loc", []))
        errors.append({"field": field, "message": error.get("msg", "Validation failed")})
    return JSONResponse(
        status_code=400,
        content={"error": True, "message": "Validation failed", "details": errors, "code": "validation_error"},
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    limit_text = str(exc.limit.limit) if exc.limit else ""
    message = DEFAULT_RATE_LIMIT_MESSAGE
    if limit_text:
        message = f"Too many requests, please try again in {limit_text}"
    return JSONResponse(
        status_code=429,
        content={"error": True, "message": message, "code": "rate_limit_exceeded"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception", extra={"path": request.url.path, "method": request.method})
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": "Internal server error", "code": "internal_error"},
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    try:
        with SessionLocal() as session:
            session.execute("SELECT 1")
        return {"status": "ok", "db": "connected"}
    except SQLAlchemyError:
        raise AppException("Database unavailable", status_code=503, code="database_unavailable")