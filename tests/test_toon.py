"""Exact-output tests for the TOON encoder."""

from __future__ import annotations

from mwdb_cli import toon

from .checks import check_eq


def test_flat_dict() -> None:
    check_eq(toon.encode({"status": "ok", "count": 3}), "status: ok\ncount: 3")


def test_nested_dict_and_primitive_list() -> None:
    encoded = toon.encode(
        {"server": {"version": "2.18.0"}, "friends": ["alice", "bob", "charlie"]}
    )
    check_eq(encoded, "server:\n  version: 2.18.0\nfriends[3]: alice,bob,charlie")


def test_uniform_object_list_is_tabular() -> None:
    encoded = toon.encode(
        [
            {"id": 1, "name": "Ada", "role": "admin"},
            {"id": 2, "name": "Bob", "role": "user"},
        ]
    )
    check_eq(encoded, "[2]{id,name,role}:\n  1,Ada,admin\n  2,Bob,user")


def test_dict_with_uniform_list_value() -> None:
    encoded = toon.encode({"users": [{"id": 1, "name": "Ada"}]})
    check_eq(encoded, "users[1]{id,name}:\n  1,Ada")


def test_non_uniform_list_falls_back_to_items() -> None:
    # TOON §10: the first field shares the hyphen line; the rest indent below.
    encoded = toon.encode([{"a": 1}, {"a": 1, "b": 2}])
    check_eq(encoded, "[2]:\n  - a: 1\n  - a: 1\n    b: 2")


def test_list_of_lists_fallback() -> None:
    encoded = toon.encode([["a", "b"], ["c"]])
    check_eq(encoded, "[2]:\n  - [2]: a,b\n  - [1]: c")


def test_list_with_empty_dict_item() -> None:
    check_eq(toon.encode([{}, {}]), "[2]:\n  -\n  -")


def test_mixed_list_with_dict_and_scalar() -> None:
    check_eq(toon.encode([{"a": 1}, "text"]), "[2]:\n  - a: 1\n  - text")


def test_empty_and_scalar_edge_cases() -> None:
    # TOON §5: conforming encoders emit "[]", never the legacy "[0]:" header.
    check_eq(toon.encode({"tags": []}), "tags: []")
    check_eq(toon.encode([]), "[]")
    check_eq(toon.encode([[]]), "[1]:\n  - []")
    check_eq(toon.encode("hello"), "hello")
    check_eq(toon.encode(42), "42")
    check_eq(toon.encode(None), "null")


def test_scalar_quoting() -> None:
    encoded = toon.encode(
        {
            "comma": "a,b",
            "colon": "has: colon",
            "empty": "",
            "pad": " x ",
            "none": None,
            "yes": True,
            "no": False,
            "num": 3.5,
            "quote": 'say "hi"',
            "newline": "a\nb",
        }
    )
    expected = (
        'comma: "a,b"\n'
        'colon: "has: colon"\n'
        'empty: ""\n'
        'pad: " x "\n'
        "none: null\n"
        "yes: true\n"
        "no: false\n"
        "num: 3.5\n"
        'quote: "say \\"hi\\""\n'
        'newline: "a\\nb"'
    )
    check_eq(encoded, expected)


def test_quoted_key_and_empty_nested_dict() -> None:
    check_eq(toon.encode({"a:b": 1}), '"a:b": 1')
    check_eq(toon.encode({"outer": {}}), "outer:")


def test_structural_and_control_characters_are_quoted() -> None:
    # TOON §7.2: brackets/braces, backslash, and a leading "-" or "#" must be
    # quoted so the value cannot be read as structure, a list item or a comment.
    check_eq(toon.encode({"name": "file[1].exe"}), 'name: "file[1].exe"')
    check_eq(toon.encode("a{b}c"), '"a{b}c"')
    check_eq(toon.encode("-flag"), '"-flag"')
    check_eq(toon.encode("#note"), '"#note"')
    check_eq(toon.encode("+5"), '"+5"')
    # §7.1: backslash, tab and carriage return are escaped inside quotes;
    # other control characters (U+0000–U+001F) become \uXXXX.
    check_eq(toon.encode("a\\b"), '"a\\\\b"')
    check_eq(toon.encode("a\tb"), '"a\\tb"')
    check_eq(toon.encode("a\rb"), '"a\\rb"')
    check_eq(toon.encode("a\x01b"), '"a\\u0001b"')
    # A middle space alone never forces quoting.
    check_eq(toon.encode("hello world"), "hello world")


def test_strings_colliding_with_scalars_are_quoted() -> None:
    # A string that reads as a bool/null/number must be quoted to keep its type.
    check_eq(toon.encode("true"), '"true"')
    check_eq(toon.encode("null"), '"null"')
    check_eq(toon.encode("123"), '"123"')
    check_eq(toon.encode("-3.5"), '"-3.5"')
    check_eq(toon.encode("1e5"), '"1e5"')
    # Genuine text (including hashes with letters) stays unquoted.
    check_eq(toon.encode("emotet"), "emotet")
    check_eq(toon.encode("9e365ca26d0b"), "9e365ca26d0b")
    # Real numeric values remain bare, not quoted.
    check_eq(toon.encode(123), "123")
    check_eq(toon.encode(True), "true")
