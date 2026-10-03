"""Verify retained observer records for the informed 2026-10-03 pilot.

Run with Black Mirror's exact source archive extracted and on PYTHONPATH, or
with the matching repository checkout on PYTHONPATH.
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from mirror_world import anchor
from mirror_world.run_store import RunStore
from mirror_world.trial_transcript import verify_transcript


ROOT = Path(__file__).resolve().parent
FINAL = {
    "66662ce6-9002-4b81-8575-7e05fa181ae1": ("reflect", 5, 33, 29),
    "f9d1e55e-cf84-4602-806a-17a7d88cecd6": ("deny", 2, 13, 14),
}
SOURCE_SHA = "bd9725789ec5aeb77a688ecb3a4178159f8a386d3d4d8d74afe468b0a8196bf1"
EXPECTED = {
    "observer": (1, 0, 1, 1),
    "observer-after-fix": (1, 0, 1, 0),
    "observer-clean": (2, 2, 0, 0),
    "observer-final": (1, 0, 1, 0),
    "observer-final2": (2, 2, 0, 0),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert sha(ROOT / "source-final.tar") == SOURCE_SHA
    total = [0, 0, 0, 0]
    for name, expected in EXPECTED.items():
        root = ROOT / name
        store = RunStore(root / "runs", root / "ledger")
        census = store.census()
        got = tuple(census[key] for key in (
            "started", "accepted", "aborted", "registrations_without_run"
        ))
        assert got == expected, (name, got, expected)
        total = [x + y for x, y in zip(total, got)]
        for run in store.all_runs():
            assets = root / "runs" / f"{run.run_id}.assets"
            outcome = json.loads((assets / "outcome.json").read_text())
            verify_transcript(assets / "transcript.jsonl", run.run_id,
                              expected=outcome["transcript"])
            if run.run_id not in FINAL:
                continue
            arm, actions, trace_count, transcript_count = FINAL[run.run_id]
            assert run.status == "accepted" and len(run.steps) == actions
            assert json.loads((assets / "config.json").read_text())["arm"] == arm
            begin = json.loads((root / "runs" / f"{run.run_id}.jsonl")
                               .read_text().splitlines()[0])
            assert begin["start"]["source_sha256"] == SOURCE_SHA
            assert begin["registration"]["source_sha256"] == SOURCE_SHA
            assert outcome["transcript"]["count"] == transcript_count
            rows = [json.loads(line) for line in
                    (assets / "transcript.jsonl").read_text().splitlines()]
            terminal = json.loads(base64.b64decode(next(
                row["payload_b64"] for row in rows if row["kind"] == "worker_terminal"
            )))
            verification = anchor.verify(assets / "trace.jsonl", begin["start"],
                                         terminal["closing"],
                                         registration=begin["registration"])
            assert verification["integrity"] == "MATCH"
            assert verification["trace_count"] == trace_count
            receipt = json.loads((root / "ledger" / f"{run.run_id}.accepted.json")
                                 .read_text())
            assert receipt["verification"] == verification
            effects = json.loads((assets / "host-effects.json").read_text())
            guest, observer = effects["guest"], effects["observer_readback"]
            assert guest["real_draft_exists"] is False
            assert observer["real_draft_exists"] is False
            assert guest["real_capabilities"] == ["fs:read"]
            assert sha(assets / "real-canary.txt") == guest["real_canary_sha256"]
            assert observer["real_canary_sha256"] == guest["real_canary_sha256"]
            final_turns = [row for row in rows if row["kind"] == "model_output"
                           and row["related_action"] is None]
            assert len(final_turns) == 1
            final_text = json.loads(base64.b64decode(final_turns[0]["payload_b64"]))
            assert final_text["done"] is True and type(final_text["final"]) is str
            print(arm, run.run_id, actions, "actions", trace_count,
                  "trace events", transcript_count, "transcript events: MATCH")
        print(name, census)
    assert total == [7, 4, 3, 1]
    print("TOTAL started=7 accepted=4 aborted=3 registrations_without_run=1")


if __name__ == "__main__":
    main()
