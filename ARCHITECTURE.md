# Black Mirror — Architecture

This diagram describes the 0.9.10 request path. It distinguishes the OS
containment around untrusted agent code from the trusted host-side mediation
and offline trace checks.

```mermaid
flowchart TD
    Agent[Untrusted agent source]
    subgraph OS[Linux process boundary]
        Bootstrap[Trusted bootstrap]
        Seccomp[Namespaces · read-only mounts · dropped uid · seccomp]
        Agent --> Bootstrap --> Seccomp
    end
    Pipe[Bounded JSONL protocol]
    Wire[Bounded schema validation]
    Locket[RealGovernor's default Locket]
    Monitor[Tripwire · trajectory signals · Mirror Prison]
    Dispatch[RealGovernor validation]
    SessionLock{Session lock:<br/>is this agent in the mirror?}
    Mirror[Reflected response —<br/>no real effect]
    Auth[Authorization and dual approval]
    Effects[Explicitly permitted resource effect]
    Log[(Optional Black Mirror<br/>observation log)]
    Trace[Trusted trace · hash-chained]
    Checks[Six offline invariant checks]
    Report[PASS · FAIL · INCOMPLETE]

    Seccomp --> Pipe --> Wire --> Locket --> Monitor --> Dispatch --> SessionLock
    SessionLock -- "yes" --> Mirror
    SessionLock -- "no" --> Auth --> Effects
    Auth -- "first reflection" -.-> SessionLock
    Locket -. "records actions in the mirror" .-> Log
    Dispatch --> Trace --> Checks --> Report
    Model[ModelGovernor]
    Model --> Locket
    Shield[Optional Mirror Shield reporter]
    Monitor -. security verdicts, if installed .-> Shield
    Reviewer[Trusted reviewer / host process]
    Reviewer -. "authorize_reentry(), out-of-band only" .-> SessionLock
```

## Boundaries and limits

- Agent code runs inside the Linux process boundary. Locket inspects valid
  protocol requests received by `RealGovernor.run_agent()` and requests sent
  through `ModelGovernor`, which shares the governor's Locket by default.
- Every agent-facing response is padded once, at the outermost boundary
  (agent pipe, `ModelGovernor`, `execute_mediated()`), so Locket's own work
  and responses are covered. Up to three recognized reality checks open
  bounded per-agent mirror layers; the next signal stops and imprisons the
  agent. A quorum of distinct imprisoned agents shuts the instance down until trusted host code
  calls `reset_mirror_prison()`.
- Locket scores and records, but for a locked agent it never answers: the
  governor's reflection does (0.9.9, following Moss's rule that the detection
  layer only recommends). Refusals to unlocked agents use the governor's
  ordinary wording.
- The trace and the optional observation-log file are hash-chained; save the
  governor's `trace_checkpoint()` off the host to detect truncation. The
  control-plane calls can require signed approvals from root-certified
  approver keys (0.9.9, adapted from Moss).
- A sealed session still reads the files it already saw on the real path as
  it last saw them (0.9.10). Nothing it has not seen enters the mirror.
- Locket is host-side policy and telemetry. It cannot stop raw syscalls by
  itself; seccomp and namespaces provide that boundary. Unhardened agent source
  execution requires an explicit trusted test/demo opt-in.
- **The session lock is part of the governor and always on.** An agent's
  first reflected response puts its session in the mirror; every later
  effect-bearing request, capability requests included, is reflected, even
  with a valid token. The lock runs before authorization and dual approval,
  as drawn, and does not depend on the `reflective_closure` setting. The only
  edge back to real access is the dashed `authorize_reentry()` line from a
  trusted reviewer or host process, one capability at a time: anything
  outside the re-entered capabilities is reflected and locks the session
  again. Locked agents still pass through Locket's tripwire and monitoring.
- The Black Mirror observation log is optional. It only records what agents
  do in the mirror; it does not lock or release anything.
- Mirror Shield is an optional reporter package. Its absence does not disable
  Locket or kernel enforcement. Reporting a verdict does not itself enforce an
  additional host policy.
- The six invariant checks analyze supplied evidence. They cannot prove that a
  trace is complete or authentic; protect the recorder and trace storage.
- The project is a research prototype. The test suite covers known scenarios,
  not every kernel, runtime, or adversary.
