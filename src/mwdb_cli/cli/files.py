"""Hand-written file commands: upload, reupload and concurrent downloads."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import click

from ..bulk import run_limited
from ..exceptions import MwdbError
from .runtime import clean_options, client_from, emit, parse_json, run_async


def safe_download_path(output_dir: Path, identifier: str, suffix: str = "") -> Path:
    """Build an output path for a downloaded sample, rejecting path traversal.

    Identifiers are content hashes, so anything that is not already a bare
    filename (a path separator, ``.``, ``..`` or an empty value) is treated
    as hostile: it could otherwise write the sample outside the chosen
    output directory.
    """
    if (
        not identifier
        or identifier in {".", ".."}
        or identifier != Path(identifier).name
    ):
        raise click.ClickException(f"Unsafe download identifier: {identifier!r}")
    return output_dir / f"{identifier}{suffix}"


@click.command("upload")
@click.argument("source", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--file-name")
@click.option("--parent")
@click.option("--upload-as")
@click.option("--tags", multiple=True)
@click.option("--attributes", callback=parse_json, help="JSON list of attributes.")
@click.option("--karton-id")
@click.option("--karton-arguments", callback=parse_json, help="JSON object.")
@click.option("--share-3rd-party", type=click.BOOL, default=None)
@click.pass_context
def file_upload(ctx: click.Context, /, source: Path, **options: Any) -> None:
    """Upload a file as a new sample."""
    kwargs = clean_options(options)

    async def run() -> Any:
        async with client_from(ctx.obj) as client:
            return await client.files.upload(source, **kwargs)

    emit(run_async(run()), ctx.obj["format"])


@click.command("reupload")
@click.argument("identifier")
@click.argument("source", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--file-name")
@click.option("--metakeys", callback=parse_json, help="JSON list of metakeys.")
@click.option("--upload-as")
@click.pass_context
def file_reupload(
    ctx: click.Context, /, identifier: str, source: Path, **options: Any
) -> None:
    """Re-upload an existing sample."""
    kwargs = clean_options(options)

    async def run() -> Any:
        async with client_from(ctx.obj) as client:
            return await client.files.reupload(identifier, source, **kwargs)

    emit(run_async(run()), ctx.obj["format"])


@click.command("download")
@click.argument("identifiers", nargs=-1, required=True)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("."),
)
@click.option("--obfuscate", is_flag=True)
@click.option("--zip", "as_zip", is_flag=True, help="Download zipped samples.")
@click.option(
    "--jobs", type=click.IntRange(min=1), default=4, help="Concurrent downloads."
)
@click.pass_context
def file_download(
    ctx: click.Context,
    identifiers: tuple[str, ...],
    output_dir: Path,
    obfuscate: bool,
    as_zip: bool,
    jobs: int,
) -> None:
    """Download one or many samples concurrently.

    Each sample is fetched independently: one that is missing or inaccessible
    is reported on stderr without aborting the rest, and the command exits
    non-zero if any download failed.
    """

    async def run() -> list[tuple[str, Path | MwdbError]]:
        output_dir.mkdir(parents=True, exist_ok=True)
        async with client_from(ctx.obj) as client:

            def task_for(
                identifier: str,
            ) -> Callable[[], Awaitable[tuple[str, Path | MwdbError]]]:
                suffix = ".zip" if as_zip else ""
                target = safe_download_path(output_dir, identifier, suffix)

                async def attempt() -> tuple[str, Path | MwdbError]:
                    try:
                        if as_zip:
                            return identifier, await client.files.download_zip(
                                identifier, target
                            )
                        return identifier, await client.files.download(
                            identifier, target, obfuscate=obfuscate
                        )
                    except MwdbError as error:
                        return identifier, error

                return attempt

            return await run_limited([task_for(i) for i in identifiers], jobs)

    results = run_async(run())
    failures = 0
    for identifier, outcome in results:
        if isinstance(outcome, Path):
            click.echo(str(outcome))
        else:
            failures += 1
            click.echo(f"failed: {identifier}: {outcome.message}", err=True)
    if failures:
        raise click.ClickException(f"{failures} of {len(results)} download(s) failed")


@click.command("download-by-token")
@click.argument("access_token")
@click.argument(
    "destination", type=click.Path(dir_okay=False, writable=True, path_type=Path)
)
@click.pass_context
def file_download_by_token(
    ctx: click.Context, access_token: str, destination: Path
) -> None:
    """Download a sample using a pre-issued access token."""

    async def run() -> Path:
        async with client_from(ctx.obj) as client:
            return await client.files.download_by_token(access_token, destination)

    emit(run_async(run()), ctx.obj["format"])
