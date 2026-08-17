"""Lightweight typed views over MWDB API payloads.

Each model keeps the full payload in ``raw`` so no API field is ever lost.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Self


def tag_names(payload: dict[str, Any]) -> list[str]:
    return [entry["tag"] for entry in payload.get("tags", [])]


@dataclass(frozen=True)
class ObjectItem:
    """Common view of any MWDB object."""

    id: str
    type: str
    upload_time: str | None
    tags: list[str]
    raw: dict[str, Any]

    _extra_fields: ClassVar[tuple[str, ...]] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Self:
        extras = {name: payload.get(name) for name in cls._extra_fields}
        return cls(
            id=payload["id"],
            type=payload["type"],
            upload_time=payload.get("upload_time"),
            tags=tag_names(payload),
            raw=payload,
            **extras,
        )


@dataclass(frozen=True)
class FileItem(ObjectItem):
    file_name: str | None = None
    file_size: int | None = None
    file_type: str | None = None
    md5: str | None = None
    sha1: str | None = None
    sha256: str | None = None

    _extra_fields = ("file_name", "file_size", "file_type", "md5", "sha1", "sha256")


@dataclass(frozen=True)
class ConfigItem(ObjectItem):
    family: str | None = None
    config_type: str | None = None

    _extra_fields = ("family", "config_type")


@dataclass(frozen=True)
class BlobItem(ObjectItem):
    blob_name: str | None = None
    blob_size: int | None = None
    blob_type: str | None = None
    last_seen: str | None = None

    _extra_fields = ("blob_name", "blob_size", "blob_type", "last_seen")
