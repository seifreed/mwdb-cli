"""Shared plumbing for API namespace classes."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from .endpoints import ENDPOINTS
from .transport import AsyncTransport

type JsonList = list[dict[str, Any]]
type StrList = list[str]


def build_params(**kwargs: Any) -> dict[str, Any]:
    return {key: value for key, value in kwargs.items() if value is not None}


async def file_payload(
    source: Path | bytes, file_name: str | None
) -> tuple[str, bytes]:
    if isinstance(source, Path):
        content = await asyncio.to_thread(source.read_bytes)
        return file_name or source.name, content
    return file_name or "file", source


class APIBase:
    def __init__(self, transport: AsyncTransport) -> None:
        self._transport = transport

    async def _call(
        self,
        operation: str,
        path_params: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Any:
        endpoint = ENDPOINTS[operation]
        return await self._transport.request(
            endpoint.method, endpoint.format(**(path_params or {})), **kwargs
        )

    async def _call_dict(
        self,
        operation: str,
        path_params: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        payload = await self._call(operation, path_params, **kwargs)
        return dict(payload) if payload is not None else {}

    async def _call_list(
        self,
        operation: str,
        path_params: dict[str, str] | None = None,
        *,
        key: str | None = None,
        **kwargs: Any,
    ) -> JsonList:
        payload = await self._call(operation, path_params, **kwargs)
        if payload is None:
            return []
        return list(payload if key is None else payload[key])

    async def _call_str_list(
        self, operation: str, *, key: str, **kwargs: Any
    ) -> StrList:
        payload = await self._call(operation, **kwargs)
        if payload is None:
            return []
        return [str(name) for name in payload[key]]

    async def _call_text(
        self,
        operation: str,
        path_params: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> str:
        endpoint = ENDPOINTS[operation]
        return await self._transport.request_text(
            endpoint.method, endpoint.format(**(path_params or {})), **kwargs
        )

    async def _download(
        self,
        operation: str,
        path_params: dict[str, str],
        destination: Path,
        params: dict[str, Any] | None = None,
    ) -> Path:
        endpoint = ENDPOINTS[operation]
        return await self._transport.download(
            endpoint.format(**path_params), destination, params=params
        )
