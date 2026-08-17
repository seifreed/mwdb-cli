"""Synchronous facade over the async client: one implementation, two APIs."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Iterator
from pathlib import Path
from types import TracebackType
from typing import Any

from .base import APIBase
from .client import AsyncMwdbClient


class SyncNamespace:
    """Runs the wrapped async namespace's coroutines on a private event loop."""

    def __init__(self, runner: asyncio.Runner, target: object) -> None:
        self._runner = runner
        self._target = target

    def __getattr__(self, name: str) -> Any:
        attribute = getattr(self._target, name)

        def invoke(*args: Any, **kwargs: Any) -> Any:
            result = attribute(*args, **kwargs)
            if inspect.isasyncgen(result):
                return self._drain(result)
            return self._runner.run(result)

        return invoke

    def _drain(self, generator: Any) -> Iterator[Any]:
        while True:
            try:
                yield self._runner.run(anext(generator))
            except StopAsyncIteration:
                return


class MwdbClient:
    """Synchronous client for the full MWDB Core API.

    Every async namespace is wrapped on demand, so the synchronous surface
    stays in sync with :class:`AsyncMwdbClient` without restating it here.
    """

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        *,
        config_path: Path | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        backoff: float = 1.0,
    ) -> None:
        self._runner = asyncio.Runner()
        self._client = AsyncMwdbClient(
            url,
            api_key,
            config_path=config_path,
            timeout=timeout,
            max_retries=max_retries,
            backoff=backoff,
        )
        self._namespaces: dict[str, SyncNamespace] = {}

    def __getattr__(self, name: str) -> SyncNamespace:
        if name.startswith("_"):
            raise AttributeError(name)
        target = getattr(self._client, name)
        if not isinstance(target, APIBase):
            raise AttributeError(name)
        wrapped = self._namespaces.get(name)
        if wrapped is None:
            wrapped = SyncNamespace(self._runner, target)
            self._namespaces[name] = wrapped
        return wrapped

    def close(self) -> None:
        self._runner.run(self._client.aclose())
        self._runner.close()

    def __enter__(self) -> MwdbClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
