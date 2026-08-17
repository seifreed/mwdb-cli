"""Encode JSON-able values as TOON (Token-Oriented Object Notation).

TOON is a compact, indentation-based serialization with tabular blocks for
arrays of uniform objects, designed to pass structured data to language models
with fewer tokens than JSON. Only encoding is implemented; MWDB output is
always serialized outward, never parsed back.

Reference: https://github.com/toon-format/toon
"""

from __future__ import annotations

import re
from typing import Any

INDENT = "  "
_AMBIGUOUS_LITERALS = frozenset({"true", "false", "null"})
_NUMBER_RE = re.compile(r"[+-]?[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?")
# Structural characters ([ ] { } : , " \) and any control char force quoting.
_STRUCTURAL_RE = re.compile(r'[\[\]{}:,"\\\x00-\x1f]')
# Translation table mapping every escaped character to its TOON sequence; the
# five named escapes plus \uXXXX for the remaining U+0000-U+001F controls.
_ESCAPE_TABLE: dict[int, str] = {
    ord("\\"): "\\\\",
    ord('"'): '\\"',
    ord("\n"): "\\n",
    ord("\r"): "\\r",
    ord("\t"): "\\t",
}
for _code in range(0x20):
    _ESCAPE_TABLE.setdefault(_code, f"\\u{_code:04x}")


def _scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    return _string(str(value))


def _needs_quote(text: str) -> bool:
    """Whether a string must be quoted to encode unambiguously (TOON §7.2)."""
    return (
        text == ""
        or text != text.strip(" \t")
        or text in _AMBIGUOUS_LITERALS
        or text[0] in "-#"
        or _NUMBER_RE.fullmatch(text) is not None
        or _STRUCTURAL_RE.search(text) is not None
    )


def _string(text: str) -> str:
    if not _needs_quote(text):
        return text
    return '"' + text.translate(_ESCAPE_TABLE) + '"'


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, str | int | float | bool)


def _uniform_fields(rows: list[Any]) -> list[str] | None:
    """Return shared field order if every row is a dict of scalars, else None."""
    if not all(isinstance(row, dict) for row in rows):
        return None
    fields = list(rows[0].keys())
    if not fields:
        return None
    field_set = set(fields)
    for row in rows:
        if set(row.keys()) != field_set or not all(
            _is_scalar(cell) for cell in row.values()
        ):
            return None
    return fields


def _encode_array(label: str, rows: list[Any], indent: str) -> str:
    """Encode a list. ``label`` is the key prefix ("" for a root/list array)."""
    if not rows:
        prefix = f"{label}: " if label else ""
        return f"{indent}{prefix}[]"
    head = f"{indent}{label}[{len(rows)}]"
    fields = _uniform_fields(rows)
    if fields is not None:
        columns = ",".join(_string(field) for field in fields)
        body = "\n".join(
            indent + INDENT + ",".join(_scalar(row[field]) for field in fields)
            for row in rows
        )
        return f"{head}{{{columns}}}:\n{body}"
    if all(_is_scalar(item) for item in rows):
        return f"{head}: " + ",".join(_scalar(item) for item in rows)
    body = "\n".join(_encode_item(item, indent + INDENT) for item in rows)
    return f"{head}:\n{body}"


def _encode_item(value: Any, indent: str) -> str:
    """Encode one non-uniform list element with its first line on the dash.

    ``- `` is exactly one ``INDENT`` wide, so the child is rendered one level
    deeper and the leading indent of its first line is swapped for the dash,
    keeping continuation lines aligned (TOON §10).
    """
    if isinstance(value, dict):
        if not value:
            return f"{indent}-"
        body = _encode_mapping(value, indent + INDENT)
    elif isinstance(value, list):
        body = _encode_array("", value, indent + INDENT)
    else:
        return f"{indent}- {_scalar(value)}"
    return indent + "- " + body[len(indent) + len(INDENT) :]


def _encode_mapping(mapping: dict[str, Any], indent: str) -> str:
    lines: list[str] = []
    for key, value in mapping.items():
        label = _string(str(key))
        if isinstance(value, dict):
            inner = _encode_mapping(value, indent + INDENT)
            head = f"{indent}{label}:"
            lines.append(f"{head}\n{inner}" if inner else head)
        elif isinstance(value, list):
            lines.append(_encode_array(label, value, indent))
        else:
            lines.append(f"{indent}{label}: {_scalar(value)}")
    return "\n".join(lines)


def encode(value: Any) -> str:
    """Serialize a JSON-able value to a TOON document."""
    if isinstance(value, dict):
        return _encode_mapping(value, "")
    if isinstance(value, list):
        return _encode_array("", value, "")
    return _scalar(value)
