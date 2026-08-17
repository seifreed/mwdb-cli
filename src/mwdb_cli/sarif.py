"""Render MWDB sample/object results as a SARIF 2.1.0 document.

SARIF is a static-analysis findings schema, so it only fits MWDB commands that
return samples/objects (file/config/blob/object listings and details, and
search). Each object becomes one SARIF result whose artifact is the sample and
whose ruleId is its malware family or tag.

Reference: https://docs.oasis-open.org/sarif/sarif/v2.1.0/
"""

from __future__ import annotations

from typing import Any

from ._version import __version__
from .models import ObjectItem

SARIF_VERSION = "2.1.0"
SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
TOOL_NAME = "mwdb-cli"
TOOL_URI = "https://github.com/seifreed/mwdb-cli"


def _as_objects(result: Any) -> list[dict[str, Any]] | None:
    """Normalize a supported result to a list of raw object payloads, else None."""
    items = result if isinstance(result, list) else [result]
    if not items:
        return None
    payloads: list[dict[str, Any]] = []
    for item in items:
        if isinstance(item, ObjectItem):
            payloads.append(item.raw)
        elif isinstance(item, dict) and "id" in item and "type" in item:
            payloads.append(item)
        else:
            return None
    return payloads


def is_supported(result: Any) -> bool:
    """Whether ``result`` is a sample/object payload SARIF can represent."""
    return _as_objects(result) is not None


def _tags(payload: dict[str, Any]) -> list[str]:
    return [entry["tag"] for entry in payload.get("tags", []) if "tag" in entry]


def _rule_id(payload: dict[str, Any]) -> str:
    family = payload.get("family")
    if isinstance(family, str) and family:
        return family
    tags = _tags(payload)
    if tags:
        return tags[0]
    return str(payload["type"])


def _message(payload: dict[str, Any]) -> str:
    identifier = payload.get("sha256") or payload["id"]
    name = payload.get("file_name")
    label = f"{payload['type']} {identifier}"
    if name:
        label += f" ({name})"
    tags = _tags(payload)
    if tags:
        label += f" tags: {', '.join(tags)}"
    return label


def _result(payload: dict[str, Any]) -> dict[str, Any]:
    identifier = payload.get("sha256") or payload["id"]
    return {
        "ruleId": _rule_id(payload),
        "level": "warning",
        "message": {"text": _message(payload)},
        "locations": [
            {"physicalLocation": {"artifactLocation": {"uri": str(identifier)}}}
        ],
        "properties": payload,
    }


def _artifact(payload: dict[str, Any]) -> dict[str, Any]:
    identifier = payload.get("sha256") or payload["id"]
    return {"location": {"uri": str(identifier)}}


def encode(result: Any) -> dict[str, Any]:
    """Build a SARIF 2.1.0 document for a supported sample/object result."""
    payloads = _as_objects(result)
    if payloads is None:
        raise ValueError("result is not a SARIF-representable sample/object")
    rules = {
        _rule_id(payload): {"id": _rule_id(payload), "name": _rule_id(payload)}
        for payload in payloads
    }
    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": TOOL_NAME,
                        "version": __version__,
                        "informationUri": TOOL_URI,
                        "rules": list(rules.values()),
                    }
                },
                "artifacts": [_artifact(payload) for payload in payloads],
                "results": [_result(payload) for payload in payloads],
            }
        ],
    }
