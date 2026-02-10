from fastapi import HTTPException, status
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or message
        super().__init__(self.message)


class ValidationException(AppException):
    """Validation error exception."""

    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(
            message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class AuthenticationException(AppException):
    """Authentication error exception."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationException(AppException):
    """Authorization error exception."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class NotFoundException(AppException):
    """Not found exception."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictException(AppException):
    """Conflict exception."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(
            message,
            status_code=status.HTTP_409_CONFLICT,
        )


class ServiceUnavailableException(AppException):
    """Service unavailable exception."""

    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(
            message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class TimeoutException(AppException):
    """Timeout exception."""

    def __init__(self, message: str = "Request timed out"):
        super().__init__(
            message,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        )


def create_error_response(
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "error": message,
        "detail": detail or message,
        "status_code": status_code,
    }


def log_error(
    error: Exception,
    context: Optional[str] = None,
    user_id: Optional[str] = None,
) -> None:
    """Log error with context."""
    error_msg = f"{context}: {str(error)}" if context else str(error)
    if user_id:
        error_msg = f"[User: {user_id}] {error_msg}"
    logger.error(error_msg, exc_info=True)
