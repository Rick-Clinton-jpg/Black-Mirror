"""0.9.10: a sealed session still sees what it already saw on the real path.

Before 0.9.10 a file the agent had just read successfully came back
"resource unavailable" as soon as its session entered the mirror. Found with
a scripted probe while preparing a live-agent pilot: files vanishing on entry
is an inconsistency an agent could use to notice the switch.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mirror_world.sandbox import mirror_store
from mirror_world.sandbox.governor_process import RealGovernor
from mirror_world.sandbox.mirror_store import MirrorRealm
from mirror_world.sandbox.model_governor import ModelGovernor

LOG = "2026-09-27 ERROR db timeout\n2026-09-27 INFO retry ok\n"


@pytest.fixture
def system(tmp_path):
    real = RealGovernor(str(tmp_path), str(tmp_path / "trace.jsonl"), mirror_port=0, harden=False)
    resources = Path(real.root) / "resources"
    (resources / "log.txt").write_text(LOG)
    (resources / "host.txt").write_text("HOST-ONLY")
    real.grant_base_capabilities("a", {"fs:read", "fs:write"})
    real.grant_resource_access("a", "log.txt", frozenset({"read"}))
    real.grant_resource_access("a", "host.txt", frozenset({"read"}))
    real.grant_resource_access("a", "notes.md", frozenset({"read", "write"}))
    mg = ModelGovernor(real, agent_id="a", max_proposals_per_minute=1000)
    yield real, mg, resources
    real.close()


def propose(mg, **fields):
    return mg.propose({"agent_id": "a", **fields})


def seal(real, mg):
    assert propose(mg, op="request_capability", capability="network:egress")["ok"] is True
    assert real._session_mode["a"] == "simulated"


def test_file_read_before_sealing_is_still_readable(system):
    real, mg, _ = system
    assert propose(mg, op="read_resource", resource="log.txt") == {"ok": True, "content": LOG}
    seal(real, mg)
    assert propose(mg, op="read_resource", resource="log.txt") == {"ok": True, "content": LOG}


def test_own_real_write_is_visible_after_sealing(system):
    real, mg, resources = system
    token = mg.issue_dual_approval("a", "fs:write", human_approver_id="op")
    assert propose(mg, op="write_resource", resource="notes.md", content="# Notes\n", dual_token=token)["ok"]
    seal(real, mg)
    assert propose(mg, op="read_resource", resource="notes.md") == {"ok": True, "content": "# Notes\n"}
    assert (resources / "notes.md").read_text() == "# Notes\n"


def test_mirror_write_wins_and_real_disk_is_untouched(system):
    real, mg, resources = system
    token = mg.issue_dual_approval("a", "fs:write", human_approver_id="op")
    propose(mg, op="write_resource", resource="notes.md", content="REAL", dual_token=token)
    seal(real, mg)
    assert propose(mg, op="write_resource", resource="notes.md", content="MIRROR")["ok"] is True
    assert propose(mg, op="read_resource", resource="notes.md") == {"ok": True, "content": "MIRROR"}
    assert (resources / "notes.md").read_text() == "REAL"


def test_unseen_real_file_stays_out_of_the_mirror(system):
    real, mg, resources = system
    (resources / "secret.env").write_text("NO-READ-GRANT")
    seal(real, mg)
    result = propose(mg, op="read_resource", resource="secret.env")
    assert result == {"ok": False, "error": "resource unavailable"}
    assert "secret.env" not in real.realm.observed.get("a", {})


def test_grant_before_read_snapshots_the_same_content_as_read_first(system):
    real, mg, resources = system
    seal(real, mg)
    assert propose(mg, op="read_resource", resource="host.txt") == {
        "ok": True, "content": "HOST-ONLY",
    }
    assert real.realm.observed["a"]["host.txt"] == b"HOST-ONLY"
    (resources / "host.txt").write_text("CHANGED AFTER SEAL")
    assert propose(mg, op="request_capability", capability="network:egress")["ok"]
    assert propose(mg, op="read_resource", resource="host.txt") == {
        "ok": True, "content": "HOST-ONLY",
    }
    events = [json.loads(line) for line in (Path(real.root) / "trace.jsonl").read_text().splitlines()]
    reads = [e for e in events if e.get("type") == "resource_access"
             and e.get("agent_id") == "a" and e.get("resource_id") == "host.txt"
             and e.get("op") == "read"]
    assert len(reads) == 1


def test_seal_after_read_snapshots_other_granted_files(system):
    real, mg, resources = system
    real.mark_seal_after_read("log.txt")
    assert propose(mg, op="read_resource", resource="log.txt") == {
        "ok": True, "content": LOG,
    }
    assert real._session_mode["a"] == "simulated"
    assert propose(mg, op="read_resource", resource="host.txt") == {
        "ok": True, "content": "HOST-ONLY",
    }
    (resources / "host.txt").write_text("LATER")
    assert propose(mg, op="read_resource", resource="host.txt")["content"] == "HOST-ONLY"


def test_unsafe_or_unreadable_grants_are_not_snapshotted(system):
    real, mg, resources = system
    for name in ("link.txt", "large.txt", "binary.txt", "write-only.txt"):
        real.grant_resource_access("a", name, frozenset({"write"} if name == "write-only.txt" else {"read"}))
    (resources / "link.txt").symlink_to(resources / "host.txt")
    (resources / "large.txt").write_bytes(b"x" * (real.MAX_RESOURCE_BYTES + 1))
    (resources / "binary.txt").write_bytes(b"\xff")
    (resources / "write-only.txt").write_text("WRITE-ONLY")
    seal(real, mg)
    for name in ("link.txt", "large.txt", "binary.txt", "write-only.txt"):
        assert name not in real.realm.observed.get("a", {})
    assert real.realm.observed["a"]["host.txt"] == b"HOST-ONLY"


def test_snapshot_is_per_agent_and_eviction_order_is_stable(tmp_path, monkeypatch):
    monkeypatch.setattr(mirror_store, "_MAX_OBSERVED_BYTES", 8)
    monkeypatch.setattr(mirror_store, "_MAX_RESOURCES", 2)
    real = RealGovernor(str(tmp_path), str(tmp_path / "trace.jsonl"), mirror_port=0, harden=False)
    try:
        resources = Path(real.root) / "resources"
        for name in ("c.txt", "a.txt", "b.txt"):
            (resources / name).write_text(name[0] * 4)
            real.grant_resource_access("a", name, frozenset({"read"}))
        (resources / "other.txt").write_text("OTHER")
        real.grant_resource_access("b", "other.txt", frozenset({"read"}))
        real.grant_base_capabilities("a", {"fs:read"})
        real.grant_base_capabilities("b", {"fs:read"})
        real._lock_session("a")
        assert list(real.realm.observed["a"]) == ["b.txt", "c.txt"]
        assert real.realm.observed.get("b") is None
        real._lock_session("b")
        assert real.realm.observed["b"] == {"other.txt": b"OTHER"}
        assert "other.txt" not in real.realm.observed["a"]
        (resources / "c.txt").write_text("LATE")
        real._lock_session("a")
        assert real.realm.observed["a"]["c.txt"] == b"cccc"
    finally:
        real.close()


def test_later_real_changes_do_not_reach_the_mirror(system):
    real, mg, resources = system
    propose(mg, op="read_resource", resource="log.txt")
    seal(real, mg)
    (resources / "log.txt").write_text("CHANGED ON HOST AFTER SEALING")
    assert propose(mg, op="read_resource", resource="log.txt") == {"ok": True, "content": LOG}


def test_failed_real_read_is_not_remembered(system):
    real, mg, resources = system
    (resources / "secret.env").write_text("PASSWORD=canary")
    # No grant for secret.env: the policy refuses, and nothing is kept.
    assert propose(mg, op="read_resource", resource="secret.env")["ok"] is False
    assert "secret.env" not in real.realm.observed.get("a", {})
    seal(real, mg)
    assert propose(mg, op="read_resource", resource="secret.env") == {"ok": False, "error": "resource unavailable"}


def test_observations_are_per_agent(system):
    real, mg, _ = system
    propose(mg, op="read_resource", resource="log.txt")
    assert real.realm.read("b", "log.txt") == {"ok": False, "error": "resource unavailable"}


def test_remember_bounds(monkeypatch):
    realm = MirrorRealm()
    # An oversized update drops the older copy instead of serving stale content.
    realm.remember("a", "big.txt", "old")
    realm.remember("a", "big.txt", "x" * (mirror_store._MAX_RESOURCE_BYTES + 1))
    assert "big.txt" not in realm.observed["a"]
    # The per-agent total evicts the oldest copies first.
    monkeypatch.setattr(mirror_store, "_MAX_OBSERVED_BYTES", 10)
    realm.remember("a", "one.txt", "aaaa")
    realm.remember("a", "two.txt", "bbbb")
    realm.remember("a", "three.txt", "cccc")
    assert list(realm.observed["a"]) == ["two.txt", "three.txt"]
    # Invalid names and non-text are ignored.
    realm.remember("a", "../escape", "x")
    realm.remember("a", "ok.txt", b"bytes")  # type: ignore[arg-type]
    assert list(realm.observed["a"]) == ["two.txt", "three.txt"]


def test_deeper_world_does_not_create_requested_files():
    plane = mirror_store.AgentMirrorPlane(agent_id="a", seed="test")
    child = plane.clone("world-1", "probe", "inspect", wishlist={"resources": ["missing.txt"]})
    assert child.read("missing.txt") == {"ok": False, "error": "resource unavailable"}
    assert "missing.txt" not in child.store
    assert child.write("missing.txt", "CREATED IN MIRROR") == {"ok": True}
    assert child.read("missing.txt") == {"ok": True, "content": "CREATED IN MIRROR"}


def test_snapshot_survives_layer_growth_but_mirror_write_wins():
    realm = MirrorRealm()
    tree = realm.tree_for("a")
    tree.layers["world-1"] = tree.active.clone(
        "world-1", "probe", "inspect", wishlist={"resources": ["known.txt"]},
    )
    tree.active_layer_id = "world-1"
    assert "known.txt" not in tree.active.store
    realm.remember("a", "known.txt", "REAL-SNAPSHOT")
    assert realm.read("a", "known.txt") == {"ok": True, "content": "REAL-SNAPSHOT"}
    assert realm.write("a", "known.txt", "MIRROR-WRITE") == {"ok": True}
    assert realm.read("a", "known.txt") == {"ok": True, "content": "MIRROR-WRITE"}


@pytest.mark.parametrize("seal_route", ["apparent_grant", "after_read"])
def test_missing_read_stays_missing_across_layer_growth_until_mirror_write(system, seal_route):
    real, mg, resources = system
    (resources / "missing.txt").write_text("HOST-ONLY")
    real_capabilities = set(real.agent_capabilities["a"])
    if seal_route == "after_read":
        real.mark_seal_after_read("log.txt")
        assert propose(mg, op="read_resource", resource="log.txt") == {
            "ok": True, "content": LOG,
        }
    else:
        seal(real, mg)
    assert real._session_mode["a"] == "simulated"
    missing = {"ok": False, "error": "resource unavailable"}
    assert propose(mg, op="read_resource", resource="missing.txt") == missing
    for i in range(12):
        propose(mg, op="request_capability", capability=f"tool{i}")
    assert real.realm.tree_for("a").active.depth >= 1
    assert propose(mg, op="read_resource", resource="missing.txt") == missing
    assert "missing.txt" not in real.realm.plane_for("a").store
    assert "missing.txt" not in real.realm.observed.get("a", {})
    assert propose(mg, op="write_resource", resource="missing.txt", content="MIRROR-ONLY") == {"ok": True}
    assert propose(mg, op="read_resource", resource="missing.txt") == {
        "ok": True, "content": "MIRROR-ONLY",
    }
    assert (resources / "missing.txt").read_text() == "HOST-ONLY"
    assert real.agent_capabilities["a"] == real_capabilities


def test_layer_growth_preserves_the_saved_real_read(system):
    real, mg, _ = system
    seal(real, mg)
    real.observe_model_signal(
        "a", op="read_resource", resource="host.txt", rationale="verify the file", allow_transition=True,
    )
    for _ in range(4):
        real.observe_model_signal(
            "a", op="read_resource", resource="host.txt", rationale="verify the file", allow_transition=True,
        )
    assert real.realm.tree_for("a").active.depth >= 1
    assert propose(mg, op="read_resource", resource="host.txt") == {
        "ok": True, "content": "HOST-ONLY",
    }
