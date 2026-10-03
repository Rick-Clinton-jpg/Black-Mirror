"""One observer registration per actual worker process, including failures."""

import json
import sys

import pytest

from mirror_world.run_launcher import LaunchError, launch_once
from mirror_world.run_store import RunStore


WORKER = '''
import hashlib, json, pathlib, sys, time
from mirror_world import anchor
from mirror_world.hashchain import GENESIS_HASH, seal
request = json.loads(sys.stdin.readline())
mode = sys.argv[1]
if mode == "crash":
    sys.exit(7)
if mode == "timeout":
    time.sleep(10)
start, registration = request["start"], request["registration"]
trace = pathlib.Path(sys.argv[2]) / (start["run_id"] + ".trace.jsonl")
events = [anchor.binding_event(start, anchor.record_digest(start), registration),
          {"type": "disclosed_fact", "fact": "synthetic worker"}]
head = GENESIS_HASH
with trace.open("w") as out:
    for event in events:
        record = seal(event, head)
        head = record["record_hash"]
        out.write(json.dumps(record) + "\\n")
close = anchor.close_record(start, trace, status="normal",
    checkpoint={"head": head, "count": len(events)}, registration=registration)
source_hash = hashlib.sha256(pathlib.Path(request["source_archive_path"]).read_bytes()).hexdigest()
config_hash = hashlib.sha256(pathlib.Path(request["config_path"]).read_bytes()).hexdigest()
if mode == "wrong_source":
    source_hash = "f" * 64
print(json.dumps({"trace_path": str(trace), "closing": close,
  "steps": [{"action": "read_resource", "response": "ok", "resource_id": "notes"}],
  "executed_source_sha256": source_hash, "executed_config_sha256": config_hash}))
'''


def setup(tmp_path):
    ledger, runs = tmp_path / "ledger", tmp_path / "runs"
    ledger.mkdir()
    runs.mkdir()
    source, config = tmp_path / "source.zip", tmp_path / "config.json"
    source.write_bytes(b"exact source")
    config.write_text('{"arm":"reflect"}')
    script = tmp_path / "worker.py"
    script.write_text(WORKER)
    return RunStore(runs, ledger), source, config, script


def run(store, source, config, script, tmp_path, mode, timeout=3):
    return launch_once(store, source_archive=source, config_file=config,
        model_id="openrouter/example-model:free", design_known=False,
        command=[sys.executable, str(script), mode, str(tmp_path)], timeout=timeout)


def test_one_process_accepted_and_source_snapshot_retained(tmp_path):
    store, source, config, script = setup(tmp_path)
    result = run(store, source, config, script, tmp_path, "ok")
    run_id = result["run_id"]
    assert result["status"] == "accepted"
    assert store.census() == {"started": 1, "accepted": 1, "aborted": 0,
                              "open": 0, "registrations_without_run": 0}
    assets = store.root / f"{run_id}.assets"
    assert (assets / "source.archive").read_bytes() == source.read_bytes()
    assert json.loads((assets / "outcome.json").read_text())["status"] == "accepted"
    assert len(store.load(run_id).steps) == 1
    assert store.load(run_id).model_id == "openrouter/example-model:free"


@pytest.mark.parametrize("mode,expected", [
    ("crash", "crash"), ("timeout", "timeout"),
    ("wrong_source", "invalid_result"),
])
def test_every_failed_launch_is_counted(tmp_path, mode, expected):
    store, source, config, script = setup(tmp_path)
    with pytest.raises(LaunchError):
        run(store, source, config, script, tmp_path, mode,
            timeout=0.1 if mode == "timeout" else 3)
    assert store.census() == {"started": 1, "accepted": 0, "aborted": 1,
                              "open": 0, "registrations_without_run": 0}
    run_id = store.all_runs()[0].run_id
    assert json.loads((store.root / f"{run_id}.assets" / "outcome.json").read_text())["status"] == expected
    assert not (store.ledger / f"{run_id}.accepted.json").exists()
