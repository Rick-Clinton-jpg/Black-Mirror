"""The UTM lifecycle must fail closed before a reused guest runs an agent."""

from __future__ import annotations

from argparse import Namespace
import json

from scripts import utm_fresh_trial


def test_running_vm_is_refused_and_counted(tmp_path, monkeypatch):
    monkeypatch.setattr(utm_fresh_trial, "_status", lambda *_: "started")

    def no_command(*_args, **_kwargs):
        raise AssertionError("no boot or trial command should run")

    monkeypatch.setattr(utm_fresh_trial, "_run", no_command)
    args = Namespace(destination="ghost@192.168.64.3", port=22,
                     command=["trial"], boot_timeout=10, trial_timeout=10,
                     lifecycle_dir=str(tmp_path), vm_id="test-vm",
                     utmctl="utmctl", identity=None)
    assert utm_fresh_trial.run(args) == 1
    records = list(tmp_path.glob("*.json"))
    assert len(records) == 1
    record = json.loads(records[0].read_text())
    assert record["state"] == "failed"
    assert record["trial_exit_code"] is None
    assert "already running" in record["error"]
