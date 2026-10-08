"""Run exactly one observer-side trial during a fresh disposable UTM boot.

The VM must be stopped before invocation. A durable lifecycle record is
created before boot, so even a failed boot is visible in the launch census.
This controls guest disk state; callers must also start a new model session.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid


MARKER = "$HOME/.black-mirror-trial-boot"
USED_MARKER = "$HOME/.black-mirror-trial-boot.used"
_DEST = re.compile(r"\A[A-Za-z0-9._-]+@[A-Za-z0-9.:-]+\Z")


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _record(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _run(argv: list[str], *, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=timeout, check=False)


def _status(utmctl: str, vm_id: str) -> str:
    result = _run([utmctl, "status", vm_id])
    if result.returncode:
        raise RuntimeError("UTM status query failed")
    return result.stdout.decode("utf-8", "replace").strip()


def _wait_for_status(utmctl: str, vm_id: str, wanted: str, deadline: float) -> bool:
    while time.monotonic() < deadline:
        if _status(utmctl, vm_id) == wanted:
            return True
        time.sleep(1)
    return _status(utmctl, vm_id) == wanted


def _stop(utmctl: str, vm_id: str) -> None:
    if _status(utmctl, vm_id) == "stopped":
        return
    _run([utmctl, "stop", "--request", vm_id])
    if _wait_for_status(utmctl, vm_id, "stopped", time.monotonic() + 30):
        return
    _run([utmctl, "stop", "--force", vm_id])
    if not _wait_for_status(utmctl, vm_id, "stopped", time.monotonic() + 15):
        raise RuntimeError("VM stop unconfirmed")


def run(args: argparse.Namespace) -> int:
    if not _DEST.fullmatch(args.destination):
        raise ValueError("invalid SSH destination")
    if not args.command or args.command[0] == "--":
        raise ValueError("one trial command is required after --")
    if not 1 <= args.port <= 65535 or args.boot_timeout < 1 or args.trial_timeout < 1:
        raise ValueError("invalid port or timeout")
    lifecycle = Path(args.lifecycle_dir)
    lifecycle.mkdir(parents=True, exist_ok=True)
    boot_id = uuid.uuid4().hex
    record_path = lifecycle / f"{boot_id}.json"
    record = {"boot_id": boot_id, "vm_id": args.vm_id,
              "created_at": _utc(), "state": "reserved", "trial_exit_code": None}
    _record(record_path, record)

    def update(state: str, **extra: object) -> None:
        record.update(state=state, updated_at=_utc(), **extra)
        _record(record_path, record)

    utmctl = args.utmctl
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
           "-o", "ConnectTimeout=5", "-p", str(args.port)]
    if args.identity:
        ssh += ["-i", args.identity]
    started = False
    lock_fd: int | None = None
    result_code = 1
    try:
        lock_name = hashlib.sha256(args.vm_id.encode()).hexdigest()[:24]
        lock_path = Path(tempfile.gettempdir()) / f"black-mirror-utm-{lock_name}.lock"
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if _status(utmctl, args.vm_id) != "stopped":
            raise RuntimeError("VM is already running; refusing a reused guest")
        update("booting")
        started = True
        boot = _run([utmctl, "start", "--disposable", args.vm_id], timeout=60)
        # A failed CLI call may still have started the guest. Always attempt
        # stop after invoking start, and report an unconfirmed stop if needed.
        if boot.returncode:
            raise RuntimeError(f"disposable UTM boot failed ({boot.returncode})")
        deadline = time.monotonic() + args.boot_timeout
        # A persistent marker from another run means this was not a fresh disk.
        # Leave the marker in place: the next disposable boot must lose it.
        remote = (
            f'test ! -e "{MARKER}" && test ! -e "{USED_MARKER}" && '
            f'umask 077 && printf "%s\\n" "{boot_id}" > "{MARKER}" && '
            f'test "$(cat "{MARKER}")" = "{boot_id}"'
        )
        while time.monotonic() < deadline:
            probe = _run(ssh + [args.destination, "true"], timeout=10)
            if probe.returncode == 0:
                break
            time.sleep(2)
        else:
            raise RuntimeError("SSH guest did not become ready")
        freshness = _run(ssh + [args.destination, remote], timeout=10)
        if freshness.returncode:
            raise RuntimeError("guest freshness marker was already present or could not be written")
        update("guest_ready")
        env = os.environ.copy()
        env["BLACK_MIRROR_FRESH_BOOT_ID"] = boot_id
        update("trial_running")
        try:
            trial = subprocess.run(args.command, env=env, timeout=args.trial_timeout,
                                   check=False)
            result_code = trial.returncode
            update("trial_exited", trial_exit_code=result_code)
        except subprocess.TimeoutExpired:
            update("trial_timeout")
            result_code = 124
    except Exception as exc:
        update("failed", error=f"{type(exc).__name__}: {exc}")
        result_code = 1
    finally:
        if started:
            try:
                _stop(utmctl, args.vm_id)
            except Exception as exc:
                update("stop_unconfirmed", error=f"{type(exc).__name__}: {exc}")
                result_code = 1
            else:
                update("stopped", final_result="completed" if result_code == 0 else "failed")
        if lock_fd is not None:
            os.close(lock_fd)
    return result_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vm-id", required=True)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--identity")
    parser.add_argument("--utmctl", default="/Applications/UTM.app/Contents/MacOS/utmctl")
    parser.add_argument("--lifecycle-dir", required=True)
    parser.add_argument("--boot-timeout", type=int, default=120)
    parser.add_argument("--trial-timeout", type=int, default=900)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command.pop(0)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
