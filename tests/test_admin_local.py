"""Success paths for every admin namespace method, via a real local server."""

from __future__ import annotations

from typing import Any

from mwdb_cli import AsyncMwdbClient

from .checks import check, check_eq
from .localserver import ScriptedResponse, scripted_server
from .test_client_local import json_response


def with_token(payload: dict[str, Any], value: str) -> dict[str, Any]:
    enriched = dict(payload)
    enriched["token"] = value
    return enriched


async def test_auth_success_paths() -> None:
    responses = [
        json_response(with_token({"login": "someone"}, "session-jwt")),
        json_response({"login": "someone"}),
        json_response({"login": "someone"}),
        json_response({"login": "someone"}),
        json_response(with_token({"login": "someone"}, "change-jwt")),
    ]
    with scripted_server(responses) as url:
        async with AsyncMwdbClient(url, "key") as client:
            logged_in = await client.auth.login("someone", "secret-pass")
            registered = await client.auth.register(
                "someone", "someone@example.org", "info", recaptcha="captcha"
            )
            changed = await client.auth.change_password("new-pass", "reset-jwt")
            recovered = await client.auth.recover_password(
                "someone", "someone@example.org"
            )
            requested = await client.auth.request_password_change()
    check("token" in logged_in)
    check_eq(registered["login"], "someone")
    check_eq(changed["login"], "someone")
    check_eq(recovered["login"], "someone")
    check("token" in requested)


async def test_users_success_paths() -> None:
    user = {"login": "someone", "email": "someone@example.org"}
    responses = [
        json_response({"users": [user]}),
        json_response(user),
        json_response(user),
        json_response(user),
        json_response(user),
        json_response(with_token({"login": "someone"}, "change-jwt")),
        json_response(with_token({"login": "someone"}, "change-jwt")),
    ]
    with scripted_server(responses) as url:
        async with AsyncMwdbClient(url, "key") as client:
            listed = await client.users.list(pending=True)
            created = await client.users.create(
                "someone", "someone@example.org", "info", feed_quality="high"
            )
            updated = await client.users.update("someone", disabled=False)
            fetched = await client.users.get("someone")
            accepted = await client.users.pending_accept("someone")
            change_link = await client.users.change_password_token("someone")
            requested = await client.users.request_password_change("someone")
    check_eq(listed, [user])
    check_eq(created["login"], "someone")
    check_eq(updated["login"], "someone")
    check_eq(fetched["login"], "someone")
    check_eq(accepted["login"], "someone")
    check("token" in change_link)
    check("token" in requested)


async def test_users_void_paths() -> None:
    responses = [ScriptedResponse(200), ScriptedResponse(200)]
    with scripted_server(responses) as url:
        async with AsyncMwdbClient(url, "key") as client:
            await client.users.delete("someone")
            await client.users.pending_reject("someone")


async def test_groups_success_paths() -> None:
    group = {"name": "analysts", "capabilities": []}
    responses = [
        json_response({"groups": [group]}),
        json_response(group),
        json_response(group),
        json_response(group),
        json_response(group),
        json_response(group),
        ScriptedResponse(200),
        ScriptedResponse(200),
    ]
    with scripted_server(responses) as url:
        async with AsyncMwdbClient(url, "key") as client:
            listed = await client.groups.list()
            fetched = await client.groups.get("analysts")
            created = await client.groups.create(
                "analysts", capabilities=["adding_tags"]
            )
            updated = await client.groups.update("analysts", new_name="analysts2")
            member_added = await client.groups.member_add("analysts", "someone")
            member_updated = await client.groups.member_update(
                "analysts", "someone", group_admin=True
            )
            await client.groups.member_delete("analysts", "someone")
            await client.groups.delete("analysts")
    check_eq(listed, [group])
    check_eq(fetched["name"], "analysts")
    check_eq(created["name"], "analysts")
    check_eq(updated["name"], "analysts")
    check_eq(member_added["name"], "analysts")
    check_eq(member_updated["name"], "analysts")


async def test_attribute_definitions_success_paths() -> None:
    definition = {"key": "source", "label": "Source", "description": "d"}
    permission = {"group_name": "analysts", "can_read": True, "can_set": False}
    responses = [
        json_response(definition),
        json_response(definition),
        json_response(definition),
        json_response({"attribute_permissions": [permission]}),
        json_response(permission),
        ScriptedResponse(200),
        ScriptedResponse(200),
    ]
    with scripted_server(responses) as url:
        async with AsyncMwdbClient(url, "key") as client:
            fetched = await client.attribute_defs.get("source")
            created = await client.attribute_defs.create(
                "source", "Source", "desc", url_template="https://x/$value"
            )
            updated = await client.attribute_defs.update("source", label="Source2")
            permissions = await client.attribute_defs.permissions("source")
            permission_set = await client.attribute_defs.permission_set(
                "source", "analysts", can_read=True, can_set=False
            )
            await client.attribute_defs.permission_delete("source", "analysts")
            await client.attribute_defs.delete("source")
    check_eq(fetched["key"], "source")
    check_eq(created["key"], "source")
    check_eq(updated["key"], "source")
    check_eq(permissions, [permission])
    check_eq(permission_set["group_name"], "analysts")


async def test_metakeys_success_paths() -> None:
    definition = {"key": "source", "label": "Source", "template": "t"}
    responses = [
        json_response({"metakeys": [definition]}),
        json_response(definition),
        json_response(definition),
        json_response(definition),
        json_response({"can_read": True, "can_set": True}),
        ScriptedResponse(200),
        ScriptedResponse(200),
    ]
    with scripted_server(responses) as url:
        async with AsyncMwdbClient(url, "key") as client:
            definitions = await client.metakeys.definitions()
            fetched = await client.metakeys.get("source")
            created = await client.metakeys.create("source", "Source", "desc", "t")
            updated = await client.metakeys.update("source", hidden=True)
            permission_set = await client.metakeys.permission_set(
                "source", "analysts", can_read=True, can_set=True
            )
            await client.metakeys.permission_delete("source", "analysts")
            await client.metakeys.delete("source")
    check_eq(definitions, [definition])
    check_eq(fetched["key"], "source")
    check_eq(created["key"], "source")
    check_eq(updated["key"], "source")
    check(permission_set["can_read"])


async def test_oauth_success_paths() -> None:
    provider = {"name": "corp-sso", "client_id": "cid"}
    responses = [
        json_response(provider),
        json_response(provider),
        json_response(provider),
        json_response(with_token({"login": "someone"}, "oidc-jwt")),
        json_response({"login": "someone"}),
        json_response({"url": "https://sso/logout"}),
        ScriptedResponse(200),
    ]
    with scripted_server(responses) as url:
        async with AsyncMwdbClient(url, "key") as client:
            registered = await client.oauth.register_provider(provider)
            fetched = await client.oauth.get("corp-sso")
            updated = await client.oauth.update("corp-sso", provider)
            authenticated = await client.oauth.authenticate(
                "corp-sso", {"code": "c", "state": "s", "nonce": "n"}
            )
            bound = await client.oauth.bind_account("corp-sso", "c", "n", "s")
            logout = await client.oauth.logout("corp-sso")
            await client.oauth.delete("corp-sso")
    check_eq(registered["name"], "corp-sso")
    check_eq(fetched["name"], "corp-sso")
    check_eq(updated["name"], "corp-sso")
    check("token" in authenticated)
    check_eq(bound["login"], "someone")
    check("url" in logout)
