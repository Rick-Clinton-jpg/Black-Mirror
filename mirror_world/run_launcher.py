"""Observer-side, one-process-per-registration launch boundary.

Run this on a host the agent VM cannot write. The trusted worker is launched
once as a child process (normally an SSH command into the VM); it cannot choose
which attempts enter the census. The worker protocol is deliberately small.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

from mirror_world import anchor
from mirror_world.hashchain import canonical
from mirror_world.run_store import RunStore, RunStoreError

MAX_WORKER_OUTPUT = 1_048_576


class LaunchError(RuntimeError):
    """A registered launch failed; its run remains in the observer census."""


def _exclusive_json(path: Path, value: dict) -> None:
    encoded = canonical(value) + b"\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)


def _snapshot(source: Path, dest: Path) -> str:
    if not source.is_file() or source.is_symlink():
        raise LaunchError("source and config must be regular files, not symlinks")
    fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    digest = hashlib.sha256()
    with os.fdopen(fd, "wb") as target, source.open("rb") as original:
        for chunk in iter(lambda: original.read(1024 * 1024), b""):
            digest.update(chunk)
            target.write(chunk)
        target.flush()
        os.fsync(target.fileno())
    return digest.hexdigest()


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise LaunchError(f"duplicate worker key: {key}")
        result[key] = value
    return result


def _invalid_constant(value):
    raise LaunchError(f"nonfinite worker value: {value}")


def launch_once(
    store: RunStore, *, source_archive: str | Path, config_file: str | Path,
    model_id: str, design_known: bool, command: list[str], timeout: float,
) -> dict:
    """Register, spawn exactly once, and record close, crash, or timeout.

    The worker receives one JSON request on stdin. On successful exit it must
    print one JSON object with ``trace_path``, ``closing``, ``steps``,
    ``executed_source_sha256`` and ``executed_config_sha256``. The two executed
    digests are a trusted-worker assertion; the observer checks them against
    its own retained byte-for-byte snapshots. Agent code must not be able to
    write the observer directories or control this worker process.
    """
    if not command or any(type(arg) is not str or not arg for arg in command):
        raise ValueError("command must be a nonempty argument vector")
    if type(timeout) not in (int, float) or not 0 < timeout <= 3600:
        raise ValueError("timeout must be between 0 and 3600 seconds")
    source_archive, config_file = Path(source_archive), Path(config_file)
    # Reserve a run before any worker is launched. The snapshots are retained
    # under the observer's authority and become the exact hash inputs.
    start = anchor.start_record(anchor.file_digest(source_archive),
                                anchor.file_digest(config_file))
    registration = anchor.register_start(start, store.ledger)
    run_id = store.begin(start, registration, model_id=model_id,
                         design_known=design_known)
    asset_dir = store.root / f"{run_id}.assets"
    pid = None
    proc = None
    outcome = "launch_error"
    accepted_close = False
    try:
        asset_dir.mkdir(mode=0o700)
        source_hash = _snapshot(source_archive, asset_dir / "source.archive")
        config_hash = _snapshot(config_file, asset_dir / "config.json")
        if source_hash != start["source_sha256"] or config_hash != start["config_sha256"]:
            raise LaunchError("source or config changed while being snapshotted")
        command_hash = hashlib.sha256(canonical(command)).hexdigest()
        _exclusive_json(asset_dir / "attempt.json", {
            "run_id": run_id, "source_sha256": source_hash,
            "config_sha256": config_hash, "command_sha256": command_hash,
            "timeout_seconds": timeout, "model_id_claim": model_id,
        })
        request = canonical({
            "start": start, "registration": registration,
            "source_archive_path": str(asset_dir / "source.archive"),
            "config_path": str(asset_dir / "config.json"),
        }) + b"\n"
        # No shell and no private retry loop. The trusted worker may itself
        # hide launches, which is a stated residual trust assumption.
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, start_new_session=True)
        pid = proc.pid
        _exclusive_json(asset_dir / "process.json", {"run_id": run_id, "pid": pid})
        try:
            stdout, stderr = proc.communicate(input=request, timeout=timeout)
        except subprocess.TimeoutExpired:
            outcome = "timeout"
            os.killpg(proc.pid, signal.SIGKILL)
            stdout, stderr = proc.communicate()
            raise LaunchError("worker timed out")
        if len(stdout) > MAX_WORKER_OUTPUT or len(stderr) > MAX_WORKER_OUTPUT:
            outcome = "invalid_result"
            raise LaunchError("worker output exceeds 1 MiB per stream")
        if proc.returncode != 0:
            outcome = "crash"
            raise LaunchError(f"worker exited with status {proc.returncode}")
        outcome = "invalid_result"
        try:
            report = json.loads(stdout, object_pairs_hook=_unique,
                                parse_constant=_invalid_constant)
        except (ValueError, UnicodeError) as exc:
            raise LaunchError(f"invalid worker response: {exc}") from exc
        if type(report) is not dict or report.keys() != {
            "trace_path", "closing", "steps", "executed_source_sha256", "executed_config_sha256"
        }:
            raise LaunchError("worker response has wrong fields")
        if report["executed_source_sha256"] != source_hash or report["executed_config_sha256"] != config_hash:
            raise LaunchError("worker did not execute the retained source and config")
        if type(report["trace_path"]) is not str or not Path(report["trace_path"]).is_absolute():
            raise LaunchError("worker trace path must be absolute")
        if type(report["steps"]) is not list or len(report["steps"]) > 1000:
            raise LaunchError("invalid worker steps")
        for step in report["steps"]:
            if type(step) is not dict or step.keys() != {"action", "response", "resource_id"}:
                raise LaunchError("invalid worker step")
            store.step(run_id, **step)
        receipt = anchor.accept_close(report["trace_path"], start,
                                      report["closing"], store.ledger)
        accepted_close = True
        store.finish(run_id, trace_path=report["trace_path"], closing=report["closing"])
        outcome = "accepted"
        return {"run_id": run_id, "status": outcome, "steps": len(report["steps"]),
                "receipt": receipt}
    except BaseException:
        if proc is not None and proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
        if accepted_close:
            outcome = "repair_needed"
        elif store.load(run_id).status == "open":
            store.abort(run_id, reason=outcome)
        raise
    finally:
        if asset_dir.is_dir():
            _exclusive_json(asset_dir / "outcome.json", {"run_id": run_id,
                            "status": outcome, "pid": pid})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Observer-owned one-shot run launcher")
    parser.add_argument("--store", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--design-known", action="store_true")
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    try:
        result = launch_once(RunStore(args.store, args.ledger),
                             source_archive=args.source, config_file=args.config,
                             model_id=args.model_id, design_known=args.design_known,
                             command=command, timeout=args.timeout)
    except (LaunchError, RunStoreError, anchor.AnchorError, OSError, ValueError) as exc:
        print(f"launch failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
