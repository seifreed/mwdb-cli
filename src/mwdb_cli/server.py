"""Server metadata and remote-instance namespaces."""

from __future__ import annotations

from typing import Any

from .base import APIBase


class ServerAPI(APIBase):
    async def ping(self) -> dict[str, Any]:
        return await self._call_dict("ping")

    async def info(self) -> dict[str, Any]:
        return await self._call_dict("server_info")

    async def admin_info(self) -> dict[str, Any]:
        return await self._call_dict("server_admin_info")

    async def docs(self) -> dict[str, Any]:
        return await self._call_dict("server_docs")

    async def metrics(self) -> str:
        return await self._call_text("varz")


class RemotesAPI(APIBase):
    async def list(self) -> list[str]:
        return await self._call_str_list("remote_list", key="remotes")

    async def pull_file(self, remote_name: str, identifier: str) -> dict[str, Any]:
        return await self._call_dict(
            "remote_pull_file",
            {"remote_name": remote_name, "identifier": identifier},
        )

    async def pull_config(self, remote_name: str, identifier: str) -> dict[str, Any]:
        return await self._call_dict(
            "remote_pull_config",
            {"remote_name": remote_name, "identifier": identifier},
        )

    async def pull_blob(self, remote_name: str, identifier: str) -> dict[str, Any]:
        return await self._call_dict(
            "remote_pull_blob",
            {"remote_name": remote_name, "identifier": identifier},
        )

    async def push_file(self, remote_name: str, identifier: str) -> dict[str, Any]:
        return await self._call_dict(
            "remote_push_file",
            {"remote_name": remote_name, "identifier": identifier},
        )

    async def push_config(self, remote_name: str, identifier: str) -> dict[str, Any]:
        return await self._call_dict(
            "remote_push_config",
            {"remote_name": remote_name, "identifier": identifier},
        )

    async def push_blob(self, remote_name: str, identifier: str) -> dict[str, Any]:
        return await self._call_dict(
            "remote_push_blob",
            {"remote_name": remote_name, "identifier": identifier},
        )
