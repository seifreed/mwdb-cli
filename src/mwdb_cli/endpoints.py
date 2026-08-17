"""Registry of every MWDB Core API operation (spec 2.18.0, 122 operations).

Each entry maps an operation name to its HTTP method and path template.
A regression test pins the operation count and asserts every entry is
referenced by a client method, guaranteeing full API coverage.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Endpoint:
    """One API operation: HTTP method plus path template."""

    method: str
    path: str

    def format(self, **params: str) -> str:
        """Fill path template parameters."""
        return self.path.format(**params)


ENDPOINTS: dict[str, Endpoint] = {
    # API keys
    "api_key_delete": Endpoint("DELETE", "/api_key/{api_key_id}"),
    "user_api_key_create": Endpoint("POST", "/user/{login}/api_key"),
    # Attribute key definitions
    "attribute_key_list": Endpoint("GET", "/attribute"),
    "attribute_key_create": Endpoint("POST", "/attribute"),
    "attribute_key_get": Endpoint("GET", "/attribute/{key}"),
    "attribute_key_update": Endpoint("PUT", "/attribute/{key}"),
    "attribute_key_delete": Endpoint("DELETE", "/attribute/{key}"),
    "attribute_key_permissions": Endpoint("GET", "/attribute/{key}/permissions"),
    "attribute_key_permission_set": Endpoint("PUT", "/attribute/{key}/permissions"),
    "attribute_key_permission_delete": Endpoint(
        "DELETE", "/attribute/{key}/permissions"
    ),
    # Authentication
    "auth_login": Endpoint("POST", "/auth/login"),
    "auth_refresh": Endpoint("POST", "/auth/refresh"),
    "auth_validate": Endpoint("GET", "/auth/validate"),
    "auth_groups": Endpoint("GET", "/auth/groups"),
    "auth_register": Endpoint("POST", "/auth/register"),
    "auth_change_password": Endpoint("POST", "/auth/change_password"),
    "auth_recover_password": Endpoint("POST", "/auth/recover_password"),
    "auth_request_password_change": Endpoint("POST", "/auth/request_password_change"),
    # Blobs
    "blob_list": Endpoint("GET", "/blob"),
    "blob_create": Endpoint("POST", "/blob"),
    "blob_get": Endpoint("GET", "/blob/{identifier}"),
    "blob_put": Endpoint("PUT", "/blob/{identifier}"),
    "blob_delete": Endpoint("DELETE", "/blob/{identifier}"),
    # Configs
    "config_list": Endpoint("GET", "/config"),
    "config_create": Endpoint("POST", "/config"),
    "config_stats": Endpoint("GET", "/config/stats"),
    "config_get": Endpoint("GET", "/config/{identifier}"),
    "config_put": Endpoint("PUT", "/config/{identifier}"),
    "config_delete": Endpoint("DELETE", "/config/{identifier}"),
    # Files
    "file_list": Endpoint("GET", "/file"),
    "file_upload": Endpoint("POST", "/file"),
    "file_get": Endpoint("GET", "/file/{identifier}"),
    "file_reupload": Endpoint("POST", "/file/{identifier}"),
    "file_delete": Endpoint("DELETE", "/file/{identifier}"),
    "file_download": Endpoint("GET", "/file/{identifier}/download"),
    "file_download_token": Endpoint("POST", "/file/{identifier}/download"),
    "file_download_zip": Endpoint("GET", "/file/{identifier}/download/zip"),
    "file_download_zip_token": Endpoint("POST", "/file/{identifier}/download/zip"),
    "download": Endpoint("GET", "/download/{access_token}"),
    "request_sample": Endpoint("POST", "/request/sample/{identifier}"),
    # Groups
    "group_list": Endpoint("GET", "/group"),
    "group_get": Endpoint("GET", "/group/{name}"),
    "group_create": Endpoint("POST", "/group/{name}"),
    "group_update": Endpoint("PUT", "/group/{name}"),
    "group_delete": Endpoint("DELETE", "/group/{name}"),
    "group_member_add": Endpoint("POST", "/group/{name}/member/{login}"),
    "group_member_update": Endpoint("PUT", "/group/{name}/member/{login}"),
    "group_member_delete": Endpoint("DELETE", "/group/{name}/member/{login}"),
    # Metakeys (legacy attribute API)
    "meta_key_list": Endpoint("GET", "/meta/list/{access}"),
    "metakey_definitions": Endpoint("GET", "/meta/manage"),
    "metakey_get": Endpoint("GET", "/meta/manage/{key}"),
    "metakey_create": Endpoint("POST", "/meta/manage/{key}"),
    "metakey_update": Endpoint("PUT", "/meta/manage/{key}"),
    "metakey_delete": Endpoint("DELETE", "/meta/manage/{key}"),
    "metakey_permission_set": Endpoint(
        "PUT", "/meta/manage/{key}/permissions/{group_name}"
    ),
    "metakey_permission_delete": Endpoint(
        "DELETE", "/meta/manage/{key}/permissions/{group_name}"
    ),
    # OAuth / OpenID Connect
    "oauth_provider_list": Endpoint("GET", "/oauth"),
    "oauth_provider_create": Endpoint("POST", "/oauth"),
    "oauth_identities": Endpoint("GET", "/oauth/identities"),
    "oauth_provider_get": Endpoint("GET", "/oauth/{provider_name}"),
    "oauth_provider_update": Endpoint("PUT", "/oauth/{provider_name}"),
    "oauth_provider_delete": Endpoint("DELETE", "/oauth/{provider_name}"),
    "oauth_authenticate": Endpoint("POST", "/oauth/{provider_name}/authenticate"),
    "oauth_bind_account": Endpoint("POST", "/oauth/{provider_name}/bind_account"),
    "oauth_logout": Endpoint("GET", "/oauth/{provider_name}/logout"),
    # Objects
    "object_list": Endpoint("GET", "/object"),
    "object_get": Endpoint("GET", "/object/{identifier}"),
    "object_delete": Endpoint("DELETE", "/object/{identifier}"),
    "object_favorite": Endpoint("PUT", "/object/{identifier}/favorite"),
    "object_unfavorite": Endpoint("DELETE", "/object/{identifier}/favorite"),
    "object_share_3rd_party": Endpoint("PUT", "/object/{identifier}/share_3rd_party"),
    # Typed object sub-resources
    "object_count": Endpoint("GET", "/{type}/count"),
    "quick_query_list": Endpoint("GET", "/{type}/quick_query"),
    "quick_query_create": Endpoint("POST", "/{type}/quick_query"),
    "quick_query_delete": Endpoint("DELETE", "/quick_query/{id}"),
    "object_attributes": Endpoint("GET", "/{type}/{identifier}/attribute"),
    "object_attribute_add": Endpoint("POST", "/{type}/{identifier}/attribute"),
    "object_attribute_delete": Endpoint(
        "DELETE", "/{type}/{identifier}/attribute/{attribute_id}"
    ),
    "object_comments": Endpoint("GET", "/{type}/{identifier}/comment"),
    "object_comment_add": Endpoint("POST", "/{type}/{identifier}/comment"),
    "object_comment_delete": Endpoint(
        "DELETE", "/{type}/{identifier}/comment/{comment_id}"
    ),
    "object_karton_list": Endpoint("GET", "/{type}/{identifier}/karton"),
    "object_karton_resubmit": Endpoint("POST", "/{type}/{identifier}/karton"),
    "object_karton_get": Endpoint("GET", "/{type}/{identifier}/karton/{analysis_id}"),
    "object_karton_assign": Endpoint(
        "PUT", "/{type}/{identifier}/karton/{analysis_id}"
    ),
    "object_karton_delete": Endpoint(
        "DELETE", "/{type}/{identifier}/karton/{analysis_id}"
    ),
    "object_meta_get": Endpoint("GET", "/{type}/{identifier}/meta"),
    "object_meta_add": Endpoint("POST", "/{type}/{identifier}/meta"),
    "object_meta_delete": Endpoint("DELETE", "/{type}/{identifier}/meta"),
    "object_relations": Endpoint("GET", "/{type}/{identifier}/relations"),
    "object_shares": Endpoint("GET", "/{type}/{identifier}/share"),
    "object_share": Endpoint("PUT", "/{type}/{identifier}/share"),
    "object_tags": Endpoint("GET", "/{type}/{identifier}/tag"),
    "object_tag_add": Endpoint("PUT", "/{type}/{identifier}/tag"),
    "object_tag_delete": Endpoint("DELETE", "/{type}/{identifier}/tag"),
    "object_child_link": Endpoint("PUT", "/{type}/{parent}/child/{child}"),
    "object_child_unlink": Endpoint("DELETE", "/{type}/{parent}/child/{child}"),
    # Remotes
    "remote_list": Endpoint("GET", "/remote"),
    "remote_pull_file": Endpoint(
        "POST", "/remote/{remote_name}/pull/file/{identifier}"
    ),
    "remote_pull_config": Endpoint(
        "POST", "/remote/{remote_name}/pull/config/{identifier}"
    ),
    "remote_pull_blob": Endpoint(
        "POST", "/remote/{remote_name}/pull/blob/{identifier}"
    ),
    "remote_push_file": Endpoint(
        "POST", "/remote/{remote_name}/push/file/{identifier}"
    ),
    "remote_push_config": Endpoint(
        "POST", "/remote/{remote_name}/push/config/{identifier}"
    ),
    "remote_push_blob": Endpoint(
        "POST", "/remote/{remote_name}/push/blob/{identifier}"
    ),
    # Search
    "search": Endpoint("POST", "/search"),
    # Server / misc
    "ping": Endpoint("GET", "/ping"),
    "server_info": Endpoint("GET", "/server"),
    "server_admin_info": Endpoint("GET", "/server/admin"),
    "server_docs": Endpoint("GET", "/docs"),
    "varz": Endpoint("GET", "/varz"),
    "share_groups": Endpoint("GET", "/share"),
    "tag_list": Endpoint("GET", "/tag"),
    "profile_get": Endpoint("GET", "/profile/{login}"),
    # Users
    "user_list": Endpoint("GET", "/user"),
    "user_get": Endpoint("GET", "/user/{login}"),
    "user_create": Endpoint("POST", "/user/{login}"),
    "user_update": Endpoint("PUT", "/user/{login}"),
    "user_delete": Endpoint("DELETE", "/user/{login}"),
    "user_change_password_token": Endpoint("GET", "/user/{login}/change_password"),
    "user_pending_accept": Endpoint("POST", "/user/{login}/pending"),
    "user_pending_reject": Endpoint("DELETE", "/user/{login}/pending"),
    "user_request_password_change": Endpoint(
        "POST", "/user/{login}/request_password_change"
    ),
}
