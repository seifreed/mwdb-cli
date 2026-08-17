"""Settings resolution: explicit arguments, environment, config file, defaults."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .exceptions import ValidationError

DEFAULT_URL = "https://mwdb.cert.pl"
ENV_URL = "MWDB_URL"
ENV_API_KEY = "MWDB_API_KEY"


@dataclass(frozen=True)
class Settings:
    """Resolved connection settings for an MWDB instance."""

    url: str
    api_key: str | None


def default_config_path() -> Path:
    return Path.home() / ".mwdb.toml"


def _read_config_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    try:
        with path.open("rb") as handle:
            document = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ValidationError(f"invalid config file {path}: {exc}") from exc
    section = document.get("mwdb", {})
    if not isinstance(section, dict):
        raise ValidationError(f"invalid config file {path}: [mwdb] must be a table")
    return {key: str(value) for key, value in section.items()}


def load_settings(
    url: str | None = None,
    api_key: str | None = None,
    config_path: Path | None = None,
) -> Settings:
    """Resolve settings with precedence: arguments > environment > file > default."""
    file_values = _read_config_file(config_path or default_config_path())
    resolved_url = (
        url or os.environ.get(ENV_URL) or file_values.get("url") or DEFAULT_URL
    )
    resolved_key = api_key or os.environ.get(ENV_API_KEY) or file_values.get("api_key")
    return Settings(url=resolved_url, api_key=resolved_key)
