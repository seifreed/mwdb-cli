"""Tests for HTTP status to exception mapping."""

from __future__ import annotations

import pytest

from mwdb_cli.exceptions import (
    AuthError,
    ConflictError,
    ForbiddenError,
    MwdbError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
    error_for_status,
)

from .checks import check, check_eq


@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        (400, ValidationError),
        (401, AuthError),
        (403, ForbiddenError),
        (404, NotFoundError),
        (409, ConflictError),
        (422, ValidationError),
        (429, RateLimitError),
        (500, ServerError),
        (503, ServerError),
        (418, MwdbError),
    ],
)
def test_error_for_status(status: int, error_type: type[MwdbError]) -> None:
    error = error_for_status(status, "boom")
    check(type(error) is error_type, f"{status} mapped to {type(error).__name__}")
    check_eq(error.status_code, status)
    check_eq(error.message, "boom")
    check(isinstance(error, MwdbError))
