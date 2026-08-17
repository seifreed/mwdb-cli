"""Live tests for metadata namespaces (tags, comments, attributes, shares,
relations, karton, quick queries, search, count).

Mutations either target the user's own data (quick queries) or are rejected
by the server (403 missing capability / 404 missing object).
"""

from __future__ import annotations

import pytest

from mwdb_cli import AsyncMwdbClient
from mwdb_cli.exceptions import ForbiddenError, NotFoundError

from .checks import check, check_eq
from .conftest import LIVE_URL
from .constants import MISSING_ANALYSIS, MISSING_SHA256


async def test_tag_and_metadata_reads(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        first = (await client.files.list(count=1))[0]
        tags = await client.tags.get(first.id)
        comments = await client.comments.list(first.id)
        legacy = await client.attributes.legacy_get(first.id)
        shares = await client.shares.get(first.id)
        relations = await client.relations.get(first.id)
        tag_names = await client.tags.list(query="emotet", count=5)
    check(isinstance(tags, list))
    check(isinstance(comments, list))
    check(isinstance(legacy, dict))
    check("shares" in shares)
    check("parents" in relations)
    check(isinstance(tag_names, list))


async def test_search_and_count(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        first = (await client.files.list(count=1))[0]
        results = await client.search_api.search(f"file.sha256:{first.sha256}")
        matched = await client.files.count(query=f"file.sha256:{first.sha256}")
        unmatched = await client.files.count(query=f"file.sha256:{MISSING_SHA256}")
    check_eq(len(results), 1)
    check_eq(matched, 1)
    check_eq(unmatched, 0)


async def test_quick_query_lifecycle(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        created = await client.quick_queries.create(
            "mwdb-cli-test", "tag:mwdb-cli-nonexistent", object_type="file"
        )
        listed = await client.quick_queries.list(object_type="file")
        await client.quick_queries.remove(created["id"])
        remaining = await client.quick_queries.list(object_type="file")
    check(any(entry["id"] == created["id"] for entry in listed))
    check(all(entry["id"] != created["id"] for entry in remaining))


async def test_tag_mutations_rejected(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        with pytest.raises(NotFoundError):
            await client.tags.add(MISSING_SHA256, "mwdb-cli-test")
        with pytest.raises(ForbiddenError):
            await client.tags.remove(MISSING_SHA256, "mwdb-cli-test")


async def test_comment_mutations_rejected(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        with pytest.raises(NotFoundError):
            await client.comments.add(MISSING_SHA256, "mwdb-cli-test")
        with pytest.raises(ForbiddenError):
            await client.comments.remove(MISSING_SHA256, 1)


async def test_attribute_mutations_rejected(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        with pytest.raises(NotFoundError):
            await client.attributes.add(MISSING_SHA256, "key", "value")
        with pytest.raises(ForbiddenError):
            await client.attributes.remove(MISSING_SHA256, 1)
        with pytest.raises(ForbiddenError):
            await client.attributes.list(MISSING_SHA256, hidden=True)
        with pytest.raises(NotFoundError):
            await client.attributes.legacy_add(MISSING_SHA256, "key", "value")
        with pytest.raises(ForbiddenError):
            await client.attributes.legacy_remove(MISSING_SHA256, "key", value="v")


async def test_share_mutations_rejected(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        groups = await client.shares.groups()
        with pytest.raises(NotFoundError):
            await client.shares.share(MISSING_SHA256, "public")
    check("groups" in groups)


async def test_relation_mutations_rejected(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        with pytest.raises(NotFoundError):
            await client.relations.link(MISSING_SHA256, MISSING_SHA256)
        with pytest.raises(ForbiddenError):
            await client.relations.unlink(MISSING_SHA256, MISSING_SHA256)


async def test_karton_operations_rejected(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        with pytest.raises(ForbiddenError):
            await client.karton.resubmit(MISSING_SHA256)
        with pytest.raises(NotFoundError):
            await client.karton.get(MISSING_SHA256, MISSING_ANALYSIS)
        with pytest.raises(ForbiddenError):
            await client.karton.assign(MISSING_SHA256, MISSING_ANALYSIS)
        with pytest.raises(ForbiddenError):
            await client.karton.remove(MISSING_SHA256, MISSING_ANALYSIS)
