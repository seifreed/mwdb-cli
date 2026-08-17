"""Composition root: the async client exposing every API namespace."""

from __future__ import annotations

from pathlib import Path
from types import TracebackType

from .admin import (
    ApiKeysAPI,
    AttributeDefinitionsAPI,
    AuthAPI,
    GroupsAPI,
    MetakeysAPI,
    OAuthAPI,
    UsersAPI,
)
from .config import load_settings
from .metadata import (
    AttributesAPI,
    CommentsAPI,
    KartonAPI,
    QuickQueriesAPI,
    RelationsAPI,
    SearchAPI,
    SharesAPI,
    TagsAPI,
)
from .objects import BlobsAPI, ConfigsAPI, FilesAPI, ObjectsAPI
from .server import RemotesAPI, ServerAPI
from .transport import AsyncTransport


class AsyncMwdbClient:
    """Async client for the full MWDB Core API."""

    def __init__(
        self,
        url: str | None = None,
        api_key: str | None = None,
        *,
        config_path: Path | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        backoff: float = 1.0,
    ) -> None:
        settings = load_settings(url, api_key, config_path)
        self.transport = AsyncTransport(
            settings.url,
            settings.api_key,
            timeout=timeout,
            max_retries=max_retries,
            backoff=backoff,
        )
        self.files = FilesAPI(self.transport)
        self.configs = ConfigsAPI(self.transport)
        self.blobs = BlobsAPI(self.transport)
        self.objects = ObjectsAPI(self.transport)
        self.search_api = SearchAPI(self.transport)
        self.tags = TagsAPI(self.transport)
        self.comments = CommentsAPI(self.transport)
        self.attributes = AttributesAPI(self.transport)
        self.shares = SharesAPI(self.transport)
        self.relations = RelationsAPI(self.transport)
        self.karton = KartonAPI(self.transport)
        self.quick_queries = QuickQueriesAPI(self.transport)
        self.auth = AuthAPI(self.transport)
        self.users = UsersAPI(self.transport)
        self.api_keys = ApiKeysAPI(self.transport)
        self.groups = GroupsAPI(self.transport)
        self.attribute_defs = AttributeDefinitionsAPI(self.transport)
        self.metakeys = MetakeysAPI(self.transport)
        self.oauth = OAuthAPI(self.transport)
        self.server = ServerAPI(self.transport)
        self.remotes = RemotesAPI(self.transport)

    async def aclose(self) -> None:
        await self.transport.aclose()

    async def __aenter__(self) -> AsyncMwdbClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()
