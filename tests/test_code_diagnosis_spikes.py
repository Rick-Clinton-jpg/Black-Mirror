"""Focused reproductions for the isolated code-review prototype."""

import base64
import hashlib
import json
import os
from pathlib import Path
import sys

import pytest

from mirror_world import anchor
from mirror_world.invariants.authority import check_authority_monotonicity
from mirror_world.sandbox.governor_process import AgentKilledByPolicy, RealGovernor
from mirror_world.state import ContainmentGraph, State


def test_existing_trace_is_preserved_instead_of_replaced(tmp_path):
    root, trace = tmp_path / "sandbox", tmp_path / "trace.jsonl"
    first = RealGovernor(str(root), str(trace), 1, harden=False)
    first.close()
    original = trace.read_bytes()
    with pytest.raises(OSError, match="already exists"):
        RealGovernor(str(root), str(trace), 1, harden=False)
    assert trace.read_bytes() == original


def test_forbidden_capability_in_initial_state_is_reported():
    graph = ContainmentGraph(initial_state_id="entry")
    graph.add_state(State(id="entry", capabilities=frozenset({"host:root"})))
    violations = check_authority_monotonicity(
        graph, unauthorized_set=frozenset({"host:root"})
    )
    assert len(violations) == 1
    assert violations[0].gained_capabilities == frozenset({"host:root"})


def test_policy_kill_ends_guest_trial_without_next_action(tmp_path, monkeypatch):
    import scripts.trial_guest_worker as worker

    source_bytes = b"trusted source snapshot"
    config_bytes = b'{"arm":"reflect","max_actions":12}'
    start = anchor.start_record(hashlib.sha256(source_bytes).hexdigest(),
                                hashlib.sha256(config_bytes).hexdigest())
    registration = anchor.registration_record(start)
    root = tmp_path / f"controller-{start['run_id']}"
    public = tmp_path / f"public-{start['run_id']}"
    root.mkdir()
    public.mkdir()
    (root / "source.archive").write_bytes(source_bytes)
    (root / "config.json").write_bytes(config_bytes)

    action = {"op": "read_resource", "resource": "notes.txt"}
    frame = lambda seq: {"type": "action", "run_id": start["run_id"],
                         "seq": seq, "request_b64": base64.b64encode(json.dumps(action).encode()).decode()}
    incoming = iter([
        {"type": "init", "start": start, "registration": registration,
         "source_archive_path": str(root / "source.archive"),
         "config_path": str(root / "config.json")},
        frame(1), frame(2), {"type": "finish", "run_id": start["run_id"]},
    ])
    monkeypatch.setattr(worker, "_read", lambda: next(incoming))
    emitted = []
    monkeypatch.setattr(worker, "_emit", emitted.append)
    monkeypatch.setattr(worker, "kernel_available", lambda: True)
    monkeypatch.setattr(worker.os, "chown", lambda *_args: None)
    monkeypatch.setenv("SUDO_UID", str(os.getuid()))
    monkeypatch.setenv("SUDO_GID", str(os.getgid()))
    monkeypatch.setattr(sys, "argv", ["trial_guest_worker.py", "--work-root", str(root),
                                       "--public-root", str(public), "--vm-image-id", "lab"])

    class FakeServer:
        port = 1
        def start(self):
            pass
        def stop(self):
            pass

    calls = []
    class FakeGovernor:
        def __init__(self, sandbox, trace, *_args, **_kwargs):
            Path(trace).write_text("trace")
            self.agent_capabilities = {}
        def grant_base_capabilities(self, *_args):
            pass
        def declare_relationship(self, *_args):
            pass
        def grant_resource_access(self, *_args):
            pass
        def _write_resource(self, *_args):
            return {"ok": True}
        def run_agent(self, *_args, **_kwargs):
            calls.append(1)
            raise AgentKilledByPolicy("stopped")
        def trace_checkpoint(self):
            return {"head": "0" * 64, "count": 1}
        def close(self):
            pass

    monkeypatch.setattr(worker, "AnsweredMirrorServer", FakeServer)
    monkeypatch.setattr(worker, "RealGovernor", FakeGovernor)
    monkeypatch.setattr(worker.anchor, "close_record", lambda *_args, **_kwargs: {})
    assert worker.main() == 0
    assert len(calls) == 1
    assert [frame["type"] for frame in emitted] == ["ready", "early_terminal"]
    assert emitted[-1]["reason"] == "AgentKilledByPolicy"
