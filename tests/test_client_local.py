"""Success paths for mutating operations, served by a real local HTTP server."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mwdb_cli import AsyncMwdbClient, MwdbClient

from .checks import check, check_eq
from .localserver import ScriptedResponse, scripted_server

FILE_PAYLOAD = {
    "id": "a" * 64,
    "type": "file",
    "upload_time": "2026-07-24T00:00:00",
    "tags": [{"tag": "test"}],
    "file_name": "sample.bin",
    "file_size": 4,
    "file_type": "data",
    "md5": "b" * 32,
    "sha1": "c" * 40,
    "sha256": "a" * 64,
}
CONFIG_PAYLOAD = {
    "id": "d" * 64,
    "type": "static_config",
    "family": "testfamily",
    "config_type": "static",
    "tags": [],
}
BLOB_PAYLOAD = {
    "id": "e" * 64,
    "type": "text_blob",
    "blob_name": "notes.txt",
    "blob_size": 5,
    "blob_type": "inject",
    "last_seen": "2026-07-24T00:00:00",
    "tags": [],
}


def json_response(payload: Any, status: int = 200) -> ScriptedResponse:
    return ScriptedResponse(status, json.dumps(payload).encode())


def token_response(value: str) -> ScriptedResponse:
    return json_response({"token": value})


async def test_empty_success_body_yields_empty_container() -> None:
    # Several operations (OAuth register, remote push, /docs, ...) are
    # documented with an empty 200 body; the client must return an empty
    # dict/list instead of crashing on dict(None) / list(None).
    empty = ScriptedResponse(200, b"")
    with scripted_server([empty, empty, empty, empty]) as url:
        async with AsyncMwdbClient(url, "key") as client:
            registered = await client.oauth.register_provider({"name": "x"})
            pushed = await client.remotes.push_file("remote", "a" * 64)
            providers = await client.oauth.providers()
            found = await client.search_api.search("family:x")
    check_eq(registered, {})
    check_eq(pushed, {})
    check_eq(providers, [])
    check_eq(found, [])


async def test_file_upload_from_bytes() -> None:
    with scripted_server([json_response(FILE_PAYLOAD)]) as url:
        async with AsyncMwdbClient(url, "key") as client:
            item = await client.files.upload(b"data", tags=["test"])
    check_eq(item.sha256, "a" * 64)
    check_eq(item.tags, ["test"])


async def test_file_upload_from_path(tmp_path: Path) -> None:
    source = tmp_path / "sample.bin"
    source.write_bytes(b"data")
    with scripted_server([json_response(FILE_PAYLOAD)]) as url:
        async with AsyncMwdbClient(url, "key") as client:
            item = await client.files.upload(source, parent="f" * 64)
    check_eq(item.file_name, "sample.bin")


async def test_file_reupload_with_options() -> None:
    with scripted_server([json_response(FILE_PAYLOAD)]) as url:
        async with AsyncMwdbClient(url, "key") as client:
            item = await client.files.reupload(
                "a" * 64,
                b"data",
                metakeys=[{"key": "source", "value": "unit"}],
                upload_as="public",
            )
    check_eq(item.id, "a" * 64)


async def test_file_reupload_plain() -> None:
    with scripted_server([json_response(FILE_PAYLOAD)]) as url:
        async with AsyncMwdbClient(url, "key") as client:
            item = await client.files.reupload("a" * 64, b"data")
    check_eq(item.id, "a" * 64)


async def test_file_download_variants(tmp_path: Path) -> None:
    responses = [
        ScriptedResponse(200, b"plain"),
        ScriptedResponse(200, b"obfuscated"),
        token_response("download-tok"),
        ScriptedResponse(200, b"zipped"),
        token_response("zip-tok"),
        ScriptedResponse(200, b"by-token"),
    ]
    with scripted_server(responses) as url:
        async with AsyncMwdbClient(url, "key") as client:
            plain = await client.files.download("a" * 64, tmp_path / "plain.bin")
            obfuscated = await client.files.download(
                "a" * 64, tmp_path / "obf.bin", obfuscate=True
            )
            token = await client.files.download_token("a" * 64)
            zipped = await client.files.download_zip("a" * 64, tmp_path / "f.zip")
            zip_token = await client.files.download_zip_token("a" * 64)
            by_token = await client.files.download_by_token(
                "download-tok", tmp_path / "tok.bin"
            )
    check_eq(plain.read_bytes(), b"plain")
    check_eq(obfuscated.read_bytes(), b"obfuscated")
    check_eq(token, "download-tok")
    check_eq(zipped.read_bytes(), b"zipped")
    check_eq(zip_token, "zip-tok")
    check_eq(by_token.read_bytes(), b"by-token")


async def test_request_sample_success() -> None:
    with scripted_server([json_response({"url": "/api/download/tok"})]) as url:
        async with AsyncMwdbClient(url, "key") as client:
            payload = await client.files.request_sample("a" * 64)
    check_eq(payload["url"], "/api/download/tok")


async def test_config_create_and_put() -> None:
    responses = [json_response(CONFIG_PAYLOAD), json_response(CONFIG_PAYLOAD)]
    with scripted_server(responses) as url:
        async with AsyncMwdbClient(url, "key") as client:
            created = await client.configs.create(
                "testfamily", {"c2": ["example.org"]}, config_type="static"
            )
            updated = await client.configs.put(
                created.id, {"family": "testfamily", "cfg": {"c2": []}}
            )
    check_eq(created.family, "testfamily")
    check_eq(updated.id, "d" * 64)


async def test_blob_create_and_put() -> None:
    responses = [json_response(BLOB_PAYLOAD), json_response(BLOB_PAYLOAD)]
    with scripted_server(responses) as url:
        async with AsyncMwdbClient(url, "key") as client:
            created = await client.blobs.create("notes.txt", "inject", "hello")
            updated = await client.blobs.put(
                created.id,
                {"blob_name": "notes.txt", "blob_type": "inject", "content": "hi"},
            )
    check_eq(created.blob_name, "notes.txt")
    check_eq(updated.id, "e" * 64)


async def test_object_delete_success() -> None:
    with scripted_server([ScriptedResponse(200)]) as url:
        async with AsyncMwdbClient(url, "key") as client:
            await client.objects.delete("a" * 64)


def test_sync_client_calls_and_iteration() -> None:
    page_one = {"files": [FILE_PAYLOAD, {**FILE_PAYLOAD, "id": "b" * 64}]}
    page_two: dict[str, Any] = {"files": []}
    responses = [
        json_response(FILE_PAYLOAD),
        json_response(page_one),
        json_response(page_two),
    ]
    with scripted_server(responses) as url, MwdbClient(url, "key") as client:
        detail = client.files.get("a" * 64)
        items = list(client.files.iterate(chunk_size=2))
    check_eq(detail.id, "a" * 64)
    check_eq(len(items), 2)
    check(items[1].id == "b" * 64)


def test_sync_client_rejects_non_namespace_attributes() -> None:
    with MwdbClient("https://unused.example", "key") as client:
        private_error = _attribute_error(lambda: client._does_not_exist)
        non_namespace_error = _attribute_error(lambda: client.transport)
    check(private_error)
    check(non_namespace_error)


def _attribute_error(access: Any) -> bool:
    try:
        access()
    except AttributeError:
        return True
    return False
