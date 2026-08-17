"""Object metadata namespaces: search, tags, comments, attributes, shares,
relations, karton analyses and quick queries."""

from __future__ import annotations

from typing import Any

from .base import APIBase, JsonList, build_params


class SearchAPI(APIBase):
    async def search(self, query: str) -> JsonList:
        return await self._call_list("search", json={"query": query})


class TagsAPI(APIBase):
    async def list(
        self, *, query: str | None = None, count: int | None = None
    ) -> JsonList:
        return await self._call_list(
            "tag_list", params=build_params(query=query, count=count)
        )

    async def get(self, identifier: str, *, object_type: str = "object") -> JsonList:
        return await self._call_list(
            "object_tags", {"type": object_type, "identifier": identifier}
        )

    async def add(
        self, identifier: str, tag: str, *, object_type: str = "object"
    ) -> None:
        await self._call(
            "object_tag_add",
            {"type": object_type, "identifier": identifier},
            json={"tag": tag},
        )

    async def remove(
        self, identifier: str, tag: str, *, object_type: str = "object"
    ) -> None:
        await self._call(
            "object_tag_delete",
            {"type": object_type, "identifier": identifier},
            params={"tag": tag},
        )


class CommentsAPI(APIBase):
    async def list(self, identifier: str, *, object_type: str = "object") -> JsonList:
        return await self._call_list(
            "object_comments", {"type": object_type, "identifier": identifier}
        )

    async def add(
        self, identifier: str, comment: str, *, object_type: str = "object"
    ) -> dict[str, Any]:
        return await self._call_dict(
            "object_comment_add",
            {"type": object_type, "identifier": identifier},
            json={"comment": comment},
        )

    async def remove(
        self, identifier: str, comment_id: int, *, object_type: str = "object"
    ) -> None:
        await self._call(
            "object_comment_delete",
            {
                "type": object_type,
                "identifier": identifier,
                "comment_id": str(comment_id),
            },
        )


class AttributesAPI(APIBase):
    async def list(
        self,
        identifier: str,
        *,
        object_type: str = "object",
        hidden: bool = False,
    ) -> JsonList:
        return await self._call_list(
            "object_attributes",
            {"type": object_type, "identifier": identifier},
            params=build_params(hidden=1 if hidden else None),
            key="attributes",
        )

    async def add(
        self,
        identifier: str,
        key: str,
        value: Any,
        *,
        object_type: str = "object",
    ) -> JsonList:
        return await self._call_list(
            "object_attribute_add",
            {"type": object_type, "identifier": identifier},
            json={"key": key, "value": value},
            key="attributes",
        )

    async def remove(
        self, identifier: str, attribute_id: int, *, object_type: str = "object"
    ) -> None:
        await self._call(
            "object_attribute_delete",
            {
                "type": object_type,
                "identifier": identifier,
                "attribute_id": str(attribute_id),
            },
        )

    async def legacy_get(
        self,
        identifier: str,
        *,
        object_type: str = "object",
        hidden: bool = False,
    ) -> dict[str, Any]:
        return await self._call_dict(
            "object_meta_get",
            {"type": object_type, "identifier": identifier},
            params=build_params(hidden=1 if hidden else None),
        )

    async def legacy_add(
        self, identifier: str, key: str, value: str, *, object_type: str = "object"
    ) -> None:
        await self._call(
            "object_meta_add",
            {"type": object_type, "identifier": identifier},
            json={"key": key, "value": value},
        )

    async def legacy_remove(
        self,
        identifier: str,
        key: str,
        *,
        value: str | None = None,
        object_type: str = "object",
    ) -> None:
        await self._call(
            "object_meta_delete",
            {"type": object_type, "identifier": identifier},
            params=build_params(key=key, value=value),
        )


class SharesAPI(APIBase):
    async def groups(self) -> dict[str, Any]:
        return await self._call_dict("share_groups")

    async def get(
        self, identifier: str, *, object_type: str = "object"
    ) -> dict[str, Any]:
        return await self._call_dict(
            "object_shares", {"type": object_type, "identifier": identifier}
        )

    async def share(
        self, identifier: str, group: str, *, object_type: str = "object"
    ) -> dict[str, Any]:
        return await self._call_dict(
            "object_share",
            {"type": object_type, "identifier": identifier},
            json={"group": group},
        )


class RelationsAPI(APIBase):
    async def get(
        self, identifier: str, *, object_type: str = "object"
    ) -> dict[str, Any]:
        return await self._call_dict(
            "object_relations", {"type": object_type, "identifier": identifier}
        )

    async def link(
        self, parent: str, child: str, *, object_type: str = "object"
    ) -> None:
        await self._call(
            "object_child_link",
            {"type": object_type, "parent": parent, "child": child},
        )

    async def unlink(
        self, parent: str, child: str, *, object_type: str = "object"
    ) -> None:
        await self._call(
            "object_child_unlink",
            {"type": object_type, "parent": parent, "child": child},
        )


class KartonAPI(APIBase):
    async def list(
        self,
        identifier: str,
        *,
        object_type: str = "object",
        older_than: str | None = None,
    ) -> dict[str, Any]:
        return await self._call_dict(
            "object_karton_list",
            {"type": object_type, "identifier": identifier},
            params=build_params(older_than=older_than),
        )

    async def resubmit(
        self,
        identifier: str,
        *,
        object_type: str = "object",
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self._call_dict(
            "object_karton_resubmit",
            {"type": object_type, "identifier": identifier},
            json=build_params(arguments=arguments),
        )

    async def get(
        self, identifier: str, analysis_id: str, *, object_type: str = "object"
    ) -> dict[str, Any]:
        return await self._call_dict(
            "object_karton_get",
            {
                "type": object_type,
                "identifier": identifier,
                "analysis_id": analysis_id,
            },
        )

    async def assign(
        self, identifier: str, analysis_id: str, *, object_type: str = "object"
    ) -> dict[str, Any]:
        return await self._call_dict(
            "object_karton_assign",
            {
                "type": object_type,
                "identifier": identifier,
                "analysis_id": analysis_id,
            },
        )

    async def remove(
        self, identifier: str, analysis_id: str, *, object_type: str = "object"
    ) -> None:
        await self._call(
            "object_karton_delete",
            {
                "type": object_type,
                "identifier": identifier,
                "analysis_id": analysis_id,
            },
        )


class QuickQueriesAPI(APIBase):
    async def list(self, *, object_type: str = "object") -> JsonList:
        return await self._call_list("quick_query_list", {"type": object_type})

    async def create(
        self, name: str, query: str, *, object_type: str = "object"
    ) -> dict[str, Any]:
        return await self._call_dict(
            "quick_query_create",
            {"type": object_type},
            json={"name": name, "query": query, "type": object_type},
        )

    async def remove(self, query_id: int) -> None:
        await self._call("quick_query_delete", {"id": str(query_id)})
