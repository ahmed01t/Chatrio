"""
Custom Application Exceptions.

Defines standardized exceptions adhering to the error response specification
in `docs/conventions.md`:
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable message",
        "details": {}
    }
}
"""

from typing import Any


class AppException(Exception):
    """Base exception for all application errors."""
# def init is 
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


class BadRequestException(AppException):
    def __init__(
        self,
        message: str = "Bad request",
        code: str = "BAD_REQUEST",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status_code=400, code=code, message=message, details=details)


class UnauthorizedException(AppException):
    def __init__(
        self,
        message: str = "Could not validate credentials",
        code: str = "UNAUTHORIZED",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status_code=401, code=code, message=message, details=details)


class ForbiddenException(AppException):
    def __init__(
        self,
        message: str = "You do not have permission to perform this action",
        code: str = "FORBIDDEN",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status_code=403, code=code, message=message, details=details)


class NotFoundException(AppException):
    def __init__(
        self,
        message: str = "Resource not found",
        code: str = "NOT_FOUND",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status_code=404, code=code, message=message, details=details)


class ConflictException(AppException):
    def __init__(
        self,
        message: str = "Resource conflict",
        code: str = "CONFLICT",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(status_code=409, code=code, message=message, details=details)
