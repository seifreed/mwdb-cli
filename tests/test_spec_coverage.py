"""Regression tests for the endpoint registry."""

from __future__ import annotations

from pathlib import Path

from mwdb_cli.endpoints import ENDPOINTS

from .checks import check, check_eq


def test_registry_has_all_122_operations() -> None:
    check_eq(len(ENDPOINTS), 122)


def test_every_operation_is_used_by_a_client_method() -> None:
    package_dir = Path(__file__).parent.parent / "src" / "mwdb_cli"
    source = "".join(
        module.read_text()
        for module in sorted(package_dir.glob("*.py"))
        if module.name != "endpoints.py"
    )
    unused = [name for name in ENDPOINTS if f'"{name}"' not in source]
    check(not unused, f"registry operations never referenced: {unused}")


def test_endpoint_path_formatting() -> None:
    check_eq(
        ENDPOINTS["object_get"].format(identifier="abc"),
        "/object/abc",
    )
