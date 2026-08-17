"""Live and local tests for server metadata and remote namespaces."""

from __future__ import annotations

import pytest

from mwdb_cli import AsyncMwdbClient
from mwdb_cli.exceptions import ForbiddenError, NotFoundError

from .checks import check, check_eq
from .conftest import LIVE_URL
from .constants import MISSING_SHA256
from .localserver import ScriptedResponse, scripted_server
from .test_client_local import json_response


async def test_server_reads(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        ping = await client.server.ping()
        info = await client.server.info()
        docs = await client.server.docs()
        remotes = await client.remotes.list()
    check_eq(ping, {"status": "ok"})
    check("server_version" in info)
    check("paths" in docs)
    check(isinstance(remotes, list))


async def test_server_admin_requires_capability(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        with pytest.raises(ForbiddenError):
            await client.server.admin_info()
        with pytest.raises(ForbiddenError):
            await client.server.metrics()


async def test_remote_operations_unknown_remote(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        with pytest.raises(NotFoundError):
            await client.remotes.pull_file("no-such-remote", MISSING_SHA256)
        with pytest.raises(NotFoundError):
            await client.remotes.push_file("no-such-remote", MISSING_SHA256)


async def test_server_and_remote_success_paths() -> None:
    file_payload = {"id": "a" * 64, "type": "file"}
    config_payload = {"id": "b" * 64, "type": "static_config"}
    blob_payload = {"id": "c" * 64, "type": "text_blob"}
    responses = [
        json_response({"active_plugins": {}}),
        ScriptedResponse(200, b"mwdb_metric 1"),
        json_response(file_payload),
        json_response(config_payload),
        json_response(blob_payload),
        json_response(file_payload),
        json_response(config_payload),
        json_response(blob_payload),
    ]
    with scripted_server(responses) as url:
        async with AsyncMwdbClient(url, "key") as client:
            admin_info = await client.server.admin_info()
            metrics = await client.server.metrics()
            pulled_file = await client.remotes.pull_file("mirror", "a" * 64)
            pulled_config = await client.remotes.pull_config("mirror", "b" * 64)
            pulled_blob = await client.remotes.pull_blob("mirror", "c" * 64)
            pushed_file = await client.remotes.push_file("mirror", "a" * 64)
            pushed_config = await client.remotes.push_config("mirror", "b" * 64)
            pushed_blob = await client.remotes.push_blob("mirror", "c" * 64)
    check("active_plugins" in admin_info)
    check_eq(metrics, "mwdb_metric 1")
    check_eq(pulled_file["id"], "a" * 64)
    check_eq(pulled_config["id"], "b" * 64)
    check_eq(pulled_blob["id"], "c" * 64)
    check_eq(pushed_file["id"], "a" * 64)
    check_eq(pushed_config["id"], "b" * 64)
    check_eq(pushed_blob["id"], "c" * 64)
