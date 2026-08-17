"""Exception hierarchy mapping MWDB API errors to typed Python exceptions."""

from __future__ import annotations


class MwdbError(Exception):
    """Base error for all MWDB client failures."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class MwdbConnectionError(MwdbError):
    """Network-level failure: DNS, refused connection, timeout."""


class ValidationError(MwdbError):
    """Request rejected as malformed (HTTP 400/422)."""


class AuthError(MwdbError):
    """Missing or invalid credentials (HTTP 401)."""


class ForbiddenError(MwdbError):
    """Authenticated but not allowed (HTTP 403)."""


class NotFoundError(MwdbError):
    """Resource does not exist or is not accessible (HTTP 404)."""


class ConflictError(MwdbError):
    """Resource already exists or conflicting state (HTTP 409)."""


class RateLimitError(MwdbError):
    """Rate limit still exceeded after retries (HTTP 429)."""


class ServerError(MwdbError):
    """Server-side failure (HTTP 5xx)."""


_STATUS_ERRORS: dict[int, type[MwdbError]] = {
    400: ValidationError,
    401: AuthError,
    403: ForbiddenError,
    404: NotFoundError,
    409: ConflictError,
    422: ValidationError,
    429: RateLimitError,
}


def error_for_status(status_code: int, message: str) -> MwdbError:
    """Build the typed exception matching an HTTP error status."""
    if status_code >= 500:
        return ServerError(message, status_code)
    error_type = _STATUS_ERRORS.get(status_code, MwdbError)
    return error_type(message, status_code)
