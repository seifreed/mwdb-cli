"""Concurrency helpers for bulk operations."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence


async def run_limited[T](
    tasks: Sequence[Callable[[], Awaitable[T]]], limit: int
) -> list[T]:
    """Run awaitable factories concurrently, at most ``limit`` at a time.

    ``limit`` must be at least 1; a non-positive value would otherwise
    deadlock (``Semaphore(0)``) or raise deep inside asyncio.
    """
    if limit < 1:
        raise ValueError("limit must be >= 1")
    semaphore = asyncio.Semaphore(limit)

    async def guarded(task: Callable[[], Awaitable[T]]) -> T:
        async with semaphore:
            return await task()

    return list(await asyncio.gather(*(guarded(task) for task in tasks)))
