"""Account, user, group, attribute-definition, metakey and OAuth namespaces."""

from __future__ import annotations

from typing import Any

from .base import APIBase, JsonList, StrList, build_params


class AuthAPI(APIBase):
    async def login(self, login: str, password: str) -> dict[str, Any]:
        return await self._call_dict(
            "auth_login", json={"login": login, "password": password}
        )

    async def refresh(self) -> dict[str, Any]:
        return await self._call_dict("auth_refresh")

    async def validate(self) -> dict[str, Any]:
        return await self._call_dict("auth_validate")

    async def groups(self) -> JsonList:
        return await self._call_list("auth_groups", key="groups")

    async def register(
        self,
        login: str,
        email: str,
        additional_info: str,
        *,
        recaptcha: str | None = None,
    ) -> dict[str, Any]:
        body = build_params(
            login=login,
            email=email,
            additional_info=additional_info,
            recaptcha=recaptcha,
        )
        return await self._call_dict("auth_register", json=body)

    async def change_password(self, password: str, token: str) -> dict[str, Any]:
        return await self._call_dict(
            "auth_change_password", json={"password": password, "token": token}
        )

    async def recover_password(
        self, login: str, email: str, *, recaptcha: str | None = None
    ) -> dict[str, Any]:
        body = build_params(login=login, email=email, recaptcha=recaptcha)
        return await self._call_dict("auth_recover_password", json=body)

    async def request_password_change(self) -> dict[str, Any]:
        return await self._call_dict("auth_request_password_change")


class UsersAPI(APIBase):
    async def list(self, *, pending: bool | None = None) -> JsonList:
        return await self._call_list(
            "user_list",
            params=build_params(pending=1 if pending else None),
            key="users",
        )

    async def get(self, login: str) -> dict[str, Any]:
        return await self._call_dict("user_get", {"login": login})

    async def create(
        self,
        login: str,
        email: str,
        additional_info: str,
        *,
        feed_quality: str | None = None,
        send_email: bool | None = None,
    ) -> dict[str, Any]:
        body = build_params(
            email=email,
            additional_info=additional_info,
            feed_quality=feed_quality,
            send_email=send_email,
        )
        return await self._call_dict("user_create", {"login": login}, json=body)

    async def update(
        self,
        login: str,
        *,
        email: str | None = None,
        additional_info: str | None = None,
        feed_quality: str | None = None,
        disabled: bool | None = None,
        send_email: bool | None = None,
    ) -> dict[str, Any]:
        body = build_params(
            email=email,
            additional_info=additional_info,
            feed_quality=feed_quality,
            disabled=disabled,
            send_email=send_email,
        )
        return await self._call_dict("user_update", {"login": login}, json=body)

    async def delete(self, login: str) -> None:
        await self._call("user_delete", {"login": login})

    async def pending_accept(self, login: str) -> dict[str, Any]:
        return await self._call_dict("user_pending_accept", {"login": login})

    async def pending_reject(self, login: str) -> None:
        await self._call("user_pending_reject", {"login": login})

    async def change_password_token(self, login: str) -> dict[str, Any]:
        return await self._call_dict("user_change_password_token", {"login": login})

    async def request_password_change(self, login: str) -> dict[str, Any]:
        return await self._call_dict("user_request_password_change", {"login": login})

    async def profile(self, login: str) -> dict[str, Any]:
        return await self._call_dict("profile_get", {"login": login})


class ApiKeysAPI(APIBase):
    async def create(self, login: str, name: str) -> dict[str, Any]:
        return await self._call_dict(
            "user_api_key_create", {"login": login}, json={"name": name}
        )

    async def delete(self, api_key_id: str) -> None:
        await self._call("api_key_delete", {"api_key_id": api_key_id})


class GroupsAPI(APIBase):
    async def list(self) -> JsonList:
        return await self._call_list("group_list", key="groups")

    async def get(self, name: str) -> dict[str, Any]:
        return await self._call_dict("group_get", {"name": name})

    async def create(
        self, name: str, *, capabilities: StrList | None = None
    ) -> dict[str, Any]:
        return await self._call_dict(
            "group_create",
            {"name": name},
            json=build_params(capabilities=capabilities),
        )

    async def update(
        self,
        name: str,
        *,
        new_name: str | None = None,
        capabilities: StrList | None = None,
        default: bool | None = None,
        provider: str | None = None,
        workspace: bool | None = None,
    ) -> dict[str, Any]:
        body = build_params(
            name=new_name,
            capabilities=capabilities,
            default=default,
            provider=provider,
            workspace=workspace,
        )
        return await self._call_dict("group_update", {"name": name}, json=body)

    async def delete(self, name: str) -> None:
        await self._call("group_delete", {"name": name})

    async def member_add(self, name: str, login: str) -> dict[str, Any]:
        return await self._call_dict("group_member_add", {"name": name, "login": login})

    async def member_update(
        self, name: str, login: str, *, group_admin: bool
    ) -> dict[str, Any]:
        return await self._call_dict(
            "group_member_update",
            {"name": name, "login": login},
            json={"group_admin": group_admin},
        )

    async def member_delete(self, name: str, login: str) -> None:
        await self._call("group_member_delete", {"name": name, "login": login})


class AttributeDefinitionsAPI(APIBase):
    async def list(self, *, access: str | None = None) -> JsonList:
        return await self._call_list(
            "attribute_key_list",
            params=build_params(access=access),
            key="attribute_definitions",
        )

    async def get(self, key: str) -> dict[str, Any]:
        return await self._call_dict("attribute_key_get", {"key": key})

    async def create(
        self,
        key: str,
        label: str,
        description: str,
        *,
        hidden: bool = False,
        url_template: str | None = None,
        rich_template: str | None = None,
        example_value: str | None = None,
    ) -> dict[str, Any]:
        body = build_params(
            key=key,
            label=label,
            description=description,
            hidden=hidden,
            url_template=url_template,
            rich_template=rich_template,
            example_value=example_value,
        )
        return await self._call_dict("attribute_key_create", json=body)

    async def update(
        self,
        key: str,
        *,
        label: str | None = None,
        description: str | None = None,
        hidden: bool | None = None,
        url_template: str | None = None,
        rich_template: str | None = None,
        example_value: str | None = None,
    ) -> dict[str, Any]:
        body = build_params(
            label=label,
            description=description,
            hidden=hidden,
            url_template=url_template,
            rich_template=rich_template,
            example_value=example_value,
        )
        return await self._call_dict("attribute_key_update", {"key": key}, json=body)

    async def delete(self, key: str) -> None:
        await self._call("attribute_key_delete", {"key": key})

    async def permissions(self, key: str) -> JsonList:
        return await self._call_list(
            "attribute_key_permissions", {"key": key}, key="attribute_permissions"
        )

    async def permission_set(
        self, key: str, group_name: str, *, can_read: bool, can_set: bool
    ) -> dict[str, Any]:
        return await self._call_dict(
            "attribute_key_permission_set",
            {"key": key},
            json={"group_name": group_name, "can_read": can_read, "can_set": can_set},
        )

    async def permission_delete(self, key: str, group_name: str) -> None:
        await self._call(
            "attribute_key_permission_delete",
            {"key": key},
            params={"group_name": group_name},
        )


class MetakeysAPI(APIBase):
    async def list_keys(self, access: str) -> JsonList:
        return await self._call_list(
            "meta_key_list", {"access": access}, key="metakeys"
        )

    async def definitions(self) -> JsonList:
        return await self._call_list("metakey_definitions", key="metakeys")

    async def get(self, key: str) -> dict[str, Any]:
        return await self._call_dict("metakey_get", {"key": key})

    async def create(
        self,
        key: str,
        label: str,
        description: str,
        template: str,
        *,
        hidden: bool = False,
    ) -> dict[str, Any]:
        body = {
            "label": label,
            "description": description,
            "template": template,
            "hidden": hidden,
        }
        return await self._call_dict("metakey_create", {"key": key}, json=body)

    async def update(
        self,
        key: str,
        *,
        label: str | None = None,
        description: str | None = None,
        template: str | None = None,
        hidden: bool | None = None,
    ) -> dict[str, Any]:
        body = build_params(
            label=label, description=description, template=template, hidden=hidden
        )
        return await self._call_dict("metakey_update", {"key": key}, json=body)

    async def delete(self, key: str) -> None:
        await self._call("metakey_delete", {"key": key})

    async def permission_set(
        self, key: str, group_name: str, *, can_read: bool, can_set: bool
    ) -> dict[str, Any]:
        return await self._call_dict(
            "metakey_permission_set",
            {"key": key, "group_name": group_name},
            json={"can_read": can_read, "can_set": can_set},
        )

    async def permission_delete(self, key: str, group_name: str) -> None:
        await self._call(
            "metakey_permission_delete", {"key": key, "group_name": group_name}
        )


class OAuthAPI(APIBase):
    async def providers(self) -> list[str]:
        return await self._call_str_list("oauth_provider_list", key="providers")

    async def identities(self) -> list[str]:
        return await self._call_str_list("oauth_identities", key="providers")

    async def register_provider(self, config: dict[str, Any]) -> dict[str, Any]:
        return await self._call_dict("oauth_provider_create", json=config)

    async def get(self, provider_name: str) -> dict[str, Any]:
        return await self._call_dict(
            "oauth_provider_get", {"provider_name": provider_name}
        )

    async def update(
        self, provider_name: str, config: dict[str, Any]
    ) -> dict[str, Any]:
        return await self._call_dict(
            "oauth_provider_update", {"provider_name": provider_name}, json=config
        )

    async def delete(self, provider_name: str) -> None:
        await self._call("oauth_provider_delete", {"provider_name": provider_name})

    async def authenticate(
        self, provider_name: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return await self._call_dict(
            "oauth_authenticate", {"provider_name": provider_name}, json=payload
        )

    async def bind_account(
        self, provider_name: str, code: str, nonce: str, state: str
    ) -> dict[str, Any]:
        return await self._call_dict(
            "oauth_bind_account",
            {"provider_name": provider_name},
            json={"code": code, "nonce": nonce, "state": state},
        )

    async def logout(self, provider_name: str) -> dict[str, Any]:
        return await self._call_dict("oauth_logout", {"provider_name": provider_name})
