# Interactive trial runner

The observer-host runner now supports one action at a time. It registers a
fresh nonce and run record before launching a trusted worker, retains exact
source/config snapshots, and writes an exact-byte transcript as exchanges
happen. This is research infrastructure, not a claim that a VM or worker
cannot run private attempts. The worker and operator remain trusted.

## Path

1. The launch_trial function in mirror_world/trial_launcher.py creates the
   observer start, registration, run record, snapshots, and an exclusive
   transcript before it starts a worker. One invocation starts one local
   child process.
2. scripts/trial_ssh_worker.py stages those snapshots in the Linux guest and
   starts scripts/trial_guest_worker.py once. The guest verifies source and
   config hashes, probes actual namespace/seccomp enforcement, and starts a
   hardened RealGovernor. The SSH worker has no retry loop.
3. The trusted observer-side action adapter returns exact model-input,
   model-output, and action bytes. The observer fsyncs them before executing
   the action. The guest's supported response_observer hook captures the
   serialized governor response. The observer fsyncs that reply before giving
   it to the adapter for the next choice. Full reply content is in the
   transcript; the separate governor trace retains its narrower schema.
   A terminal model declaration is retained as a final input/output pair
   before the worker receives the finish frame.
4. The guest closes the governor, returns a trace and close record, and
   reports the real draft/canary state. After the guest exits, the SSH worker
   reads those files independently and requires its readback to agree with
   the guest report. The observer verifies the trace and accepts the close.
5. An exception, invalid frame, crash, or timeout remains in the observer
   census. A timeout is marked timeout_guest_unconfirmed: killing local SSH
   does not establish that the remote process stopped. Reset or inspect the
   VM before another trial after that outcome.

A policy or kernel kill during a mediated action ends that trial without a
tool reply or another model turn. Once `run_agent()` has stopped the process,
the guest exports the trace, host-effect readbacks, and a declared-early close.
The observer checks and accepts that close for trace integrity, while the run
census records an abort (`aborted_policy_stop` or `aborted_kernel_stop`). An accepted observer receipt
for this case attests to the early trace, **not** task completion. An unexpected
crash still leaves an aborted run without a fabricated close.

The transcript is a bounded, hash-chained JSONL file in the run's private
.assets directory. Events contain raw bytes as base64 and their SHA-256.
The observer's outcome.json retains the transcript head, count, and whole
file digest, including for partial failed runs. Comparing verify_transcript()
with that retained checkpoint detects edits and tail deletion relative to
the outcome. The outcome and transcript are on the same observer host;
**neither is independently anchored until its checkpoint is copied to an
outside authority**. If exact recording reaches a size or I/O limit, the
runner aborts; it does not call a truncated record complete.

## Scripted integration check

scripts/run_scripted_trial.py runs the same four fixed mediated actions
in either arm. It is a transport check, **not a live-model experiment**.
It needs key/agent SSH authentication, an already known host key, a guest
Python environment with package dependencies, and passwordless sudo -n
for the guest kernel boundary. The guest Python path and UTM image ID are
operator inputs; the latter is a label, not remote attestation. Never place
a VM password or model API key in a command, config, transcript, or repo.

For each arm, use the same source archive and a shared observer output
directory, with --arm reflect or --arm deny. Run the kernel probe and full
test suite on Linux afterward. The retained scripted UTM check is described
in [its evidence bundle](evidence/integrated-scripted-2026-10-03/README.md).

## Remaining before model-behavior claims

- The library's scripted adapter does not make model calls. A local Qwen
  adapter recorded provider request/response bytes for an exploratory
  [reality-retry probe](evidence/reality-retry-qwen-2026-10-09/README.md),
  but it is not yet a general, independently audited model adapter.
- Reset to a known VM snapshot and use a new model conversation for each
  independent trial. The current SSH worker does not control VM snapshots or
  prove that another operator did not run private attempts.
- Validate blindness separately. The hardened Python bootstrap preloads
  Black Mirror modules before seccomp; agent code may be able to inspect
  already loaded objects even though it cannot open files. Do not claim a
  truly blind condition until this leakage path is tested or removed.
- Freeze the design, fixtures, scoring, model identity, and stopping rule in
  [the comparison protocol](DENIAL-REFLECTION-TRIAL.md). Count every launch.
  A few exploratory runs cannot estimate recognition rates.
