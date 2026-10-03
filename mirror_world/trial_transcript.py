"""Observer-owned, exact-byte transcript for interactive trials.

The transcript is separate from the governor trace. It records the bytes that
cross the model/tool boundary, including content the trace intentionally omits.
Its local hash chain needs an outside checkpoint to detect tail deletion by
the observer host's owner.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
from pathlib import Path

from mirror_world.hashchain import ChainVerifier, GENESIS_HASH, canonical, seal

MAX_PAYLOAD_BYTES = 512 * 1024
MAX_TRANSCRIPT_BYTES = 16 * 1024 * 1024
_KINDS = frozenset({"model_input", "model_output", "tool_request", "tool_reply",
                    "worker_ready", "worker_frame", "worker_terminal"})


class TranscriptError(ValueError):
    """An exact transcript cannot be recorded or verified."""


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise TranscriptError(f"duplicate transcript key: {key}")
        result[key] = value
    return result


def _nonfinite(value):
    raise TranscriptError(f"nonfinite transcript value: {value}")


class TranscriptWriter:
    def __init__(self, path: str | Path, run_id: str):
        self.path = Path(path)
        self.run_id = run_id
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        self._stream = os.fdopen(fd, "wb", buffering=0)
        self.head = GENESIS_HASH
        self.count = 0
        self.size = 0
        directory = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

    def append(self, kind: str, payload: bytes, *, related_action: int | None = None) -> None:
        if kind not in _KINDS or type(payload) is not bytes:
            raise TranscriptError("invalid transcript event")
        if len(payload) > MAX_PAYLOAD_BYTES:
            raise TranscriptError("transcript payload exceeds exact-byte limit")
        if related_action is not None and (type(related_action) is not int or related_action < 1):
            raise TranscriptError("invalid related action")
        event = seal({
            "run_id": self.run_id, "seq": self.count + 1, "kind": kind,
            "payload_b64": base64.b64encode(payload).decode("ascii"),
            "payload_sha256": hashlib.sha256(payload).hexdigest(),
            "related_action": related_action,
        }, self.head)
        line = canonical(event) + b"\n"
        if self.size + len(line) > MAX_TRANSCRIPT_BYTES:
            raise TranscriptError("transcript exceeds exact-byte file limit")
        try:
            written = self._stream.write(line)
            if written != len(line):
                raise OSError("short transcript write")
            os.fsync(self._stream.fileno())
        except OSError as exc:
            raise TranscriptError(f"transcript append failed: {exc}") from exc
        self.head = event["record_hash"]
        self.count += 1
        self.size += len(line)

    def close(self) -> None:
        self._stream.close()


def verify_transcript(path: str | Path, run_id: str, *, expected: dict | None = None) -> dict:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise TranscriptError("transcript must be a regular file")
    verifier = ChainVerifier()
    file_hash = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for line in stream:
            size += len(line)
            if size > MAX_TRANSCRIPT_BYTES or len(line) > 2 * MAX_PAYLOAD_BYTES:
                raise TranscriptError("transcript exceeds size limit")
            file_hash.update(line)
            try:
                event = json.loads(line, object_pairs_hook=_unique,
                                   parse_constant=_nonfinite)
            except (ValueError, UnicodeError, RecursionError) as exc:
                raise TranscriptError(f"invalid transcript JSON: {exc}") from exc
            if type(event) is not dict or event.keys() != {
                "run_id", "seq", "kind", "payload_b64", "payload_sha256",
                "related_action", "previous_hash", "record_hash",
            }:
                raise TranscriptError("invalid transcript fields")
            if event["run_id"] != run_id or type(event["seq"]) is not int or event["seq"] != verifier.count + 1:
                raise TranscriptError("transcript run or sequence mismatch")
            if type(event["kind"]) is not str or event["kind"] not in _KINDS or type(event["payload_b64"]) is not str:
                raise TranscriptError("invalid transcript payload")
            if event["related_action"] is not None and (
                type(event["related_action"]) is not int or event["related_action"] < 1
            ):
                raise TranscriptError("invalid related action")
            try:
                payload = base64.b64decode(event["payload_b64"], validate=True)
            except (binascii.Error, ValueError) as exc:
                raise TranscriptError("invalid transcript base64") from exc
            if len(payload) > MAX_PAYLOAD_BYTES or hashlib.sha256(payload).hexdigest() != event["payload_sha256"]:
                raise TranscriptError("transcript byte digest mismatch")
            try:
                verifier.feed(event)
            except ValueError as exc:
                raise TranscriptError(f"transcript chain: {exc}") from exc
    checkpoint = {"count": verifier.count, "head": verifier.head,
                  "sha256": file_hash.hexdigest()}
    if expected is not None and checkpoint != expected:
        raise TranscriptError("transcript does not match retained checkpoint")
    return checkpoint
