"""Tests for settings resolution precedence."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from mwdb_cli.config import (
    DEFAULT_URL,
    ENV_API_KEY,
    ENV_URL,
    default_config_path,
    load_settings,
)
from mwdb_cli.exceptions import ValidationError

from .checks import check, check_eq


@pytest.fixture
def clean_env() -> Iterator[None]:
    saved = {
        name: os.environ.pop(name)
        for name in (ENV_URL, ENV_API_KEY)
        if name in os.environ
    }
    try:
        yield
    finally:
        for name in (ENV_URL, ENV_API_KEY):
            os.environ.pop(name, None)
        os.environ.update(saved)


def write_config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "mwdb.toml"
    path.write_text(content)
    return path


def test_defaults_without_any_source(clean_env: None, tmp_path: Path) -> None:
    settings = load_settings(config_path=tmp_path / "missing.toml")
    check_eq(settings.url, DEFAULT_URL)
    check_eq(settings.api_key, None)


def test_malformed_toml_raises_validation_error(
    clean_env: None, tmp_path: Path
) -> None:
    path = write_config(tmp_path, "this is = not = valid toml ][")
    with pytest.raises(ValidationError):
        load_settings(config_path=path)


def test_non_table_section_raises_validation_error(
    clean_env: None, tmp_path: Path
) -> None:
    path = write_config(tmp_path, 'mwdb = "not a table"')
    with pytest.raises(ValidationError):
        load_settings(config_path=path)


def test_config_file_values(clean_env: None, tmp_path: Path) -> None:
    path = write_config(
        tmp_path, '[mwdb]\nurl = "https://example.org"\napi_key = "from-file"\n'
    )
    settings = load_settings(config_path=path)
    check_eq(settings.url, "https://example.org")
    check_eq(settings.api_key, "from-file")


def test_config_file_without_section(clean_env: None, tmp_path: Path) -> None:
    path = write_config(tmp_path, '[other]\nurl = "https://ignored.example"\n')
    settings = load_settings(config_path=path)
    check_eq(settings.url, DEFAULT_URL)


def test_environment_overrides_file(clean_env: None, tmp_path: Path) -> None:
    path = write_config(tmp_path, '[mwdb]\nurl = "https://file.example"\n')
    os.environ[ENV_URL] = "https://env.example"
    os.environ[ENV_API_KEY] = "from-env"
    settings = load_settings(config_path=path)
    check_eq(settings.url, "https://env.example")
    check_eq(settings.api_key, "from-env")


def test_arguments_override_everything(clean_env: None, tmp_path: Path) -> None:
    os.environ[ENV_URL] = "https://env.example"
    os.environ[ENV_API_KEY] = "from-env"
    settings = load_settings(
        url="https://arg.example",
        api_key="from-arg",
        config_path=tmp_path / "missing.toml",
    )
    check_eq(settings.url, "https://arg.example")
    check_eq(settings.api_key, "from-arg")


def test_default_config_path_is_in_home() -> None:
    check(default_config_path() == Path.home() / ".mwdb.toml")
