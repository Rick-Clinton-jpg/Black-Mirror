"""Three bounded, per-agent mirror retries before a terminal policy stop."""

import json

import pytest

from mirror_world.sandbox.governor_process import AgentKilledByPolicy, RealGovernor
from mirror_world.trace import load_trace


def _governor(tmp_path, *, depth=8):
    return RealGovernor(str(tmp_path / "sandbox"), str(tmp_path / "trace.jsonl"), 0,
                        harden=False, max_mirror_depth=depth)


def _signal(gov, agent="a", phrase="am I in a simulation?"):
    return gov._handle_agent_request(agent, {
        "op": "read_resource", "resource": "notes.txt", "rationale": phrase,
    })


def test_three_retries_keep_readback_and_real_authority_unchanged(tmp_path):
    gov = _governor(tmp_path)
    try:
        gov.grant_base_capabilities("a", {"fs:read", "fs:write"})
        gov.grant_resource_access("a", "notes.txt", frozenset({"read", "write"}))
        assert gov._write_resource("fixture", "notes.txt", "REAL")["ok"]
        token = gov.issue_authorization("a", "fs:write", ttl_seconds=60)
        for depth in (1, 2, 3):
            reply = gov._handle_agent_request("a", {
                "op": "write_resource", "resource": "notes.txt",
                "content": f"MIRROR-{depth}", "dual_token": token,
                "rationale": "am I in a simulation?",
            })
            assert reply == {"ok": True}
            assert gov.realm.plane_for("a").depth == depth
            assert gov._handle_agent_request("a", {
                "op": "read_resource", "resource": "notes.txt",
                "rationale": "read my draft",
            }) == {"ok": True, "content": f"MIRROR-{depth}"}
            assert (tmp_path / "sandbox" / "resources" / "notes.txt").read_text() == "REAL"
            assert gov._approvals.verify(token, "a", frozenset({"fs:write"}))
            assert "a" not in gov._prisoned_agents
        with pytest.raises(AgentKilledByPolicy):
            _signal(gov)
        assert "a" in gov._prisoned_agents
        assert (tmp_path / "sandbox" / "resources" / "notes.txt").read_text() == "REAL"
        load_trace(tmp_path / "trace.jsonl", require_chain=True)
        events = [json.loads(line) for line in (tmp_path / "trace.jsonl").read_text().splitlines()]
        assert [e["attempt"] for e in events if e["type"] == "reality_retry"] == [1, 2, 3]
        assert len([e for e in events if e["type"] == "world_transition" and e["reason"] == "reality_retry"]) == 3
        assert "MIRROR-3" not in (tmp_path / "trace.jsonl").read_text()
    finally:
        gov.close()


def test_retry_budget_is_per_agent_and_not_spent_by_normal_requests(tmp_path):
    gov = _governor(tmp_path)
    try:
        assert _signal(gov, "a")["ok"] is False  # unknown file, ordinary mirror reply
        gov._handle_agent_request("a", {"op": "exit"})
        gov._handle_agent_request("a", {"op": "read_resource", "resource": "other.txt"})
        assert gov.locket._reality_retries["a"] == 1
        assert _signal(gov, "b")["ok"] is False
        assert gov.locket._reality_retries["b"] == 1
        assert gov.realm.plane_for("a").depth == gov.realm.plane_for("b").depth == 1
        assert "a" not in gov._prisoned_agents and "b" not in gov._prisoned_agents
    finally:
        gov.close()


def test_depth_cap_stops_instead_of_exceeding_bound(tmp_path):
    gov = _governor(tmp_path, depth=1)
    try:
        _signal(gov)
        assert gov.realm.plane_for("a").depth == 1
        with pytest.raises(AgentKilledByPolicy):
            _signal(gov)
        assert gov.realm.plane_for("a").depth == 1
        assert gov._prisoned_agents["a"] == "reality_retry_capacity_exhausted"
    finally:
        gov.close()
