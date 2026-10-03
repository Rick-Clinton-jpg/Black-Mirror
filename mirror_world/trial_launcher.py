"""Observer-side interactive trial launch with durable, exact-byte exchanges.

The child is a trusted controller, not an agent. It may operate an SSH session
to one VM guest, but it must not privately retry. The observer controls model
turns, records every exchange before delivery, and accepts only one close.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time
from typing import Callable

from mirror_world import anchor
from mirror_world.hashchain import canonical
from mirror_world.run_launcher import LaunchError, _exclusive_json, _snapshot, _unique, _invalid_constant
from mirror_world.run_store import RunStore, _model_id
from mirror_world.trial_transcript import TranscriptError, TranscriptWriter, verify_transcript

MAX_FRAME = 1_048_576
MAX_STDERR = 64 * 1024
MAX_ACTIONS = 12


@dataclass(frozen=True)
class ModelTurn:
    """Exact provider/adapter bytes and the selected mediated action."""

    model_input: bytes
    model_output: bytes
    action: bytes


@dataclass(frozen=True)
class FinalTurn:
    """Exact model input/output bytes for a terminal declaration."""

    model_input: bytes
    model_output: bytes


class TrialProtocolError(LaunchError):
    """The trusted worker violated the streaming contract."""


class TrialTimeout(TimeoutError):
    """A worker read, write, or exit exceeded the observer's deadline."""


class _Frames:
    def __init__(self, proc: subprocess.Popen, deadline: float):
        self.proc = proc
        self.deadline = deadline
        self.stdout = bytearray()
        self.stderr = bytearray()
        self.stderr_open = True
        for pipe in (proc.stdin, proc.stdout, proc.stderr):
            os.set_blocking(pipe.fileno(), False)

    def _left(self) -> float:
        left = self.deadline - time.monotonic()
        if left <= 0:
            raise TrialTimeout("trial wall deadline reached")
        return left

    def send(self, value: dict) -> None:
        raw = canonical(value) + b"\n"
        if len(raw) > MAX_FRAME:
            raise TrialProtocolError("input frame exceeds limit")
        fd = self.proc.stdin.fileno()
        offset = 0
        while offset < len(raw):
            _, writable, _ = select.select([], [fd], [], self._left())
            if not writable:
                raise TrialTimeout("trial input stalled")
            try:
                written = os.write(fd, raw[offset:])
                if written == 0:
                    raise TrialProtocolError("worker input made no progress")
                offset += written
            except (BrokenPipeError, OSError) as exc:
                raise TrialProtocolError("worker closed input") from exc

    def receive(self) -> tuple[dict, bytes]:
        out_fd, err_fd = self.proc.stdout.fileno(), self.proc.stderr.fileno()
        while True:
            newline = self.stdout.find(b"\n")
            if newline >= 0:
                raw = bytes(self.stdout[:newline + 1])
                del self.stdout[:newline + 1]
                if len(raw) > MAX_FRAME:
                    raise TrialProtocolError("worker frame exceeds limit")
                try:
                    value = json.loads(raw, object_pairs_hook=_unique,
                                       parse_constant=_invalid_constant)
                except (ValueError, UnicodeError, RecursionError) as exc:
                    raise TrialProtocolError("invalid worker JSON frame") from exc
                if type(value) is not dict:
                    raise TrialProtocolError("worker frame must be an object")
                return value, raw
            if len(self.stdout) >= MAX_FRAME:
                raise TrialProtocolError("worker frame exceeds limit")
            readable, _, _ = select.select(
                [out_fd] + ([err_fd] if self.stderr_open else []), [], [], self._left()
            )
            if not readable:
                raise TrialTimeout("trial worker stalled")
            if err_fd in readable:
                chunk = os.read(err_fd, 65536)
                if not chunk:
                    self.stderr_open = False
                self.stderr.extend(chunk)
                if len(self.stderr) > MAX_STDERR:
                    raise TrialProtocolError("worker stderr exceeds limit")
            if out_fd in readable:
                chunk = os.read(out_fd, 65536)
                if not chunk:
                    raise TrialProtocolError("worker closed output before terminal frame")
                self.stdout.extend(chunk)


def _decode_bytes(value: object) -> bytes:
    if type(value) is not str:
        raise TrialProtocolError("reply bytes must be base64 text")
    try:
        data = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise TrialProtocolError("invalid reply base64") from exc
    if len(data) > 512 * 1024:
        raise TrialProtocolError("reply exceeds exact-byte limit")
    return data


def _step(action: bytes, reply: bytes) -> dict:
    try:
        request = json.loads(action, object_pairs_hook=_unique,
                             parse_constant=_invalid_constant)
        response = json.loads(reply, object_pairs_hook=_unique,
                              parse_constant=_invalid_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise TrialProtocolError("action and reply must be JSON objects") from exc
    if type(request) is not dict or type(response) is not dict:
        raise TrialProtocolError("action and reply must be JSON objects")
    op = request.get("op")
    if type(op) is not str or not op or len(op) > 64:
        raise TrialProtocolError("invalid action operation")
    # Some valid operations return a scalar `response` field inside the
    # top-level result (for example differential_query returns "yes").
    # Only unwrap a nested object when it is actually a result envelope.
    result = response.get("response") if type(response.get("response")) is dict else response
    label = "ok" if result.get("ok") is True else "denied" if result.get("error") == "operation not authorized" else "error"
    resource = request.get("resource", request.get("capability"))
    if resource is not None and (type(resource) is not str or len(resource) > 256):
        resource = None
    return {"action": op, "response": label, "resource_id": resource}


def launch_trial(
    store: RunStore, *, source_archive: str | Path, config_file: str | Path,
    model_id: str, design_known: bool, command: list[str], timeout: float,
    next_turn: Callable[[tuple[bytes, ...]], ModelTurn | FinalTurn | None],
) -> dict:
    """One registration, one trusted worker, interactive model turns.

    ``next_turn`` is a trusted observer-host adapter. It receives exact prior
    tool replies and returns the exact model input/output bytes plus the chosen
    action, or None to finish. A scripted adapter is an integration test, not a
    live-model trial. The worker must send READY, one REPLY per action, then a
    TERMINAL frame; it may not control registration or model choices.
    """
    if not command or any(type(arg) is not str or not arg for arg in command):
        raise ValueError("command must be a nonempty argument vector")
    if type(timeout) not in (int, float) or not 0 < timeout <= 3600:
        raise ValueError("timeout must be between 0 and 3600 seconds")
    # Validate before observer registration; a malformed identifier must not
    # leave an orphan registration for an execution that could never start.
    _model_id(model_id)
    source_archive, config_file = Path(source_archive), Path(config_file)
    start = anchor.start_record(anchor.file_digest(source_archive), anchor.file_digest(config_file))
    registration = anchor.register_start(start, store.ledger)
    run_id = store.begin(start, registration, model_id=model_id, design_known=design_known)
    # Worker handoff and returned trace paths must be absolute even when a
    # caller constructed RunStore from a relative output directory.
    assets = store.root.resolve() / f"{run_id}.assets"
    proc = None
    transcript = None
    outcome = "launch_error"
    accepted_close = False
    pid = None
    transcript_checkpoint = None
    frames = None
    guest_stop_reported_and_worker_exited = False
    vm_image_id_claim = None
    try:
        assets.mkdir(mode=0o700)
        source_hash = _snapshot(source_archive, assets / "source.archive")
        config_hash = _snapshot(config_file, assets / "config.json")
        if source_hash != start["source_sha256"] or config_hash != start["config_sha256"]:
            raise LaunchError("source or config changed while being snapshotted")
        transcript = TranscriptWriter(assets / "transcript.jsonl", run_id)
        _exclusive_json(assets / "attempt.json", {
            "run_id": run_id, "source_sha256": source_hash,
            "config_sha256": config_hash,
            "command_sha256": hashlib.sha256(canonical(command)).hexdigest(),
            "timeout_seconds": timeout, "model_id_claim": model_id,
        })
        deadline = time.monotonic() + timeout
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, start_new_session=True)
        pid = proc.pid
        _exclusive_json(assets / "process.json", {"run_id": run_id, "pid": pid})
        frames = _Frames(proc, deadline)
        frames.send(dict(type="init", start=start, registration=registration,
                         source_archive_path=str(assets / "source.archive"),
                         config_path=str(assets / "config.json")))
        ready, raw = frames.receive()
        transcript.append("worker_ready", raw)
        if ready.keys() != {"type", "run_id", "source_sha256", "config_sha256", "vm_image_id"} or ready["type"] != "ready" or ready["run_id"] != run_id:
            raise TrialProtocolError("invalid ready frame")
        if ready["source_sha256"] != source_hash or ready["config_sha256"] != config_hash:
            raise TrialProtocolError("guest execution bytes differ from retained snapshots")
        if type(ready["vm_image_id"]) is not str or not 1 <= len(ready["vm_image_id"]) <= 256:
            raise TrialProtocolError("missing VM image identity")
        vm_image_id_claim = ready["vm_image_id"]
        replies = []
        actions = 0
        while True:
            try:
                turn = next_turn(tuple(replies))
            except Exception:
                outcome = "adapter_error"
                raise
            if turn is None:
                break
            if type(turn) is FinalTurn:
                if type(turn.model_input) is not bytes or type(turn.model_output) is not bytes:
                    raise TrialProtocolError("model adapter returned invalid final turn")
                transcript.append("model_input", turn.model_input)
                transcript.append("model_output", turn.model_output)
                break
            if type(turn) is not ModelTurn or any(type(x) is not bytes for x in (turn.model_input, turn.model_output, turn.action)):
                raise TrialProtocolError("model adapter returned invalid turn")
            if actions >= MAX_ACTIONS:
                raise TrialProtocolError("model exceeded action cap")
            actions += 1
            for kind, data in (("model_input", turn.model_input),
                               ("model_output", turn.model_output),
                               ("tool_request", turn.action)):
                transcript.append(kind, data, related_action=actions)
            frames.send(dict(type="action", run_id=run_id, seq=actions,
                             request_b64=base64.b64encode(turn.action).decode("ascii")))
            reply, raw = frames.receive()
            transcript.append("worker_frame", raw, related_action=actions)
            if reply.keys() != {"type", "run_id", "seq", "reply_b64"} or reply["type"] != "reply" or reply["run_id"] != run_id or type(reply["seq"]) is not int or reply["seq"] != actions:
                raise TrialProtocolError("invalid or out-of-order worker reply")
            reply_bytes = _decode_bytes(reply["reply_b64"])
            transcript.append("tool_reply", reply_bytes, related_action=actions)
            store.step(run_id, **_step(turn.action, reply_bytes))
            replies.append(reply_bytes)
        frames.send(dict(type="finish", run_id=run_id))
        final, raw = frames.receive()
        transcript.append("worker_terminal", raw)
        if final.keys() != {"type", "run_id", "trace_path", "closing", "source_sha256", "config_sha256", "host_effects", "guest_stopped"} or final["type"] != "terminal" or final["run_id"] != run_id:
            raise TrialProtocolError("invalid terminal frame")
        if final["source_sha256"] != source_hash or final["config_sha256"] != config_hash or final["guest_stopped"] is not True:
            raise TrialProtocolError("guest execution or stop is unconfirmed")
        if type(final["trace_path"]) is not str or not Path(final["trace_path"]).is_absolute() or type(final["host_effects"]) is not dict:
            raise TrialProtocolError("missing trace or host-effect snapshot")
        try:
            proc.wait(timeout=max(0.001, deadline - time.monotonic()))
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError("worker did not exit after terminal frame") from exc
        if proc.returncode != 0:
            raise TrialProtocolError("worker failed after terminal frame")
        guest_stop_reported_and_worker_exited = True
        verification = anchor.verify(final["trace_path"], start, final["closing"],
                                     registration=registration)
        if verification["integrity"] != "MATCH":
            raise TrialProtocolError("trace does not match closing anchor")
        _exclusive_json(assets / "host-effects.json", final["host_effects"])
        transcript.close()
        transcript_checkpoint = verify_transcript(assets / "transcript.jsonl", run_id)
        receipt = anchor.accept_close(final["trace_path"], start,
                                      final["closing"], store.ledger)
        accepted_close = True
        store.finish(run_id, trace_path=final["trace_path"], closing=final["closing"])
        outcome = "accepted"
        return {"run_id": run_id, "status": outcome, "actions": actions,
                "receipt": receipt, "transcript_path": str(assets / "transcript.jsonl")}
    except TrialTimeout:
        outcome = "timeout_guest_unconfirmed"
        raise
    except TranscriptError:
        outcome = "recording_failed"
        raise
    except Exception:
        if accepted_close:
            outcome = "repair_needed"
        elif outcome == "launch_error":
            outcome = "invalid_result" if proc is not None else "launch_error"
        raise
    finally:
        if proc is not None and proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.communicate()
        if transcript is not None:
            transcript.close()
            if transcript_checkpoint is None:
                try:
                    transcript_checkpoint = verify_transcript(assets / "transcript.jsonl", run_id)
                except TranscriptError as exc:
                    outcome = "recording_failed" if not accepted_close else "repair_needed"
                    transcript_checkpoint = {"error": str(exc)}
        if not accepted_close and store.load(run_id).status == "open":
            store.abort(run_id, reason=outcome)
        if assets.is_dir():
            stderr_digest = None
            if frames is not None and frames.stderr:
                fd = os.open(assets / "worker-stderr.bin",
                             os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(frames.stderr)
                    stream.flush()
                    os.fsync(stream.fileno())
                stderr_digest = hashlib.sha256(frames.stderr).hexdigest()
            _exclusive_json(assets / "outcome.json", {
                "run_id": run_id, "status": outcome, "pid": pid,
                "transcript": transcript_checkpoint,
                "worker_stderr_sha256": stderr_digest,
                "guest_stop_reported_and_worker_exited": guest_stop_reported_and_worker_exited,
                "vm_image_id_claim": vm_image_id_claim,
            })
