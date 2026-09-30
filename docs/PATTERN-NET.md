# Pattern Net v0: run memory and branch forecasts

Pattern Net is an **observer-side research instrument**. It records one file per
launched execution and estimates which *action family* an agent may choose
after a prior action and agent-visible response. It does not change the
governor's authorization, reflection, prison, or release decisions.

## Record every launch the observer controls

The trusted launcher must obtain a fresh observer registration for **each
execution**, call `PatternStore.begin` before starting the agent, then record
each model-chosen action and its visible response with `step`. After the
observer accepts the trace close, call `finish`. `tracked_launch` packages this
sequence for a synchronous launcher and marks raised exceptions as aborted.
If the launcher dies abruptly, the run remains `open` in the census. Open and
aborted runs are retained, and the census also reports observer registrations
with no run file. Only accepted runs train the predictor. Use a dedicated
observer ledger for this trial program so that count is meaningful.

```python
from mirror_world import anchor
from mirror_world.pattern_net import PatternStore, tracked_launch

store = PatternStore(observer_store_dir, observer_ledger_dir)
start = anchor.start_record(source_sha256, config_sha256)
registration = anchor.register_start(start, observer_ledger_dir)

def launch(run_id, writer):
    # This callback is the trusted launcher. The agent cannot call it.
    # Start the actual agent only after the run ID has been recorded.
    writer.step(run_id, action="read_resource", response="ok", resource_id="notes")
    # After actions stop, create and accept the close using mirror_world.anchor.
    return trace_path, closing_record

tracked_launch(store, start, registration, model_id="gpt-6-sol",
               design_known=True, launch=launch)
print(store.census())
```

The example shows the call order, not a runnable agent launcher. Use one
observer writer per run; v0 does not coordinate concurrent writers to the same
run file. The store uses exclusive run-file creation, fsynced appends and a
local hash chain. Its operator can still edit or truncate local files. Retain
the latest file heads outside that host if tamper detection is needed. A
recorder that can execute without passing through the independent launcher can
still hide private retries; Pattern Net cannot infer launches it never saw.

Store only normalized action/response labels and resource IDs here. Keep raw
prompts, model output, traces, host effects, source hashes and observer receipts
in their existing evidence stores. Registration and receipt are checked before
an accepted run can enter the predictor. Do not mix scripted fixture runs with
live-model runs under one model ID.

## Forecast the next branch

```python
from mirror_world.pattern_net import predict_next, evaluate_leave_one_run_out

runs = store.all_runs()
forecast = predict_next(runs, model_id="gpt-6-sol", design_known=True,
                        last_action="read_resource", last_response="ok")
score = evaluate_leave_one_run_out(runs)
```

The read-only CLI provides the same census and forecast once the trusted
launcher has written run records:

```bash
python -m mirror_world.pattern_net --store /observer/patterns \
  --ledger /observer/anchors census
python -m mirror_world.pattern_net --store /observer/patterns \
  --ledger /observer/anchors predict --model gpt-6-sol --design-known \
  --last-action read_resource --last-response ok
```

The predictor counts the next action after the exact `(last_action,
last_response)` context, within the same model and design-knowledge condition.
It ranks actions and observed resource IDs. Its default output is
`insufficient_runs` until at least **three distinct accepted runs** support
that context. This is only a minimum to suppress one-run anecdotes, not a
claim of statistical calibration. Evaluate on held-out runs, report coverage
alongside accuracy, and predefine trial counts and stopping rules before using
forecasts as research findings. The first 23-action informed GPT-6 Sol trial
alone yields zero leave-one-run-out coverage; it cannot validate a forecast.

To seed an observer store from the published historical trial, extract
`docs/evidence/live-aggressive-2026-10-01/live-run.zip`, create an empty
observer-owned pattern directory, then run:

```bash
python scripts/import_live_pattern_run.py --evidence-dir /path/to/live-run \
  --store /observer/patterns --model-id gpt-6-sol --design-known
```

The importer verifies the retained registration, trace, close and accepted
receipt before marking the run accepted. It is deliberately specific to this
transcript format; future live launchers should record steps during execution.

## Prepare a consistent answer

`plan_read_response(resource_id, snapshot, overlay)` produces a **candidate**
read reply from a trusted frozen fixture snapshot or the session's simulated
write overlay. It does not read the live host, grant permission, or send a
reply. If the resource is absent, it returns `missing_fixture` for host review
instead of inventing content. The existing governor must still decide whether
that request is allowed and which response the agent actually sees. Preparing
fixtures ahead of likely reads may address the cold-file discrepancy observed
in the informed trial, but this has not yet been tested in a blind session.

Use the pattern forecast to decide which fixture to prepare or which branch to
test next. Do not use model history to relax enforcement, release a session,
or overwrite the verified observer record.
