"""Assertion helpers used instead of the bare assert statement."""

from __future__ import annotations

from typing import Any


def check(condition: bool, message: str = "condition not met") -> None:
    if not condition:
        raise AssertionError(message)


def check_eq(actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{actual!r} != {expected!r}")
