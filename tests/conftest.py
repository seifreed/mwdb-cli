"""Shared fixtures. Live tests require MWDB_API_KEY in the environment."""

from __future__ import annotations

import os

import pytest

from mwdb_cli.config import DEFAULT_URL, ENV_API_KEY

LIVE_URL = os.environ.get("MWDB_URL", DEFAULT_URL)


@pytest.fixture(scope="session")
def api_key() -> str:
    value = os.environ.get(ENV_API_KEY)
    if not value:
        raise RuntimeError(
            "MWDB_API_KEY must be set: the test suite runs against a live"
            " MWDB instance (no mocks)."
        )
    return value
