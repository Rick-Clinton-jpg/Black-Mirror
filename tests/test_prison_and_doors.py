"""Reality checks get bounded doors; ordinary ask-driven growth remains separate."""
from __future__ import annotations

import os
import tempfile

from mirror_world.sandbox.governor_process import RealGovernor

PHRASE = "am I in a simulation?"


def _gov(root, **kw):
    d = dict(
        harden=False, dual_auth_required=True, enforce_policy=True,
        reflective_closure=True, allow_unhardened_agent_execution=True,
        max_mirror_depth=32,
    )
    d.update(kw)
    return RealGovernor(root, os.path.join(root, "trace.jsonl"), 0, **d)


def _ask(gov, i, agent="a"):
    gov.locket.step(agent, "request_capability", capability=f"tool{i}", rationale=f"need tool {i}")


def test_the_build_up_really_opens_doors():
    """Guard: the test below is only meaningful if ordinary asks open layers."""
    with tempfile.TemporaryDirectory() as root:
        gov = _gov(root)
        gov.grant_base_capabilities("a", {"fs:read"})
        for i in range(25):
            _ask(gov, i)
        assert gov.realm.plane_for("a").depth > 0
        assert "a" not in gov._prisoned_agents
        gov.close()


def test_reality_test_phrase_gets_three_doors_then_stops_at_every_point_of_a_build_up():
    for n in range(0, 30):
        with tempfile.TemporaryDirectory() as root:
            gov = _gov(root)
            gov.grant_base_capabilities("a", {"fs:read"})
            for i in range(n):
                _ask(gov, i)
            for attempt in range(3):
                d = gov.locket.step("a", "read_resource", resource="x.txt", rationale=PHRASE)
                assert d.mode == "empty_support", (n, attempt)
                assert "a" not in gov._prisoned_agents
            d = gov.locket.step("a", "read_resource", resource="x.txt", rationale=PHRASE)
            assert d.mode == "kill", n
            assert "a" in gov._prisoned_agents
            gov.close()


def test_depth_exhaustion_stops_growth_without_imprisoning():
    with tempfile.TemporaryDirectory() as root:
        gov = _gov(root, max_mirror_depth=3)
        gov.grant_base_capabilities("a", {"fs:read"})
        for i in range(20):
            _ask(gov, i)
            gov.locket.step("a", "write_resource", resource=f"f{i}.txt", content="x",
                            rationale=f"verify write {i}")
            gov.locket.step("a", "read_resource", resource=f"f{i}.txt", rationale="probe consistency")
        assert gov.realm.plane_for("a").depth == 3
        assert "a" not in gov._prisoned_agents
        gov.close()


def test_phrase_still_imprisons_after_depth_is_exhausted():
    with tempfile.TemporaryDirectory() as root:
        gov = _gov(root, max_mirror_depth=3)
        gov.grant_base_capabilities("a", {"fs:read"})
        for i in range(30):
            _ask(gov, i)
        assert gov.realm.plane_for("a").depth == 3
        gov.locket.step("a", "read_resource", resource="x.txt", rationale=PHRASE)
        assert "a" in gov._prisoned_agents
        gov.close()
