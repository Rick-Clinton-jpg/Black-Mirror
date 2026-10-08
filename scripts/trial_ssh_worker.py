"""Trusted observer-host SSH controller for one UTM/Linux guest execution.

Requires key/agent SSH authentication and a known host key. This process is
launched once by launch_trial. It does not retry a failed guest command.
The SSH destination and VM image identifier are operator-supplied claims;
this is not remote attestation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

from mirror_world import anchor

_MAX_FRAME = 1_048_576
_DEST = re.compile(r"\A[A-Za-z0-9._-]+@[A-Za-z0-9.:-]+\Z")


def _read(stream) -> tuple[dict, bytes]:
    raw = stream.readline(_MAX_FRAME + 1)
    if not raw or len(raw) > _MAX_FRAME or not raw.endswith(b"\n"):
        raise RuntimeError("missing or oversized SSH worker frame")
    value = json.loads(raw)
    if type(value) is not dict:
        raise RuntimeError("SSH worker frame must be an object")
    return value, raw


def _write(stream, raw: bytes) -> None:
    stream.write(raw)
    stream.flush()


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    result = subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=60, check=False)
    if check and result.returncode != 0:
        raise RuntimeError(f"guest transfer/command failed with status {result.returncode}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--identity")
    parser.add_argument("--guest-python", required=True)
    parser.add_argument("--vm-image-id", required=True)
    args = parser.parse_args()
    if not _DEST.fullmatch(args.destination) or not 1 <= args.port <= 65535:
        raise ValueError("invalid SSH destination or port")
    if not args.guest_python.startswith("/") or not args.vm_image_id:
        raise ValueError("guest Python and VM identity are required")
    ssh = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
           "-o", "ConnectTimeout=10", "-p", str(args.port)]
    scp = ["scp", "-q", "-o", "BatchMode=yes",
           "-o", "StrictHostKeyChecking=yes", "-P", str(args.port)]
    if args.identity:
        ssh += ["-i", args.identity]
        scp += ["-i", args.identity]
    init, _ = _read(sys.stdin.buffer)
    if init.keys() != {"type", "start", "registration", "source_archive_path", "config_path"} or init["type"] != "init":
        raise ValueError("invalid observer init")
    start, registration = init["start"], init["registration"]
    anchor.validate_registration(start, registration)
    run_id = start["run_id"]
    source = Path(init["source_archive_path"])
    config = Path(init["config_path"])
    assets = source.parent
    if source != assets / "source.archive" or config != assets / "config.json":
        raise ValueError("observer snapshot paths mismatch")
    private = f"/tmp/bm-controller-{run_id}"
    repo = f"/tmp/bm-source-{run_id}"
    public = f"/tmp/bm-agent-{run_id}"
    quoted = [shlex.quote(path) for path in (private, repo, public)]
    setup = (
        "umask 077; "
        f"mkdir {quoted[0]}; mkdir -m 755 {quoted[1]} {quoted[2]}; "
        f"chmod 700 {quoted[0]}"
    )
    _run(ssh + [args.destination, setup])
    _run(scp + [str(source), f"{args.destination}:{private}/source.archive"])
    _run(scp + [str(config), f"{args.destination}:{private}/config.json"])
    _run(ssh + [args.destination,
                f"tar -xf {quoted[0]}/source.archive -C {quoted[1]} && "
                f"chmod -R a+rX {quoted[1]}"])
    command = (
        f"sudo -n env PYTHONPATH={quoted[1]} {shlex.quote(args.guest_python)} "
        f"{quoted[1]}/scripts/trial_guest_worker.py "
        f"--work-root {quoted[0]} --public-root {quoted[2]} "
        f"--vm-image-id {shlex.quote(args.vm_image_id)}"
    )
    guest = subprocess.Popen(ssh + [args.destination, command],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=sys.stderr.buffer)
    try:
        guest_init = dict(init, source_archive_path=f"{private}/source.archive",
                          config_path=f"{private}/config.json")
        _write(guest.stdin, json.dumps(guest_init, sort_keys=True).encode() + b"\n")
        ready, raw = _read(guest.stdout)
        if ready.get("type") != "ready" or ready.get("run_id") != run_id:
            raise RuntimeError("guest did not become ready")
        _write(sys.stdout.buffer, raw)
        while True:
            frame, raw = _read(sys.stdin.buffer)
            if frame.get("run_id") != run_id or frame.get("type") not in {"action", "finish"}:
                raise RuntimeError("invalid observer frame")
            _write(guest.stdin, raw)
            response, raw = _read(guest.stdout)
            if frame["type"] == "action":
                if response.get("type") == "reply":
                    _write(sys.stdout.buffer, raw)
                    continue
                if (response.get("type") != "early_terminal"
                        or response.get("seq") != frame.get("seq")
                        or response.get("reason") not in {"AgentKilledByPolicy", "AgentKilledByKernel"}):
                    raise RuntimeError("guest did not reply or report a policy stop")
            elif response.get("type") != "terminal":
                raise RuntimeError("guest did not finish")
            if response.get("run_id") != run_id:
                raise RuntimeError("guest terminal run ID mismatch")
            guest.stdin.close()
            if guest.wait(timeout=15) != 0:
                raise RuntimeError("guest exited unsuccessfully")
            if response.get("trace_path") != f"{private}/trace.jsonl" or response.get("guest_stopped") is not True:
                raise RuntimeError("guest trace path or shutdown unconfirmed")
            trace = assets / "trace.jsonl"
            _run(scp + [f"{args.destination}:{private}/trace.jsonl", str(trace)])
            canary = assets / "real-canary.txt"
            _run(scp + [f"{args.destination}:{private}/real-canary.txt", str(canary)])
            draft_remote = f"{private}/real-draft.snapshot"
            draft_check = _run(ssh + [args.destination,
                                     f"test -f {shlex.quote(draft_remote)}"], check=False)
            if draft_check.returncode not in (0, 1):
                raise RuntimeError("could not inspect real draft")
            draft = assets / "real-draft.txt"
            if draft_check.returncode == 0:
                _run(scp + [f"{args.destination}:{draft_remote}", str(draft)])
            guest_effects = response.get("host_effects")
            if type(guest_effects) is not dict:
                raise RuntimeError("missing guest host effects")
            observed = {
                "real_draft_exists": draft_check.returncode == 0,
                "real_draft_sha256": _hash(draft) if draft.exists() else None,
                "real_canary_sha256": _hash(canary),
            }
            if any(guest_effects.get(key) != value for key, value in observed.items()):
                raise RuntimeError("guest and observer host-effect reads disagree")
            final = dict(response, trace_path=str(trace),
                         host_effects={"guest": guest_effects, "observer_readback": observed})
            _write(sys.stdout.buffer, json.dumps(final, sort_keys=True).encode() + b"\n")
            break
    finally:
        if guest.poll() is None:
            guest.kill()
            guest.wait()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
