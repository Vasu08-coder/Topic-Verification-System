from __future__ import annotations


class AppException(Exception):
    """Base application exception with an HTTP status code and client-safe message."""

    def __init__(self, message: str, status_code: int = 500, code: str = "internal_error") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = message
        self.code = code


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", code: str = "not_found") -> None:
        super().__init__(message, status_code=404, code=code)


class ValidationException(AppException):
    def __init__(self, message: str = "Validation failed", code: str = "validation_error") -> None:
        super().__init__(message, status_code=400, code=code)


class DuplicateException(AppException):
    def __init__(self, message: str = "Resource already exists", code: str = "duplicate") -> None:
        super().__init__(message, status_code=409, code=code)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", code: str = "unauthorized") -> None:
        super().__init__(message, status_code=401, code=code)


class FileTypeException(AppException):
    def __init__(self, message: str = "Unsupported file type", code: str = "file_type_error") -> None:
        super().__init__(message, status_code=400, code=code)
