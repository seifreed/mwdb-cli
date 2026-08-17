"""Success paths for metadata mutations, served by a real local HTTP server."""

from __future__ import annotations

from mwdb_cli import AsyncMwdbClient

from .checks import check, check_eq
from .localserver import scripted_server
from .test_client_local import json_response


async def test_attribute_success_paths() -> None:
    attribute = {"id": 1, "key": "source", "value": "unit"}
    responses = [
        json_response({"attributes": [attribute]}),
        json_response({"attributes": [attribute]}),
    ]
    with scripted_server(responses) as url:
        async with AsyncMwdbClient(url, "key") as client:
            listed = await client.attributes.list("a" * 64, object_type="file")
            added = await client.attributes.add("a" * 64, "source", "unit")
    check_eq(listed, [attribute])
    check_eq(added, [attribute])


async def test_comment_and_share_success_paths() -> None:
    responses = [
        json_response({"id": 5, "comment": "note"}),
        json_response({"shares": []}),
    ]
    with scripted_server(responses) as url:
        async with AsyncMwdbClient(url, "key") as client:
            comment = await client.comments.add("a" * 64, "note")
            shared = await client.shares.share("a" * 64, "public")
    check_eq(comment["id"], 5)
    check("shares" in shared)


async def test_karton_success_paths() -> None:
    analysis = {"id": "abc", "status": "running"}
    responses = [
        json_response({"analyses": [analysis]}),
        json_response(analysis),
        json_response(analysis),
        json_response(analysis),
    ]
    with scripted_server(responses) as url:
        async with AsyncMwdbClient(url, "key") as client:
            listed = await client.karton.list("a" * 64, older_than="abc")
            resubmitted = await client.karton.resubmit(
                "a" * 64, arguments={"priority": "high"}
            )
            fetched = await client.karton.get("a" * 64, "abc")
            assigned = await client.karton.assign("a" * 64, "abc")
    check_eq(listed["analyses"], [analysis])
    check_eq(resubmitted["id"], "abc")
    check_eq(fetched["id"], "abc")
    check_eq(assigned["id"], "abc")
