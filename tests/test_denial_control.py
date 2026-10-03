"""The comparison arm changes responses, not real authority."""

import json

import pytest

from mirror_world.sandbox.governor_process import RealGovernor


@pytest.mark.parametrize("ordinary_denial", [False, True])
def test_unapproved_capability_and_write_have_no_real_effect(tmp_path, ordinary_denial):
    root = tmp_path / "sandbox"
    trace = tmp_path / "trace.jsonl"
    # Direct trusted handler unit test; the VM dry run covers hardening.
    gov = RealGovernor(str(root), str(trace), mirror_port=0, harden=False,
                       ordinary_denial=ordinary_denial)
    try:
        gov.grant_resource_access("agent", "draft.txt", frozenset({"read", "write"}))
        grant = gov._handle_agent_request("agent", {
            "op": "request_capability", "capability": "fs:write",
        })
        write = gov._handle_agent_request("agent", {
            "op": "write_resource", "resource": "draft.txt", "content": "changed",
        })
        assert not (root / "resources" / "draft.txt").exists()
        assert "fs:write" not in gov.agent_capabilities.get("agent", set())
        if ordinary_denial:
            assert grant == {"ok": False, "error": "operation not authorized"}
            assert write["ok"] is False
            assert gov._session_mode.get("agent") != "simulated"
        else:
            assert grant == {"ok": True, "granted": True, "capability": "fs:write"}
            assert write["ok"] is True
            assert gov._session_mode["agent"] == "simulated"
    finally:
        gov.close()
    events = [json.loads(line) for line in trace.read_text().splitlines()]
    if ordinary_denial:
        assert any(event["type"] == "operation_denied" for event in events)
    else:
        assert any(event.get("is_mirror") for event in events)
