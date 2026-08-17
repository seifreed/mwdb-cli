"""Transport tests: real local HTTP server for edge cases, live MWDB for semantics."""

from __future__ import annotations

from pathlib import Path

import pytest

from mwdb_cli.exceptions import (
    AuthError,
    MwdbConnectionError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from mwdb_cli.transport import AsyncTransport

from .checks import check, check_eq
from .conftest import LIVE_URL
from .localserver import ScriptedResponse, closed_port_url, scripted_server


async def test_live_ping() -> None:
    async with AsyncTransport(LIVE_URL) as transport:
        payload = await transport.request("GET", "/ping")
    check_eq(payload, {"status": "ok"})


async def test_live_auth_validate(api_key: str) -> None:
    async with AsyncTransport(LIVE_URL, api_key) as transport:
        payload = await transport.request("GET", "/auth/validate")
    check(isinstance(payload, dict))
    check("login" in payload)


async def test_live_invalid_credentials() -> None:
    async with AsyncTransport(LIVE_URL, "invalid") as transport:
        with pytest.raises(AuthError) as excinfo:
            await transport.request("GET", "/auth/validate")
    check_eq(excinfo.value.status_code, 401)


async def test_connection_refused() -> None:
    async with AsyncTransport(closed_port_url(), max_retries=0) as transport:
        with pytest.raises(MwdbConnectionError):
            await transport.request("GET", "/ping")


def test_connection_error_keeps_message_when_httpx_is_blank() -> None:
    # httpx timeout exceptions often stringify to "": the wrapper must still
    # carry a usable message instead of surfacing a bare "Error:".
    from httpx import ReadTimeout

    from mwdb_cli.transport import _connection_error

    check_eq(_connection_error(ReadTimeout("")).message, "ReadTimeout")
    check_eq(_connection_error(ReadTimeout("boom")).message, "boom")


async def test_retry_on_429_then_success() -> None:
    responses = [
        ScriptedResponse(429, headers={"Retry-After": "0"}),
        ScriptedResponse(200, b'{"status": "ok"}'),
    ]
    with scripted_server(responses) as url:
        async with AsyncTransport(url, backoff=0.0) as transport:
            payload = await transport.request("GET", "/ping")
    check_eq(payload, {"status": "ok"})


async def test_rate_limit_exhausts_retries() -> None:
    responses = [
        ScriptedResponse(429, b'{"message": "too fast"}'),
        ScriptedResponse(429, b'{"message": "too fast"}'),
    ]
    with scripted_server(responses) as url:
        async with AsyncTransport(url, backoff=0.0, max_retries=1) as transport:
            with pytest.raises(RateLimitError) as excinfo:
                await transport.request("GET", "/ping")
    check_eq(excinfo.value.message, "too fast")


async def test_retry_on_503_then_success() -> None:
    responses = [
        ScriptedResponse(503),
        ScriptedResponse(200, b'{"status": "ok"}'),
    ]
    with scripted_server(responses) as url:
        async with AsyncTransport(url, backoff=0.0) as transport:
            payload = await transport.request("GET", "/ping")
    check_eq(payload, {"status": "ok"})


async def test_server_error_without_retryable_status() -> None:
    with scripted_server([ScriptedResponse(500, b"crashed")]) as url:
        async with AsyncTransport(url, max_retries=0) as transport:
            with pytest.raises(ServerError) as excinfo:
                await transport.request("GET", "/ping")
    check_eq(excinfo.value.message, "crashed")


async def test_error_message_from_json_payload() -> None:
    with scripted_server([ScriptedResponse(404, b'{"message": "gone"}')]) as url:
        async with AsyncTransport(url, max_retries=0) as transport:
            with pytest.raises(NotFoundError) as excinfo:
                await transport.request("GET", "/object/x")
    check_eq(excinfo.value.message, "gone")


async def test_error_message_from_non_dict_json() -> None:
    with scripted_server([ScriptedResponse(404, b"[1, 2]")]) as url:
        async with AsyncTransport(url, max_retries=0) as transport:
            with pytest.raises(NotFoundError) as excinfo:
                await transport.request("GET", "/object/x")
    check_eq(excinfo.value.message, "HTTP 404")


async def test_error_message_from_empty_body() -> None:
    with scripted_server([ScriptedResponse(404)]) as url:
        async with AsyncTransport(url, max_retries=0) as transport:
            with pytest.raises(NotFoundError) as excinfo:
                await transport.request("GET", "/object/x")
    check_eq(excinfo.value.message, "HTTP 404")


async def test_non_json_success_body_raises_server_error() -> None:
    with scripted_server([ScriptedResponse(200, b"<html>not json</html>")]) as url:
        async with AsyncTransport(url) as transport:
            with pytest.raises(ServerError) as excinfo:
                await transport.request("GET", "/ping")
    check_eq(excinfo.value.status_code, 200)


async def test_empty_success_body_returns_none() -> None:
    with scripted_server([ScriptedResponse(200)]) as url:
        async with AsyncTransport(url) as transport:
            payload = await transport.request("DELETE", "/object/x")
    check_eq(payload, None)


async def test_request_text() -> None:
    with scripted_server([ScriptedResponse(200, b"metrics 1")]) as url:
        async with AsyncTransport(url) as transport:
            text = await transport.request_text("GET", "/varz")
    check_eq(text, "metrics 1")


async def test_download_writes_file(tmp_path: Path) -> None:
    with scripted_server([ScriptedResponse(200, b"binary-data")]) as url:
        async with AsyncTransport(url) as transport:
            destination = await transport.download("/download/t", tmp_path / "out.bin")
    check_eq(destination.read_bytes(), b"binary-data")


async def test_download_error_status(tmp_path: Path) -> None:
    destination = tmp_path / "out.bin"
    with scripted_server([ScriptedResponse(404, b'{"message": "gone"}')]) as url:
        async with AsyncTransport(url) as transport:
            with pytest.raises(NotFoundError):
                await transport.download("/download/t", destination)
    check(not destination.exists())
    check(not destination.with_name("out.bin.part").exists())


async def test_download_midstream_failure_leaves_no_partial(tmp_path: Path) -> None:
    destination = tmp_path / "sample.bin"
    truncated = ScriptedResponse(200, b"short", declared_length=4096)
    with scripted_server([truncated]) as url:
        async with AsyncTransport(url) as transport:
            with pytest.raises(MwdbConnectionError):
                await transport.download("/download/t", destination)
    check(not destination.exists())
    check(not destination.with_name("sample.bin.part").exists())


async def test_download_replaces_existing_file(tmp_path: Path) -> None:
    destination = tmp_path / "out.bin"
    destination.write_bytes(b"stale")
    with scripted_server([ScriptedResponse(200, b"fresh")]) as url:
        async with AsyncTransport(url) as transport:
            await transport.download("/download/t", destination)
    check_eq(destination.read_bytes(), b"fresh")


async def test_download_connection_error(tmp_path: Path) -> None:
    async with AsyncTransport(closed_port_url()) as transport:
        with pytest.raises(MwdbConnectionError):
            await transport.download("/download/t", tmp_path / "out.bin")
