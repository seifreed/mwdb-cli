"""CLI tests: command generation, output modes, live and local execution."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from click.testing import CliRunner

from mwdb_cli import AsyncMwdbClient
from mwdb_cli.cli import main
from mwdb_cli.cli.specs import SPECS

from .checks import check, check_eq
from .conftest import LIVE_URL
from .constants import MISSING_SHA256
from .localserver import ScriptedResponse, scripted_server
from .test_client_local import BLOB_PAYLOAD, CONFIG_PAYLOAD, FILE_PAYLOAD, json_response


def invoke(url: str, credential: str, *args: str) -> tuple[int, str]:
    runner = CliRunner()
    result = runner.invoke(
        main, ["--url", url, "--api-key", credential, *args], catch_exceptions=False
    )
    return result.exit_code, result.output


def test_every_spec_maps_to_a_real_client_method() -> None:
    async def verify() -> None:
        async with AsyncMwdbClient("https://unused.example", "key") as client:
            for spec in SPECS:
                namespace = getattr(client, spec.namespace)
                check(
                    callable(getattr(namespace, spec.method, None)),
                    f"{spec.group} {spec.name} -> {spec.namespace}.{spec.method}",
                )

    asyncio.run(verify())


def test_every_command_has_help() -> None:
    runner = CliRunner()
    for spec in SPECS:
        result = runner.invoke(main, [spec.group, spec.name, "--help"])
        check_eq((spec.group, spec.name, result.exit_code), (spec.group, spec.name, 0))


def test_live_ping_and_json_mode(api_key: str) -> None:
    code, output = invoke(LIVE_URL, api_key, "server", "ping")
    check_eq(code, 0)
    check("ok" in output)
    runner = CliRunner()
    result = runner.invoke(
        main, ["--url", LIVE_URL, "--api-key", api_key, "--json", "server", "ping"]
    )
    check_eq(json.loads(result.output), {"status": "ok"})


def test_live_file_listing_and_detail(api_key: str) -> None:
    async def first_id() -> str:
        async with AsyncMwdbClient(LIVE_URL, api_key) as client:
            return (await client.files.list(count=1))[0].id

    identifier = asyncio.run(first_id())
    code, output = invoke(LIVE_URL, api_key, "file", "list", "--count", "2")
    check_eq(code, 0)
    check("id" in output)
    check(len(output.strip().splitlines()) >= 4)
    code, output = invoke(LIVE_URL, api_key, "--json", "file", "get", identifier)
    check_eq(code, 0)
    check_eq(json.loads(output)["id"], identifier)
    code, output = invoke(LIVE_URL, api_key, "search", f"file.sha256:{identifier}")
    check_eq(code, 0)
    code, output = invoke(LIVE_URL, api_key, "file", "download-token", identifier)
    check_eq(code, 0)
    check(len(output.strip()) > 10)


def test_live_error_reports_cleanly(api_key: str) -> None:
    runner = CliRunner()
    result = runner.invoke(
        main, ["--url", LIVE_URL, "--api-key", api_key, "file", "get", MISSING_SHA256]
    )
    check_eq(result.exit_code, 1)
    check("Error" in result.output)


def test_cli_void_and_table_free_outputs() -> None:
    with scripted_server([ScriptedResponse(200)]) as url:
        code, output = invoke(url, "key", "object", "delete", "a" * 64)
    check_eq(code, 0)
    check_eq(output.strip(), "ok")
    with scripted_server([json_response({"families": []})]) as url:
        code, output = invoke(url, "key", "config", "stats")
    check_eq(code, 0)
    check("families" in output)


def test_cli_table_with_missing_fields() -> None:
    partial = {key: value for key, value in FILE_PAYLOAD.items() if key != "file_name"}
    with scripted_server([json_response({"files": [partial]})]) as url:
        code, output = invoke(url, "key", "file", "list")
    check_eq(code, 0)
    check("id" in output)


def test_cli_upload_and_reupload(tmp_path: Path) -> None:
    source = tmp_path / "sample.bin"
    source.write_bytes(b"data")
    with scripted_server([json_response(FILE_PAYLOAD)]) as url:
        code, output = invoke(
            url,
            "key",
            "--json",
            "file",
            "upload",
            str(source),
            "--tags",
            "one",
            "--tags",
            "two",
            "--attributes",
            '[{"key": "source", "value": "unit"}]',
            "--share-3rd-party",
            "true",
        )
    check_eq(code, 0)
    check_eq(json.loads(output)["id"], "a" * 64)
    with scripted_server([json_response(FILE_PAYLOAD)]) as url:
        code, output = invoke(
            url, "key", "file", "reupload", "a" * 64, str(source), "--upload-as", "p"
        )
    check_eq(code, 0)


def test_cli_bulk_download(tmp_path: Path) -> None:
    plain_dir = tmp_path / "plain"
    responses = [
        ScriptedResponse(200, b"one"),
        ScriptedResponse(200, b"two"),
    ]
    with scripted_server(responses) as url:
        code, output = invoke(
            url,
            "key",
            "file",
            "download",
            "a" * 64,
            "b" * 64,
            "-o",
            str(plain_dir),
            "--jobs",
            "2",
            "--obfuscate",
        )
    check_eq(code, 0)
    check_eq(len(output.strip().splitlines()), 2)
    check((plain_dir / ("a" * 64)).exists())
    zip_dir = tmp_path / "zips"
    with scripted_server([ScriptedResponse(200, b"zipbytes")]) as url:
        code, output = invoke(
            url, "key", "file", "download", "c" * 64, "-o", str(zip_dir), "--zip"
        )
    check_eq(code, 0)
    check((zip_dir / (("c" * 64) + ".zip")).exists())
    destination = tmp_path / "by-token.bin"
    with scripted_server([ScriptedResponse(200, b"tok-bytes")]) as url:
        code, output = invoke(
            url, "key", "file", "download-by-token", "tok", str(destination)
        )
    check_eq(code, 0)
    check_eq(destination.read_bytes(), b"tok-bytes")


def test_cli_bulk_download_continues_past_a_missing_sample(tmp_path: Path) -> None:
    # A missing sample must not abort the whole batch: the available samples
    # are still written and the command exits non-zero. --jobs 1 keeps the
    # scripted responses aligned with the request order.
    out = tmp_path / "out"
    responses = [
        ScriptedResponse(200, b"first"),
        ScriptedResponse(404, b'{"message": "Object not found"}'),
        ScriptedResponse(200, b"third"),
    ]
    with scripted_server(responses) as url:
        code, output = invoke(
            url,
            "key",
            "file",
            "download",
            "a" * 64,
            "b" * 64,
            "c" * 64,
            "-o",
            str(out),
            "--jobs",
            "1",
        )
    check_eq(code, 1)
    check((out / ("a" * 64)).read_bytes() == b"first")
    check((out / ("c" * 64)).read_bytes() == b"third")
    check(not (out / ("b" * 64)).exists())


def test_cli_download_rejects_path_traversal(tmp_path: Path) -> None:
    output_dir = tmp_path / "safe"
    hostile = ["../escape", "sub/evil", f"{tmp_path}/abs", "..", ""]
    for identifier in hostile:
        code, output = invoke(
            "http://127.0.0.1:1",
            "key",
            "file",
            "download",
            identifier,
            "-o",
            str(output_dir),
        )
        check_eq((identifier, code), (identifier, 1))
        check("Unsafe download identifier" in output)
    # A well-formed hash is still accepted and written inside the output dir.
    with scripted_server([ScriptedResponse(200, b"safe")]) as url:
        code, output = invoke(
            url, "key", "file", "download", "d" * 64, "-o", str(output_dir)
        )
    check_eq(code, 0)
    written = output_dir / ("d" * 64)
    check(written.exists())
    check(written.resolve().parent == output_dir.resolve())


def test_cli_download_reports_filesystem_error_cleanly(tmp_path: Path) -> None:
    # A file where the output directory should be makes mkdir raise OSError;
    # the CLI must report it as a clean message, never a raw traceback.
    blocker = tmp_path / "blocker"
    blocker.write_bytes(b"not a directory")
    code, output = invoke(
        "http://127.0.0.1:1",
        "key",
        "file",
        "download",
        "d" * 64,
        "-o",
        str(blocker / "sub"),
    )
    check_eq(code, 1)
    check("Error" in output)
    check("Traceback" not in output)


def test_cli_download_zip_rejects_path_traversal(tmp_path: Path) -> None:
    code, output = invoke(
        "http://127.0.0.1:1",
        "key",
        "file",
        "download",
        "../evil",
        "-o",
        str(tmp_path / "safe"),
        "--zip",
    )
    check_eq(code, 1)
    check("Unsafe download identifier" in output)


def test_cli_toon_format_listing() -> None:
    # Real MWDB objects carry a nested ``tags`` list, so a listing renders with
    # TOON's ``-`` item fallback rather than a flat table.
    with scripted_server([json_response({"files": [FILE_PAYLOAD]})]) as url:
        code, output = invoke(url, "key", "--format", "toon", "file", "list")
    check_eq(code, 0)
    check(output.startswith("[1]:"))
    check("type: file" in output)


def test_cli_toon_format_tabular_scalar_list() -> None:
    scalar_objects = [
        {"id": "a", "type": "file"},
        {"id": "b", "type": "file"},
    ]
    with scripted_server([json_response({"files": scalar_objects})]) as url:
        code, output = invoke(url, "key", "--format", "toon", "file", "list")
    check_eq(code, 0)
    check(output.startswith("[2]{id,type}:"))


def test_cli_toon_format_dict() -> None:
    with scripted_server([json_response({"status": "ok"})]) as url:
        code, output = invoke(url, "key", "--format", "toon", "config", "stats")
    check_eq(code, 0)
    check_eq(output.strip(), "status: ok")


def test_cli_json_flag_is_alias_for_format_json() -> None:
    payload = {"id": "a" * 64, "type": "file", "tags": []}
    with scripted_server([json_response(payload)]) as url:
        via_flag = invoke(url, "key", "--json", "object", "get", "a" * 64)
    with scripted_server([json_response(payload)]) as url:
        via_format = invoke(url, "key", "--format", "json", "object", "get", "a" * 64)
    check_eq(via_flag[0], 0)
    check_eq(via_flag, via_format)


def test_cli_sarif_format_listing() -> None:
    objects = [{"id": "a" * 64, "type": "file", "tags": [{"tag": "emotet"}]}]
    with scripted_server([json_response({"files": objects})]) as url:
        code, output = invoke(url, "key", "--format", "sarif", "file", "list")
    check_eq(code, 0)
    document = json.loads(output)
    check_eq(document["version"], "2.1.0")
    check_eq(len(document["runs"][0]["results"]), 1)
    check_eq(document["runs"][0]["results"][0]["ruleId"], "emotet")


def test_cli_sarif_format_search() -> None:
    hits = [{"id": "b" * 64, "type": "file", "tags": []}]
    with scripted_server([json_response(hits)]) as url:
        code, output = invoke(url, "key", "--format", "sarif", "search", "tag:x")
    check_eq(code, 0)
    check_eq(json.loads(output)["runs"][0]["results"][0]["ruleId"], "file")


def test_cli_sarif_unsupported_command_errors() -> None:
    with scripted_server([json_response({"status": "ok"})]) as url:
        code, output = invoke(url, "key", "--format", "sarif", "server", "ping")
    check_eq(code, 1)
    check("SARIF output is not available for this command." in output)


def test_cli_void_result_is_valid_json_under_json_format() -> None:
    with scripted_server([ScriptedResponse(200)]) as url:
        code, output = invoke(url, "key", "--json", "object", "delete", "a" * 64)
    check_eq(code, 0)
    check_eq(json.loads(output), None)
    with scripted_server([ScriptedResponse(200)]) as url:
        toon_code, toon_output = invoke(
            url, "key", "--format", "toon", "object", "delete", "a" * 64
        )
    check_eq(toon_code, 0)
    check_eq(toon_output.strip(), "null")


def test_cli_malformed_json_argument_reports_cleanly() -> None:
    code, output = invoke(
        "http://127.0.0.1:1", "key", "config", "create", "fam", "{bad json"
    )
    check_eq(code, 2)
    check("invalid JSON" in output)


def test_cli_malformed_json_option_reports_cleanly() -> None:
    code, output = invoke(
        "http://127.0.0.1:1",
        "key",
        "karton",
        "resubmit",
        "a" * 64,
        "--arguments",
        "{nope",
    )
    check_eq(code, 2)
    check("invalid JSON" in output)


def test_cli_download_rejects_non_positive_jobs(tmp_path: Path) -> None:
    code, output = invoke(
        "http://127.0.0.1:1",
        "key",
        "file",
        "download",
        "a" * 64,
        "-o",
        str(tmp_path),
        "--jobs",
        "0",
    )
    check_eq(code, 2)
    check("jobs" in output.lower())


def test_cli_json_and_value_params(tmp_path: Path) -> None:
    with scripted_server([json_response(CONFIG_PAYLOAD)]) as url:
        code, output = invoke(
            url,
            "key",
            "--json",
            "config",
            "create",
            "testfamily",
            '{"c2": ["example.org"]}',
            "--tags",
            "one",
        )
    check_eq(code, 0)
    check_eq(json.loads(output)["family"], "testfamily")
    attribute = {"id": 1, "key": "k", "value": {"x": 1}}
    with scripted_server([json_response({"attributes": [attribute]})]) as url:
        code, output = invoke(
            url, "key", "--json", "attribute", "add", "a" * 64, "k", '{"x": 1}'
        )
    check_eq(code, 0)
    with scripted_server([json_response({"attributes": []})]) as url:
        code, output = invoke(
            url, "key", "--json", "attribute", "add", "a" * 64, "k", "plain-text"
        )
    check_eq(code, 0)
    with scripted_server([json_response({"id": "x", "status": "running"})]) as url:
        code, output = invoke(
            url,
            "key",
            "--json",
            "karton",
            "resubmit",
            "a" * 64,
            "--arguments",
            '{"priority": "high"}',
        )
    check_eq(code, 0)


def test_cli_bool_int_and_blob_commands() -> None:
    with scripted_server([json_response({"login": "someone"})]) as url:
        code, output = invoke(
            url, "key", "--json", "user", "update", "someone", "--disabled", "true"
        )
    check_eq(code, 0)
    with scripted_server([ScriptedResponse(200)]) as url:
        code, output = invoke(url, "key", "comment", "remove", "a" * 64, "5")
    check_eq(code, 0)
    with scripted_server([json_response(BLOB_PAYLOAD)]) as url:
        code, output = invoke(
            url, "key", "--json", "blob", "create", "notes.txt", "inject", "hello"
        )
    check_eq(code, 0)
    check_eq(json.loads(output)["id"], "e" * 64)
