"""Tests for the bulk concurrency helper."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import pytest

from mwdb_cli.bulk import run_limited

from .checks import check, check_eq


def doubler(value: int) -> Callable[[], Awaitable[int]]:
    async def run() -> int:
        await asyncio.sleep(0)
        return value * 2

    return run


async def test_run_limited_preserves_order_and_runs_all() -> None:
    results = await run_limited([doubler(v) for v in range(5)], limit=2)
    check_eq(results, [0, 2, 4, 6, 8])


async def test_run_limited_caps_concurrency() -> None:
    active = 0
    peak = 0

    async def task() -> None:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1

    await run_limited([task for _ in range(6)], limit=2)
    check(peak <= 2)


@pytest.mark.parametrize("limit", [0, -1])
async def test_run_limited_rejects_non_positive_limit(limit: int) -> None:
    with pytest.raises(ValueError):
        await run_limited([doubler(1)], limit=limit)
