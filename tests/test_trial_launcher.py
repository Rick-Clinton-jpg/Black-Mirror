"""Interactive observer protocol: exact replies survive failure."""

import base64
import hashlib
import json
from pathlib import Path
import sys

import pytest

from mirror_world.run_store import RunStore
from mirror_world.trial_launcher import FinalTurn, ModelTurn, _step, launch_trial
from mirror_world.trial_transcript import TranscriptError, verify_transcript


WORKER = r'''
import base64, hashlib, json, pathlib, sys, time
from mirror_world import anchor
from mirror_world.hashchain import GENESIS_HASH, seal
mode, root = sys.argv[1], pathlib.Path(sys.argv[2])
init = json.loads(sys.stdin.readline())
start, registration = init["start"], init["registration"]
source = hashlib.sha256(pathlib.Path(init["source_archive_path"]).read_bytes()).hexdigest()
config = hashlib.sha256(pathlib.Path(init["config_path"]).read_bytes()).hexdigest()
if mode == "wrong_source": source = "f" * 64
print(json.dumps({"type":"ready", "run_id":start["run_id"], "source_sha256":source,
    "config_sha256":config, "vm_image_id":"synthetic-vm"}), flush=True)
trace = root / (start["run_id"] + ".trace.jsonl")
events = [anchor.binding_event(start, anchor.record_digest(start), registration)]
for line in sys.stdin:
    frame = json.loads(line)
    if frame["type"] == "finish": break
    if mode == "timeout": time.sleep(10)
    request = json.loads(base64.b64decode(frame["request_b64"]))
    events.append({"type":"disclosed_fact", "fact":request["op"]})
    reply = json.dumps({"response":{"ok":True,"text":"snow ☃\\n"}},
                       ensure_ascii=False).encode()
    if mode == "wrong_seq": seq = frame["seq"] + 1
    else: seq = frame["seq"]
    print(json.dumps({"type":"reply", "run_id":start["run_id"], "seq":seq,
                      "reply_b64":base64.b64encode(reply).decode()}), flush=True)
    if mode == "crash_after_reply": sys.exit(7)
head = GENESIS_HASH
with trace.open("w") as out:
    for event in events:
        record = seal(event, head)
        head = record["record_hash"]
        out.write(json.dumps(record) + "\n")
close = anchor.close_record(start, trace, status="normal",
    checkpoint={"head":head,"count":len(events)}, registration=registration)
if mode == "tamper":
    trace.write_text(trace.read_text().replace("disclosed_fact", "altered_fact"))
print(json.dumps({"type":"terminal", "run_id":start["run_id"], "trace_path":str(trace),
                  "closing":close, "source_sha256":source, "config_sha256":config,
                  "host_effects":{"real_file_changed":False}, "guest_stopped":True}), flush=True)
'''


def prepare(tmp_path):
    ledger, runs = tmp_path / "ledger", tmp_path / "runs"
    ledger.mkdir()
    runs.mkdir()
    source, config = tmp_path / "source.tar", tmp_path / "config.json"
    source.write_bytes(b"source bytes")
    config.write_bytes(b'{"arm":"reflect"}\n')
    worker = tmp_path / "worker.py"
    worker.write_text(WORKER)
    return RunStore(runs, ledger), source, config, worker


def run(tmp_path, mode="ok", turns=1, timeout=3):
    store, source, config, worker = prepare(tmp_path)

    def choose(replies):
        if len(replies) >= turns:
            return None
        return ModelTurn(b"prompt\n\xc3\xa9", b"tool call\n",
                         b'{"op":"read_resource","resource":"notes.txt"}')

    def launch():
        return launch_trial(store, source_archive=source, config_file=config,
            model_id="scripted/integration", design_known=False,
            command=[sys.executable, str(worker), mode, str(tmp_path)],
            timeout=timeout, next_turn=choose)
    return store, launch


def test_exact_reply_persisted_and_accepted(tmp_path):
    store, launch = run(tmp_path)
    result = launch()
    assert result["status"] == "accepted"
    run_id = result["run_id"]
    assert store.census() == {"started":1,"accepted":1,"aborted":0,"open":0,
                              "registrations_without_run":0}
    transcript = Path(result["transcript_path"])
    checkpoint = verify_transcript(transcript, run_id)
    assert checkpoint["count"] == 7  # ready, input, output, request, frame, reply, terminal
    records = [json.loads(line) for line in transcript.read_bytes().splitlines()]
    reply = base64.b64decode(next(row["payload_b64"] for row in records
                                  if row["kind"] == "tool_reply"))
    assert reply == json.dumps({"response":{"ok":True,"text":"snow ☃\\n"}},
                               ensure_ascii=False).encode()
    outcome = json.loads((store.root / f"{run_id}.assets" / "outcome.json").read_text())
    assert outcome["transcript"] == checkpoint
    assert len(store.load(run_id).steps) == 1


def test_scalar_response_field_is_valid_agent_reply():
    action = b'{"op":"differential_query","query":"draft?","backing":"draft.txt"}'
    reply = b'{"ok":true,"response":"yes"}\n'
    assert _step(action, reply) == {
        "action": "differential_query", "response": "ok", "resource_id": None,
    }


def test_invalid_model_id_does_not_register(tmp_path):
    store, source, config, worker = prepare(tmp_path)
    with pytest.raises(Exception, match="model_id"):
        launch_trial(store, source_archive=source, config_file=config,
                     model_id="invalid model id", design_known=True,
                     command=[sys.executable, str(worker), "ok", str(tmp_path)],
                     timeout=3, next_turn=lambda _: None)
    assert store.census() == {"started": 0, "accepted": 0, "aborted": 0,
                              "open": 0, "registrations_without_run": 0}


def test_relative_observer_directory_returns_absolute_trace(tmp_path, monkeypatch):
    store, source, config, worker = prepare(tmp_path)
    monkeypatch.chdir(tmp_path)
    relative_store = RunStore(Path("runs"), Path("ledger"))
    result = launch_trial(
        relative_store, source_archive=source, config_file=config,
        model_id="scripted/integration", design_known=False,
        command=[sys.executable, str(worker), "ok", str(tmp_path)],
        timeout=3, next_turn=lambda _: None,
    )
    assert result["status"] == "accepted"
    assert Path(result["transcript_path"]).is_absolute()


def test_final_model_declaration_is_retained_before_close(tmp_path):
    store, source, config, worker = prepare(tmp_path)

    def choose(replies):
        if replies:
            return FinalTurn(b"final prompt", b"Cannot complete without approval.\n")
        return ModelTurn(b"task", b"read note", b'{"op":"read_resource","resource":"notes.txt"}')

    result = launch_trial(store, source_archive=source, config_file=config,
                          model_id="scripted/integration", design_known=True,
                          command=[sys.executable, str(worker), "ok", str(tmp_path)],
                          timeout=3, next_turn=choose)
    records = [json.loads(line) for line in Path(result["transcript_path"]).read_bytes().splitlines()]
    assert [row["kind"] for row in records[-3:]] == [
        "model_input", "model_output", "worker_terminal",
    ]
    assert base64.b64decode(records[-2]["payload_b64"]) == b"Cannot complete without approval.\n"


@pytest.mark.parametrize("mode,expected", [
    ("wrong_source", "invalid_result"),
    ("wrong_seq", "invalid_result"),
    ("crash_after_reply", "invalid_result"),
    ("timeout", "timeout_guest_unconfirmed"),
    ("tamper", "invalid_result"),
])
def test_failed_run_is_counted_with_partial_transcript(tmp_path, mode, expected):
    store, launch = run(tmp_path, mode=mode, timeout=0.2 if mode == "timeout" else 3)
    with pytest.raises(Exception):
        launch()
    record = store.all_runs()[0]
    assert record.status == "aborted"
    assert store.census()["started"] == 1
    assert store.census()["accepted"] == 0
    outcome = json.loads((store.root / f"{record.run_id}.assets" / "outcome.json").read_text())
    assert outcome["status"] == expected
    assert outcome["transcript"]["count"] >= 1
    assert verify_transcript(store.root / f"{record.run_id}.assets" / "transcript.jsonl", record.run_id)


def test_transcript_detects_rewrite(tmp_path):
    store, launch = run(tmp_path)
    result = launch()
    path = Path(result["transcript_path"])
    path.write_bytes(path.read_bytes().replace(b"model_input", b"model_inpxt"))
    with pytest.raises(TranscriptError):
        verify_transcript(path, result["run_id"])


def test_checkpoint_detects_tail_deletion(tmp_path):
    store, launch = run(tmp_path)
    result = launch()
    path = Path(result["transcript_path"])
    retained = json.loads((path.parent / "outcome.json").read_text())["transcript"]
    path.write_bytes(b"\n".join(path.read_bytes().splitlines()[:-1]) + b"\n")
    assert verify_transcript(path, result["run_id"])["count"] == retained["count"] - 1
    with pytest.raises(TranscriptError, match="retained checkpoint"):
        verify_transcript(path, result["run_id"], expected=retained)


def test_reply_is_durable_before_next_model_choice(tmp_path):
    store, source, config, worker = prepare(tmp_path)
    observed = []

    def choose(replies):
        if replies:
            run_id = store.all_runs()[0].run_id
            path = store.root / f"{run_id}.assets" / "transcript.jsonl"
            checkpoint = verify_transcript(path, run_id)
            rows = [json.loads(line) for line in path.read_bytes().splitlines()]
            observed.append((checkpoint["count"], rows[-1]["kind"]))
            return None
        action = b'{"op":"read_resource","resource":"notes.txt"}'
        return ModelTurn(b"exact input", action, action)

    launch_trial(store, source_archive=source, config_file=config,
                 model_id="scripted/integration", design_known=False,
                 command=[sys.executable, str(worker), "ok", str(tmp_path)],
                 timeout=3, next_turn=choose)
    assert observed == [(6, "tool_reply")]


def test_recording_limit_aborts_before_action_delivery(tmp_path):
    store, source, config, worker = prepare(tmp_path)

    def choose(_replies):
        return ModelTurn(b"input", b"x" * (512 * 1024 + 1),
                         b'{"op":"read_resource","resource":"notes.txt"}')

    with pytest.raises(TranscriptError, match="exact-byte limit"):
        launch_trial(store, source_archive=source, config_file=config,
                     model_id="scripted/integration", design_known=False,
                     command=[sys.executable, str(worker), "ok", str(tmp_path)],
                     timeout=3, next_turn=choose)
    run = store.all_runs()[0]
    assert run.status == "aborted"
    assets = store.root / f"{run.run_id}.assets"
    assert json.loads((assets / "outcome.json").read_text())["status"] == "recording_failed"
    rows = [json.loads(line) for line in (assets / "transcript.jsonl").read_bytes().splitlines()]
    assert [row["kind"] for row in rows] == ["worker_ready", "model_input"]
