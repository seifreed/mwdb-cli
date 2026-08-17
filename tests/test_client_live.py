"""Live tests for core object namespaces against mwdb.cert.pl.

Mutating operations are exercised only through requests the server rejects
(403 for missing capabilities, 404 for nonexistent identifiers), so the
production service is never modified.
"""

from __future__ import annotations

import pytest

from mwdb_cli import AsyncMwdbClient
from mwdb_cli.exceptions import ForbiddenError, NotFoundError

from .checks import check, check_eq
from .conftest import LIVE_URL
from .constants import MISSING_SHA256


async def test_files_list(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        items = await client.files.list(count=3)
    check_eq(len(items), 3)
    for item in items:
        check_eq(item.type, "file")
        check(item.sha256 is not None)


async def test_files_get(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        items = await client.files.list(count=1)
        detail = await client.files.get(items[0].id)
    check_eq(detail.id, items[0].id)
    check(detail.file_size is not None)


async def test_files_iterate_across_pages(api_key: str) -> None:
    collected = []
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        async for item in client.files.iterate(chunk_size=2):
            collected.append(item)
            if len(collected) == 3:
                break
    check_eq(len(collected), 3)
    check_eq(len({item.id for item in collected}), 3)


async def test_files_iterate_stops_on_short_chunk(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        items = await client.files.list(count=1)
        query = f"file.sha256:{items[0].sha256}"
        matched = [item async for item in client.files.iterate(query=query)]
    check_eq(len(matched), 1)
    check_eq(matched[0].id, items[0].id)


async def test_objects_list_and_get(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        items = await client.objects.list(count=2)
        detail = await client.objects.get(items[0].id)
    check_eq(len(items), 2)
    check_eq(detail.id, items[0].id)


async def test_configs_and_blobs_list(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        configs = await client.configs.list(count=1)
        blobs = await client.blobs.list(count=1)
    check(isinstance(configs, list))
    check(isinstance(blobs, list))


async def test_config_stats(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        stats = await client.configs.stats()
    check(isinstance(stats, dict))


async def test_file_delete_requires_capability(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        with pytest.raises(ForbiddenError):
            await client.files.delete(MISSING_SHA256)


async def test_favorite_missing_object(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        with pytest.raises(NotFoundError):
            await client.objects.favorite(MISSING_SHA256)


async def test_unfavorite_missing_object(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        with pytest.raises(NotFoundError):
            await client.objects.unfavorite(MISSING_SHA256)


async def test_share_3rd_party_requires_capability(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        with pytest.raises(ForbiddenError):
            await client.objects.share_3rd_party(MISSING_SHA256)


async def test_request_sample_missing_object(api_key: str) -> None:
    async with AsyncMwdbClient(LIVE_URL, api_key) as client:
        with pytest.raises(NotFoundError):
            await client.files.request_sample(MISSING_SHA256)
