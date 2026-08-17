"""Shared CLI runtime: parameter building, execution and output rendering."""

from __future__ import annotations

import asyncio
import dataclasses
import json
from collections.abc import Awaitable, Callable, Coroutine
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from .. import sarif, toon
from ..client import AsyncMwdbClient
from ..exceptions import MwdbError
from ..models import ObjectItem
from .specs import Spec


def parse_json(
    ctx: click.Context, param: click.Parameter, value: str | None
) -> Any | None:
    del ctx
    if value is None:
        return None
    try:
        return json.loads(value)
    except ValueError as error:
        raise click.BadParameter(f"invalid JSON: {error}", param=param) from error


def _parse_value(ctx: click.Context, param: click.Parameter, value: str) -> Any:
    del ctx, param
    try:
        return json.loads(value)
    except ValueError:
        return value


def _click_params(spec: Spec) -> list[click.Parameter]:
    params: list[click.Parameter] = []
    for param in spec.params:
        flag = f"--{param.name.replace('_', '-')}"
        if param.kind == "bool":
            params.append(
                click.Option([flag], type=click.BOOL, default=None, help=param.help)
            )
        elif param.kind == "multi":
            params.append(click.Option([flag], multiple=True, help=param.help))
        elif param.required:
            callback = {"json": parse_json, "value": _parse_value}.get(param.kind)
            argument_type = int if param.kind == "int" else str
            params.append(
                click.Argument([param.name], type=argument_type, callback=callback)
            )
        else:
            callback = {"json": parse_json, "value": _parse_value}.get(param.kind)
            option_type = int if param.kind == "int" else str
            params.append(
                click.Option(
                    [flag], type=option_type, callback=callback, help=param.help
                )
            )
    return params


def run_async[T](coroutine: Coroutine[Any, Any, T]) -> T:
    try:
        return asyncio.run(coroutine)
    except MwdbError as error:
        raise click.ClickException(error.message) from error
    except OSError as error:
        # Local filesystem failures (permission denied, disk full, unwritable
        # output directory) must read as a clean CLI message, not a traceback.
        raise click.ClickException(str(error)) from error


def client_from(ctx_obj: dict[str, Any]) -> AsyncMwdbClient:
    return AsyncMwdbClient(
        ctx_obj.get("url"),
        ctx_obj.get("api_key"),
        config_path=ctx_obj.get("config_path"),
    )


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(entry) for entry in value)
    return str(value)


_TABLE_SKIP_FIELDS = frozenset({"raw", "md5", "sha1", "sha256"})


def _model_table(items: list[ObjectItem]) -> Table:
    names = [
        field.name
        for field in dataclasses.fields(items[0])
        if field.name not in _TABLE_SKIP_FIELDS
    ]
    table = Table(*names)
    for item in items:
        table.add_row(*[_cell(getattr(item, name)) for name in names])
    return table


def _to_jsonable(result: Any) -> Any:
    if isinstance(result, ObjectItem):
        return result.raw
    if isinstance(result, list):
        return [_to_jsonable(entry) for entry in result]
    if isinstance(result, Path):
        return str(result)
    return result


def _emit_json(result: Any) -> None:
    click.echo(json.dumps(_to_jsonable(result), indent=2, sort_keys=True))


def _emit_table(result: Any) -> None:
    if isinstance(result, str):
        click.echo(result)
        return
    if isinstance(result, ObjectItem | Path):
        _emit_json(result)
        return
    if result and isinstance(result, list) and isinstance(result[0], ObjectItem):
        Console().print(_model_table(result))
        return
    Console().print_json(json.dumps(_to_jsonable(result)))


def emit(result: Any, fmt: str) -> None:
    if fmt == "json":
        _emit_json(result)
        return
    if fmt == "toon":
        click.echo(toon.encode(_to_jsonable(result)))
        return
    if fmt == "sarif":
        if not sarif.is_supported(result):
            raise click.ClickException(
                "SARIF output is not available for this command."
            )
        click.echo(json.dumps(sarif.encode(result), indent=2, sort_keys=True))
        return
    if result is None:
        click.echo("ok")
        return
    _emit_table(result)


def clean_options(options: dict[str, Any]) -> dict[str, Any]:
    """Drop unset options and expand click's multiple-value tuples to lists."""
    return {
        name: (list(value) if isinstance(value, tuple) else value)
        for name, value in options.items()
        if value is not None and value != ()
    }


def build_command(spec: Spec) -> click.Command:
    def callback(**cli_kwargs: Any) -> None:
        ctx = click.get_current_context()
        kwargs = clean_options(cli_kwargs)

        async def run() -> Any:
            async with client_from(ctx.obj) as client:
                method: Callable[..., Awaitable[Any]] = getattr(
                    getattr(client, spec.namespace), spec.method
                )
                return await method(**kwargs)

        emit(run_async(run()), ctx.obj["format"])

    return click.Command(
        spec.name, params=_click_params(spec), callback=callback, help=spec.help
    )
