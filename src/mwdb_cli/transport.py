"""Async HTTP transport: authentication, retries and error mapping."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import TracebackType
from typing import Any

import httpx

from .exceptions import (
    MwdbConnectionError,
    RateLimitError,
    ServerError,
    error_for_status,
)

RETRYABLE_STATUSES = frozenset({429, 502, 503, 504})


def _connection_error(exc: httpx.HTTPError) -> MwdbConnectionError:
    """Wrap a transport failure, keeping a message even when httpx's is blank.

    Timeout exceptions (``ReadTimeout``, ``ConnectTimeout``) commonly stringify
    to ``""``, which would otherwise reach the user as a bare ``Error:``; fall
    back to the exception class name so the cause is always visible.
    """
    return MwdbConnectionError(str(exc) or type(exc).__name__)


def _error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text or f"HTTP {response.status_code}"
    if isinstance(payload, dict) and "message" in payload:
        return str(payload["message"])
    return f"HTTP {response.status_code}"


def _retry_delay(response: httpx.Response, attempt: int, backoff: float) -> float:
    retry_after = response.headers.get("Retry-After")
    if retry_after is not None and retry_after.isdigit():
        return float(retry_after)
    return backoff * float(2**attempt)


class AsyncTransport:
    """Thin wrapper over httpx.AsyncClient targeting an MWDB API root."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        *,
        timeout: float = 60.0,
        max_retries: int = 3,
        backoff: float = 1.0,
    ) -> None:
        headers = {}
        if api_key is not None:
            headers["Authorization"] = f"Bearer {api_key}"
        self._max_retries = max_retries
        self._backoff = backoff
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/") + "/api",
            headers=headers,
            timeout=timeout,
            follow_redirects=True,
        )

    async def _send(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        files: Any | None = None,
        data: dict[str, Any] | None = None,
    ) -> httpx.Response:
        attempt = 0
        while True:
            try:
                response = await self._client.request(
                    method, path, params=params, json=json, files=files, data=data
                )
            except httpx.HTTPError as exc:
                raise _connection_error(exc) from exc
            if (
                response.status_code in RETRYABLE_STATUSES
                and attempt < self._max_retries
            ):
                await asyncio.sleep(_retry_delay(response, attempt, self._backoff))
                attempt += 1
                continue
            break
        if response.status_code == 429:
            raise RateLimitError(_error_message(response), 429)
        if response.status_code >= 400:
            raise error_for_status(response.status_code, _error_message(response))
        return response

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
        files: Any | None = None,
        data: dict[str, Any] | None = None,
    ) -> Any:
        """Perform a request and return the decoded JSON body."""
        response = await self._send(
            method, path, params=params, json=json, files=files, data=data
        )
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise ServerError(
                f"server returned a non-JSON response (HTTP {response.status_code})",
                response.status_code,
            ) from exc

    async def request_text(
        self, method: str, path: str, *, params: dict[str, Any] | None = None
    ) -> str:
        """Perform a request and return the raw text body."""
        response = await self._send(method, path, params=params)
        return response.text

    async def download(
        self, path: str, destination: Path, *, params: dict[str, Any] | None = None
    ) -> Path:
        """Stream a GET response body into a file without buffering in memory.

        The body is written to a sibling ``.part`` file and atomically moved
        into place only after a complete transfer, so a mid-stream failure
        never leaves a truncated sample (or clobbers an existing file) on disk.
        """
        partial = destination.with_name(destination.name + ".part")
        try:
            async with self._client.stream("GET", path, params=params) as response:
                if response.status_code >= 400:
                    await response.aread()
                    raise error_for_status(
                        response.status_code, _error_message(response)
                    )
                with partial.open("wb") as output:
                    async for chunk in response.aiter_bytes():
                        await asyncio.to_thread(output.write, chunk)
        except httpx.HTTPError as exc:
            partial.unlink(missing_ok=True)
            raise _connection_error(exc) from exc
        except BaseException:
            partial.unlink(missing_ok=True)
            raise
        partial.replace(destination)
        return destination

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncTransport:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()
