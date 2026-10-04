"""
Application exceptions
"""

from typing import Any, Dict, Optional

# Import HTTP constants first
from .constants import (
    HTTP_BAD_REQUEST,
    HTTP_FORBIDDEN,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_NOT_FOUND,
    HTTP_SERVICE_UNAVAILABLE,
    HTTP_TOO_MANY_REQUESTS,
    HTTP_UNAUTHORIZED,
)


class BlindSpotException(Exception):
    """Base exception for Blind Spot application."""

    def __init__(
        self,
        message: str,
        status_code: int = HTTP_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BlindSpotException):
    """Validation error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=HTTP_BAD_REQUEST,
            details=details
        )


class AuthenticationError(BlindSpotException):
    """Authentication error."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=HTTP_UNAUTHORIZED
        )


class AuthorizationError(BlindSpotException):
    """Authorization error."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=HTTP_FORBIDDEN
        )


class NotFoundError(BlindSpotException):
    """Resource not found error."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            status_code=HTTP_NOT_FOUND
        )


class RateLimitError(BlindSpotException):
    """Rate limit exceeded error."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=HTTP_TOO_MANY_REQUESTS
        )


class GeminiAPIError(BlindSpotException):
    """Gemini API error."""

    def __init__(self, message: str = "Gemini API error"):
        super().__init__(
            message=message,
            status_code=HTTP_SERVICE_UNAVAILABLE
        )


class ConfigurationError(BlindSpotException):
    """Configuration error."""

    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=HTTP_INTERNAL_SERVER_ERROR
        )