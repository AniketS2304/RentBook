from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base application exception with standardized code and errors."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        code: str = "ERROR",
        errors: Optional[List[Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.code = code
        self.errors = errors or []


class NotFoundError(AppException):
    def __init__(
        self,
        detail: str = "Resource not found",
        code: str = "NOT_FOUND",
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            code=code,
        )


class UnauthorizedError(AppException):
    def __init__(
        self,
        detail: str = "Could not validate credentials",
        code: str = "UNAUTHORIZED",
        headers: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            code=code,
            headers=headers or {"WWW-Authenticate": "Bearer"},
        )


class InvalidCredentialsError(AppException):
    def __init__(
        self,
        detail: str = "Invalid email or password",
        code: str = "INVALID_CREDENTIALS",
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            code=code,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ConflictError(AppException):
    def __init__(
        self,
        detail: str = "Resource already exists",
        code: str = "CONFLICT",
        errors: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            code=code,
            errors=errors,
        )


class ForbiddenError(AppException):
    def __init__(
        self,
        detail: str = "Access forbidden",
        code: str = "FORBIDDEN",
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            code=code,
        )


class BadRequestError(AppException):
    def __init__(
        self,
        detail: str = "Bad request",
        code: str = "BAD_REQUEST",
        errors: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            code=code,
            errors=errors,
        )
