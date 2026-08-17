"""Live tests for auth/admin namespaces against mwdb.cert.pl."""

from __future__ import annotations

import pytest

from mwdb_cli import AsyncMwdbClient
from mwdb_cli.exceptions import ForbiddenError, NotFoundError

from .checks import check, check_eq
from .conftest import LIVE_URL


async def test_auth_session_reads(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        session = await client.auth.validate()
        refreshed = await client.auth.refresh()
        groups = await client.auth.groups()
    check_eq(session["login"], "seifreed")
    check_eq(refreshed["login"], "seifreed")
    check(isinstance(groups, list))


async def test_profile_read(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        profile = await client.users.profile("seifreed")
    check_eq(profile["login"], "seifreed")


async def test_attribute_definitions_readable(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        definitions = await client.attribute_defs.list(access="read")
        legacy = await client.metakeys.list_keys("read")
    check(len(definitions) > 0)
    check("key" in definitions[0])
    check(len(legacy) > 0)


async def test_oauth_public_reads(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        providers = await client.oauth.providers()
        identities = await client.oauth.identities()
    check(isinstance(providers, list))
    check(isinstance(identities, list))


async def test_api_key_lifecycle(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        created = await client.api_keys.create("seifreed", "mwdb-cli-test")
        await client.api_keys.delete(created["id"])
    check("id" in created)


async def test_admin_reads_require_capability(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        with pytest.raises(ForbiddenError):
            await client.users.list()
        with pytest.raises(ForbiddenError):
            await client.groups.list()
        with pytest.raises(ForbiddenError):
            await client.users.get("seifreed")


async def test_login_with_wrong_credentials(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        with pytest.raises(ForbiddenError):
            await client.auth.login("mwdb-cli-no-such-user", "wrong-password")


async def test_oauth_unknown_provider(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        with pytest.raises(NotFoundError):
            await client.oauth.authenticate("no-such-provider")
        with pytest.raises(ForbiddenError):
            await client.oauth.get("no-such-provider")
