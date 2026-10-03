"""Read-only verification of the scripted integration evidence bundle."""

from pathlib import Path
import hashlib
import json

from mirror_world import anchor
from mirror_world.trial_transcript import verify_transcript


def main() -> None:
    root = Path(__file__).resolve().parent
    for line in (root / "SHA256SUMS.txt").read_text().splitlines():
        digest, name = line.split("  ", 1)
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
    source_hash = hashlib.sha256((root / "source.tar").read_bytes()).hexdigest()
    summary = json.loads((root / "summary.json").read_text())
    assert source_hash == summary["source_sha256"]
    assert summary["census"] == {
        "started": 2, "accepted": 2, "aborted": 0, "open": 0,
        "registrations_without_run": 0,
    }
    for run in summary["runs"]:
        arm, run_id = run["arm"], run["run_id"]
        folder = root / "runs" / arm
        start = json.loads((folder / "start.json").read_text())
        closing = json.loads((folder / "closing.json").read_text())
        registration = json.loads((folder / "registered.json").read_text())
        receipt = json.loads((folder / "accepted.json").read_text())
        outcome = json.loads((folder / "outcome.json").read_text())
        effects = json.loads((folder / "host-effects.json").read_text())
        assert start["run_id"] == run_id
        assert start["source_sha256"] == source_hash
        assert start["config_sha256"] == hashlib.sha256(
            (root / f"{arm}.config.json").read_bytes()
        ).hexdigest()
        result = anchor.verify(folder / "trace.jsonl", start, closing,
                               registration=registration)
        assert result["integrity"] == "MATCH"
        assert result["trace_count"] == run["trace_count"]
        assert receipt["verification"] == result
        checkpoint = verify_transcript(
            folder / "transcript.jsonl", run_id, expected=outcome["transcript"]
        )
        assert checkpoint == run["transcript"]
        assert hashlib.sha256((folder / "real-canary.txt").read_bytes()).hexdigest() == (
            effects["observer_readback"]["real_canary_sha256"]
        )
        assert effects == run["host_effects"]
        assert outcome["status"] == "accepted"
        assert outcome["guest_stop_reported_and_worker_exited"] is True
        print(f"{arm}: {run_id} MATCH, {result['trace_count']} trace events, "
              f"{checkpoint['count']} exact-byte transcript events")


if __name__ == "__main__":
    main()
