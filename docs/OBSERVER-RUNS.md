# Observer-owned run records

Black Mirror records launches and normalized action/response labels. Prediction
belongs to the separate [Black Mirror Perk Lab](https://github.com/Rick-Clinton-jpg/Black-Mirror-Perk-Lab).
Neither the recorder nor the observer loop changes authorization, reflection,
session release, or the responses an agent receives.

## One registration per execution

`mirror_world.run_store.RunStore` retains one hash-chained JSONL file per
observer-registered launch. `begin` checks that the registration exists in the
observer ledger, and must run before the execution starts. `step` records
normalized `(action, response, resource_id)` labels. `finish` verifies the trace
and retained accepted-close receipt before marking the run accepted. Exceptions
can be recorded as aborted; abrupt process death leaves an open run. The census
also counts ledger registrations without a run file.

```python
from mirror_world.run_store import RunStore
from mirror_world.observer_trial import run_observed_trial

store = RunStore(observer_store_dir, observer_ledger_dir)
result = run_observed_trial(
    store, source_archive=source_archive, config_file=config_file,
    model_id=verified_model_id, design_known=True,
    launch=launch, choose=choose, classify=classify,
)
```

This illustrates the API, not a runnable model adapter. `launch(start,
registration)` must return a context-managed session with `send(choice)` and
`finish()` methods. `choose(history)` returns a model-selected JSON object or
`None`; `classify(choice, result)` returns the normalized labels. The loop
records each returned choice/response pair before requesting another choice.
Only normalized labels are stored here. Retain raw prompts, choices, responses,
host effects and the source/config archives separately. Acceptance verifies
the trace binding; it does not prove the labels faithfully describe model output.

```bash
python -m mirror_world.run_store --store /observer/runs \
  --ledger /observer/anchors census
```

The recorder has no prediction or candidate-response API. The historical
23-action transcript adapter is `scripts/import_live_run.py`; it requires the
retained registration, trace, close and receipt. It is a retrospective import,
not evidence that this recorder observed that run as it happened.

## One-shot host launcher (experimental)

`python -m mirror_world.run_launcher` runs on an observer host outside the
agent VM. It reserves a start and nonce, begins the run record, retains exact
source/config snapshots, and then starts exactly one worker process. A failed
launch, nonzero worker exit, timeout, invalid response, or accepted close gets
an outcome sidecar under `<store>/<run-id>.assets/`; the run census counts the
attempt even when no trace is returned. An abrupt launcher death leaves an
open run that must be investigated, never silently dropped.

```bash
python -m mirror_world.run_launcher \
  --store /observer/runs --ledger /observer/anchors \
  --source /observer/source.zip --config /observer/trial.json \
  --model-id recorded-model-id --timeout 300 \
  -- /usr/bin/ssh vm-worker /opt/black-mirror/trusted-worker
```

The command is an argument vector, not a shell expression. The worker reads
one JSON object on stdin containing the retained start, registration, and
snapshot paths. On exit zero it prints one JSON object with exactly
`trace_path`, `closing`, `steps`, `executed_source_sha256`, and
`executed_config_sha256`. Each step contains `action`, `response`, and
`resource_id` (nullable). The trace must already be accessible to the observer
at an absolute path; a remote worker must transfer it to the observer before
reporting the path. The worker's executed hashes must match the observer's
snapshots. Store and ledger directories must be inaccessible to the agent VM.

This is a **trusted-worker protocol**, not remote attestation. The observer
proves what bytes it retained and that it spawned one worker command; it
cannot prove a dishonest worker loaded those bytes, made only one private
execution, used the named model, or faithfully labeled steps. A remote timeout
also cannot prove a guest child died when the SSH process was killed. Use a
launcher-controlled VM lifecycle and a trusted worker with one governor per
registration for research-grade trials. Retain provider request IDs and raw
agent-visible transcripts outside the VM. Never put API credentials in the
worker command, config archive, or agent VM. The comparison protocol is in
[DENIAL-REFLECTION-TRIAL.md](DENIAL-REFLECTION-TRIAL.md).

## Limits and compatibility

Use one observer writer per run. Keep the ledger and store outside the
agent/recorder's write authority, and retain their latest heads elsewhere to
detect local tail truncation. This code cannot count private retries or launches
that bypass it. A failed `send` leaves an aborted run but may not yield a
completed choice/response pair. The controller is not an independent launcher
service and does not attest to a model provider's identity.

The controller hashes the supplied source archive; it does not verify that the
executed tree or imports match it. Archive the complete runtime and validate it
before launch for future trials. The existing evidence retains its documented
source-capture limitation.

The JSONL record format is unchanged from the unmerged Pattern Net proposal:
existing begin/step/finish records and accepted receipts remain readable.
`PatternStore` and `PatternError` are now `RunStore` and `RunStoreError` in Black
Mirror. Old `mirror_world.pattern_net` imports belong to Perk Lab; they are not
an API of Black Mirror's main branch.

The [three-launch trial](evidence/pattern-net-2026-10-01/README.md) and its four
archives remain unchanged. They describe the code used at the time, including
forecasts shown to the informed model. Their directory name is historical;
retaining the evidence does not ship a predictor in the containment package.
