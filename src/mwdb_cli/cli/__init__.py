"""Command-line interface exposing every MWDB Core API operation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import click

from .. import __version__
from .files import file_download, file_download_by_token, file_reupload, file_upload
from .runtime import build_command, client_from, emit, run_async
from .specs import GROUP_HELP, SPECS


@click.group()
@click.version_option(__version__)
@click.option("--url", help="MWDB instance URL (default: https://mwdb.cert.pl).")
@click.option("--api-key", help="API key (or set MWDB_API_KEY).")
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    help="Config file path (default: ~/.mwdb.toml).",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "toon", "sarif"]),
    default=None,
    help="Output format (default: table). SARIF is only available for "
    "sample/object commands.",
)
@click.option("--json", "as_json", is_flag=True, help="Alias for --format json.")
@click.pass_context
def main(
    ctx: click.Context,
    url: str | None,
    api_key: str | None,
    config_path: Path | None,
    output_format: str | None,
    as_json: bool,
) -> None:
    """Command-line client for the MWDB Core API."""
    ctx.obj = {
        "url": url,
        "api_key": api_key,
        "config_path": config_path,
        "format": output_format or ("json" if as_json else "table"),
    }


GROUPS: dict[str, click.Group] = {}
for group_name, group_help in GROUP_HELP.items():
    group = click.Group(group_name, help=group_help)
    GROUPS[group_name] = group
    main.add_command(group)

for spec in SPECS:
    GROUPS[spec.group].add_command(build_command(spec))


@main.command("search")
@click.argument("query")
@click.pass_context
def search(ctx: click.Context, query: str) -> None:
    """Search objects with the deprecated POST /search endpoint."""

    async def run() -> Any:
        async with client_from(ctx.obj) as client:
            return await client.search_api.search(query)

    emit(run_async(run()), ctx.obj["format"])


for command in (file_upload, file_reupload, file_download, file_download_by_token):
    GROUPS["file"].add_command(command)
