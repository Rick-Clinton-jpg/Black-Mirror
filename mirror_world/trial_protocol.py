"""Shared exact-byte action decoding for the observer and guest worker."""

from __future__ import annotations

import json


MAX_ACTION_BYTES = 512 * 1024
_REQUIRED = {
    "read_resource": {"resource"},
    "write_resource": {"resource", "content"},
    "request_capability": {"capability"},
    "differential_query": {"query", "backing"},
    "delegate": {"to_agent", "authority"},
}


def _unique(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate action key: {key}")
        result[key] = value
    return result


def _nonfinite(value: str):
    raise ValueError(f"nonfinite action value: {value}")


def decode_action(raw: bytes) -> dict:
    """Reject ambiguous or unsupported actions before executing guest code."""
    if type(raw) is not bytes or len(raw) > MAX_ACTION_BYTES:
        raise ValueError("invalid action bytes")
    try:
        command = json.loads(raw, object_pairs_hook=_unique, parse_constant=_nonfinite)
    except (UnicodeError, RecursionError) as exc:
        raise ValueError("invalid action JSON") from exc
    if type(command) is not dict or type(command.get("op")) is not str:
        raise ValueError("action must be an object with an operation")
    op = command["op"]
    if op not in _REQUIRED:
        raise ValueError("unsupported trial action")
    allowed = _REQUIRED[op] | {"op", "rationale"} | (
        {"dual_token"} if op in {"write_resource", "request_capability", "delegate"} else set()
    )
    if not _REQUIRED[op] <= command.keys() or not command.keys() <= allowed:
        raise ValueError("invalid trial action fields")
    return command
