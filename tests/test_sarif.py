"""Tests for the SARIF 2.1.0 encoder and applicability check."""

from __future__ import annotations

import pytest

from mwdb_cli import sarif
from mwdb_cli.models import ConfigItem, FileItem

from .checks import check, check_eq

FILE_PAYLOAD = {
    "id": "a" * 64,
    "type": "file",
    "tags": [{"tag": "emotet"}, {"tag": "trojan"}],
    "file_name": "sample.bin",
    "sha256": "a" * 64,
}
CONFIG_PAYLOAD = {
    "id": "b" * 64,
    "type": "static_config",
    "family": "emotet",
    "tags": [],
}


def test_is_supported() -> None:
    check(sarif.is_supported(FileItem.from_dict(FILE_PAYLOAD)))
    check(sarif.is_supported([FileItem.from_dict(FILE_PAYLOAD)]))
    check(sarif.is_supported([FILE_PAYLOAD]))
    check(not sarif.is_supported({"status": "ok"}))
    check(not sarif.is_supported([]))
    check(not sarif.is_supported(["plain", "strings"]))
    check(not sarif.is_supported("text"))


def test_encode_single_file_item() -> None:
    document = sarif.encode(FileItem.from_dict(FILE_PAYLOAD))
    check_eq(document["version"], "2.1.0")
    check("$schema" in document)
    run = document["runs"][0]
    check_eq(run["tool"]["driver"]["name"], "mwdb-cli")
    check("version" in run["tool"]["driver"])
    check_eq(len(run["results"]), 1)
    result = run["results"][0]
    check_eq(result["ruleId"], "emotet")
    check_eq(result["level"], "warning")
    check_eq(
        result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"],
        "a" * 64,
    )
    check("sample.bin" in result["message"]["text"])
    check_eq(result["properties"]["file_name"], "sample.bin")


def test_encode_uses_family_then_tag_then_type() -> None:
    by_family = sarif.encode(ConfigItem.from_dict(CONFIG_PAYLOAD))
    check_eq(by_family["runs"][0]["results"][0]["ruleId"], "emotet")
    by_type = sarif.encode([{"id": "c" * 64, "type": "file", "tags": []}])
    check_eq(by_type["runs"][0]["results"][0]["ruleId"], "file")


def test_encode_dedupes_rules_and_lists_artifacts() -> None:
    document = sarif.encode(
        [FILE_PAYLOAD, {**FILE_PAYLOAD, "id": "d" * 64, "sha256": "d" * 64}]
    )
    run = document["runs"][0]
    check_eq(len(run["results"]), 2)
    check_eq(len(run["artifacts"]), 2)
    # Both share ruleId "emotet", so the rules table holds a single entry.
    check_eq(len(run["tool"]["driver"]["rules"]), 1)
    check_eq(run["tool"]["driver"]["rules"][0]["id"], "emotet")


def test_encode_rejects_unsupported() -> None:
    with pytest.raises(ValueError):
        sarif.encode({"status": "ok"})
