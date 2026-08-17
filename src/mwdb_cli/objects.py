"""Typed object namespaces: files, configs, blobs and generic objects."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any, ClassVar

from .base import APIBase, build_params, file_payload
from .models import BlobItem, ConfigItem, FileItem, ObjectItem


class _TypedObjectsAPI[ItemT: ObjectItem](APIBase):
    """Shared list/iterate/get/delete behavior for the four object kinds."""

    _list_operation: ClassVar[str]
    _get_operation: ClassVar[str]
    _delete_operation: ClassVar[str]
    _list_key: ClassVar[str]
    _type_name: ClassVar[str]
    _item_factory: Callable[[dict[str, Any]], ItemT]

    async def list(
        self,
        *,
        query: str | None = None,
        older_than: str | None = None,
        count: int | None = None,
    ) -> list[ItemT]:
        payload = await self._call(
            self._list_operation,
            params=build_params(query=query, older_than=older_than, count=count),
        )
        return [self._item_factory(entry) for entry in payload[self._list_key]]

    async def iterate(
        self, *, query: str | None = None, chunk_size: int = 100
    ) -> AsyncIterator[ItemT]:
        older_than: str | None = None
        while True:
            chunk = await self.list(
                query=query, older_than=older_than, count=chunk_size
            )
            for item in chunk:
                yield item
            if len(chunk) < chunk_size:
                return
            older_than = chunk[-1].id

    async def get(self, identifier: str) -> ItemT:
        payload = await self._call(self._get_operation, {"identifier": identifier})
        return self._item_factory(payload)

    async def delete(self, identifier: str) -> None:
        await self._call(self._delete_operation, {"identifier": identifier})

    async def count(self, *, query: str | None = None) -> int:
        payload = await self._call(
            "object_count",
            {"type": self._type_name},
            params=build_params(query=query),
        )
        return int(payload["count"])


class FilesAPI(_TypedObjectsAPI[FileItem]):
    _item_factory = staticmethod(FileItem.from_dict)
    _list_operation = "file_list"
    _get_operation = "file_get"
    _delete_operation = "file_delete"
    _list_key = "files"
    _type_name = "file"

    async def upload(
        self,
        source: Path | bytes,
        *,
        file_name: str | None = None,
        parent: str | None = None,
        upload_as: str | None = None,
        attributes: list[dict[str, Any]] | None = None,
        tags: list[str] | None = None,
        karton_id: str | None = None,
        karton_arguments: dict[str, Any] | None = None,
        share_3rd_party: bool | None = None,
    ) -> FileItem:
        name, content = await file_payload(source, file_name)
        options = build_params(
            parent=parent,
            upload_as=upload_as,
            attributes=attributes,
            tags=tags,
            karton_id=karton_id,
            karton_arguments=karton_arguments,
            share_3rd_party=share_3rd_party,
        )
        payload = await self._call(
            "file_upload",
            files={"file": (name, content)},
            data={"options": json.dumps(options)},
        )
        return FileItem.from_dict(payload)

    async def reupload(
        self,
        identifier: str,
        source: Path | bytes,
        *,
        file_name: str | None = None,
        metakeys: list[dict[str, Any]] | None = None,
        upload_as: str | None = None,
    ) -> FileItem:
        name, content = await file_payload(source, file_name)
        data: dict[str, Any] = {}
        if metakeys is not None:
            data["metakeys"] = json.dumps({"metakeys": metakeys})
        if upload_as is not None:
            data["upload_as"] = upload_as
        payload = await self._call(
            "file_reupload",
            {"identifier": identifier},
            files={"file": (name, content)},
            data=data,
        )
        return FileItem.from_dict(payload)

    async def download(
        self, identifier: str, destination: Path, *, obfuscate: bool = False
    ) -> Path:
        params = build_params(obfuscate=1 if obfuscate else None)
        return await self._download(
            "file_download", {"identifier": identifier}, destination, params=params
        )

    async def download_token(self, identifier: str) -> str:
        payload = await self._call("file_download_token", {"identifier": identifier})
        return str(payload["token"])

    async def download_zip(self, identifier: str, destination: Path) -> Path:
        return await self._download(
            "file_download_zip", {"identifier": identifier}, destination
        )

    async def download_zip_token(self, identifier: str) -> str:
        payload = await self._call(
            "file_download_zip_token", {"identifier": identifier}
        )
        return str(payload["token"])

    async def download_by_token(self, access_token: str, destination: Path) -> Path:
        return await self._download(
            "download", {"access_token": access_token}, destination
        )

    async def request_sample(self, identifier: str) -> dict[str, Any]:
        return await self._call_dict("request_sample", {"identifier": identifier})


class ConfigsAPI(_TypedObjectsAPI[ConfigItem]):
    _item_factory = staticmethod(ConfigItem.from_dict)
    _list_operation = "config_list"
    _get_operation = "config_get"
    _delete_operation = "config_delete"
    _list_key = "configs"
    _type_name = "config"

    async def create(
        self,
        family: str,
        cfg: dict[str, Any],
        *,
        config_type: str | None = None,
        parent: str | None = None,
        upload_as: str | None = None,
        attributes: list[dict[str, Any]] | None = None,
        metakeys: list[dict[str, Any]] | None = None,
        tags: list[str] | None = None,
        karton_id: str | None = None,
        karton_arguments: dict[str, Any] | None = None,
        share_3rd_party: bool | None = None,
    ) -> ConfigItem:
        body = build_params(
            family=family,
            cfg=cfg,
            config_type=config_type,
            parent=parent,
            upload_as=upload_as,
            attributes=attributes,
            metakeys=metakeys,
            tags=tags,
            karton_id=karton_id,
            karton_arguments=karton_arguments,
            share_3rd_party=share_3rd_party,
        )
        payload = await self._call("config_create", json=body)
        return ConfigItem.from_dict(payload)

    async def put(self, identifier: str, body: dict[str, Any]) -> ConfigItem:
        payload = await self._call("config_put", {"identifier": identifier}, json=body)
        return ConfigItem.from_dict(payload)

    async def stats(self, *, time_range: str | None = None) -> dict[str, Any]:
        return await self._call_dict(
            "config_stats", params=build_params(range=time_range)
        )


class BlobsAPI(_TypedObjectsAPI[BlobItem]):
    _item_factory = staticmethod(BlobItem.from_dict)
    _list_operation = "blob_list"
    _get_operation = "blob_get"
    _delete_operation = "blob_delete"
    _list_key = "blobs"
    _type_name = "blob"

    async def create(
        self,
        blob_name: str,
        blob_type: str,
        content: str,
        *,
        parent: str | None = None,
        upload_as: str | None = None,
        attributes: list[dict[str, Any]] | None = None,
        metakeys: list[dict[str, Any]] | None = None,
        tags: list[str] | None = None,
        karton_id: str | None = None,
        karton_arguments: dict[str, Any] | None = None,
        share_3rd_party: bool | None = None,
    ) -> BlobItem:
        body = build_params(
            blob_name=blob_name,
            blob_type=blob_type,
            content=content,
            parent=parent,
            upload_as=upload_as,
            attributes=attributes,
            metakeys=metakeys,
            tags=tags,
            karton_id=karton_id,
            karton_arguments=karton_arguments,
            share_3rd_party=share_3rd_party,
        )
        payload = await self._call("blob_create", json=body)
        return BlobItem.from_dict(payload)

    async def put(self, identifier: str, body: dict[str, Any]) -> BlobItem:
        payload = await self._call("blob_put", {"identifier": identifier}, json=body)
        return BlobItem.from_dict(payload)


class ObjectsAPI(_TypedObjectsAPI[ObjectItem]):
    _item_factory = staticmethod(ObjectItem.from_dict)
    _list_operation = "object_list"
    _get_operation = "object_get"
    _delete_operation = "object_delete"
    _list_key = "objects"
    _type_name = "object"

    async def favorite(self, identifier: str) -> None:
        await self._call("object_favorite", {"identifier": identifier})

    async def unfavorite(self, identifier: str) -> None:
        await self._call("object_unfavorite", {"identifier": identifier})

    async def share_3rd_party(self, identifier: str) -> None:
        await self._call("object_share_3rd_party", {"identifier": identifier})
