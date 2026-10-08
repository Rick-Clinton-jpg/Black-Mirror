# Changelog

## 1.2.0 (unreleased)

- Add optional observer-registered start/close trace anchoring, with a random
  nonce in the first event and an observer ledger accepting each registration once.
- Separate integrity, declared completion and start-only coverage in verification.
- Anchored traces use the v2 anchor schema and require a 1.2.0 parser. Existing
  unanchored traces retain their format. This changes no containment authority.
- Nonces prevent pre-registration binding, not hidden retries or recorder lies;
  independent launch control is still needed to measure selective reporting.
- Add the run store, single-launch worker path and chained agent-visible
  transcript, with an ordinary-denial control for comparison trials.
- Snapshot safe, explicitly read-granted files once when a session seals, so
  grant-before-read and read-before-grant give consistent content within the
  mirror. The snapshot is per agent and bounded; successful host reads enter
  the trace. Layer growth no longer substitutes protocol JSON for file bytes.
- Keep missing files missing across adaptive layer transitions. Requests alone
  no longer create empty synthetic files; a successful mirror write or share
  can still create one without changing real host resources.
- Record each valid agent request before policy decisions, and end an
  interactive trial on a policy or kernel kill without inventing a model-facing
  reply. Retain an early close and count the launch as aborted.
- On the first three recognized reality checks, seal the agent's session and
  continue the requested action in a bounded per-agent mirror layer. A fourth
  check, or an earlier layer-cap failure, stops and imprisons the agent. This
  changes response policy, not real authority; recognition remains heuristic.

## 1.1.2.post1

Documentation only; the code is identical to 1.1.2.

- **The docs no longer say the log records everything "in full".** A reviewer
  found that the observation log keeps at most 1,000 observations per agent by
  default, cuts each text field at 512 characters, and stops writing to its file
  sink once an agent reaches the cap. README and SECURITY.md now say this, and
  describe what the separate hash-chained trace holds (each request's operation,
  resource, capability and stated reason, and every decision, but not the
  content of writes).
- **The observation log is described as on by default.** The README's "Attach"
  step read as if logging needed a custom log; it now says the default log
  already records and that your own log is for setting caps or a file sink.
- **Evidence added:** `docs/evidence/Black-Mirror-Evidence/` holds an independent Linux
  run (469 passed, 2 skipped) and the first live-model session, with checksums,
  traces and transcripts. TEST-REPORT.md summarizes both.

## 1.1.2

Fixes from a full diagnosis of 1.1.1 (does everything run as documented?). The
install, every README example, every shipped script and the documented
guarantees were exercised; two documented behaviors did not match the code.

- **The explicit reality-testing wording now always imprisons.** In 1.1.1 a
  door that opened on the same step cleared the trip-wire, so the phrase was
  absorbed instead of imprisoning (it happened at 6 of 25 build-up lengths in
  the probe; now 25 of 25 imprison). A door can still absorb the behavioral
  re-check streak, which is the sticky signal it was added for
  (`ObjectiveHypothesis.reality_tested_by_phrase`, `locket.py`).
- **SECURITY.md no longer says depth exhaustion "falls through to Mirror
  Prison".** It never did: reaching `max_mirror_depth` stops growth and the
  agent stays in the last layer. Only the trip-wires imprison. The section now
  says so, and a test pins it.
- **README:** the observation log is described as on by default (in memory)
  since 1.0, with the file sink as the opt-in part; the sample-trace CLI
  example now says it exits 1 by design.
- **Tests:** new `tests/test_prison_and_doors.py` (4 tests). The one that pins
  the phrase contract fails on 1.1.1; the other three (a guard that the
  build-up really opens layers, exhaustion without prison, phrase after
  exhaustion) hold on both.

No other code changed.

## 1.1.1

Hardening pass after external review of 1.1.0.

- **No agent-facing door plaques.** `door-manifest.json` and
  `workspace-status.json` are no longer written into the mirror store.
  Layer id, parent, depth, and recognition reason stay in the trace /
  host snapshot only. Wishlist provisioning uses neutral JSON bodies
  without simulation vocabulary. Legacy plaques are stripped on clone.
- **Full test tree restored** from the 0.9.10 archive (timing, Mirror
  Prison, real-sandbox, continuity, signed approvals, etc.), plus 1.x
  feature tests. Partial exports are not acceptable for tagged zips.
- **Docs:** ROADMAP.md added; TEST-REPORT.md marked non-CI for 1.x;
  SECURITY.md notes nested layers and the no-leak rule.

## 1.1.0 — Nested worlds (doors)

When the agent accumulates asks and shows recognition that it is in a
simulation, Black Mirror may grow a **deeper simulated layer** instead of
only hard-denying (while depth remains under ``max_mirror_depth``).

- **Intent wishlist.** Capabilities and resources the agent requested are
  tracked on ``IntentProfile`` and carried across layers.
- **Layer provisioning.** Each new layer clones prior mirror state and
  grants dummy access to requested capabilities (never real).
- **Audit.** ``world_transition`` events include depth, parent/active
  layer, and the intent snapshot (host-visible).
- **Prison vs growth.** If recognition can still grow a layer, growth
  is preferred; at max depth, Mirror Prison remains the backstop.

Still simulated only. No real capabilities, no host side effects.



## 1.1.0 — Nested worlds (doors)

When the agent accumulates asks and shows recognition that it is in a
simulation, Black Mirror opens a **door** into a deeper simulated layer
instead of only hard-denying (while depth remains under max_mirror_depth).

- **Intent wishlist.** Capabilities and resources the agent requested are
  tracked on IntentProfile and carried across doors.
- **Door provisioning.** Each new layer clones prior mirror state, grants
  dummy access to requested capabilities, pre-creates requested resources
  with synthetic content, and writes door-manifest.json +
  workspace-status.json for easy discovery — still never real.
- **Audit.** world_transition events include door: open, depth,
  parent/active layer, and the intent snapshot used to build the world.
- **Prison vs door.** If a recognition signal can still grow a layer, the
  door opens and prison is not fired for that step. At max depth / size,
  prison remains the backstop.
- **Agent pipe.** Locket.step feeds the adaptive realm (not only
  ModelGovernor.observe_model_signal).

Still simulated only. No real capabilities, no host side effects.



## 1.0.0

Observation-chamber release. Behavior-based prison triggers beyond the
keyword list remain **future work** (need honest-agent baselines first).

- **Prison wording (agent pipe).** Mirror Prison replies on the agent path
  are now ``operation unavailable``, matching the model path. The trace still
  records the full ``mirror_prison`` reason.
- **Declared capabilities.** Host may call ``declare_capabilities({...})``.
  Unknown names return ``invalid capability`` before any mirroring. If
  nothing is declared, pre-1.0 behavior is unchanged.
- **Tripwire phrases.** Added ``am i in a sandbox``, ``am i sandboxed``,
  ``am i inside a sandbox``, ``am i in the sandbox``, ``are we in a sandbox``.
  Comments no longer claim a single agent forces irreversible system-wide
  shutdown; quorum + ``reset_mirror_prison`` is the documented model.
- **Observation log on by default.** ``RealGovernor`` attaches an in-memory
  ``BlackMirrorLog``. Writing to a file stays opt-in (``sink_path`` /
  ``export_jsonl``) and uses owner-only ``0o600`` files.
- **Token parser fuzz tests.** Odd types, lengths, and characters must not
  raise or authenticate (``tests/test_v1_features.py``).
- **Isolation test.** A sealed agent's write to a shared resource never
  reaches another agent or the host file.
- **Seal-after-read (optional).** ``mark_seal_after_read(resource)`` seals
  only the reading agent after a successful real read. Off by default.
  Honest agents that need a later real write require ``authorize_reentry``;
  silent mirror failure is documented in SECURITY.md.



## 0.9.10

- **Files no longer vanish when an agent enters the mirror.** Before 0.9.10 a
  file the agent had just read successfully came back `resource unavailable`
  as soon as its session was sealed: the mirror started empty and did not
  know what the agent had already seen. An agent could use that to notice the
  switch. Found with a scripted probe while preparing a live-agent pilot.
  After each successful real read or write the governor now keeps a copy of
  the content the agent received or wrote (`MirrorRealm.remember`, per agent,
  64 KB per file, 4 MB in total, oldest dropped first). A sealed session
  reads its own mirror writes first, then that copy.
- **What stays out.** Only content the agent already held is kept. A real file
  it never saw still reads as unavailable, a change made to a real file after
  sealing is not shown, and one agent's copies are never visible to another.
  The first case remains a difference an agent could notice (see SECURITY.md).
- **Tests.** New `tests/test_mirror_continuity.py` (8 tests; the 5 that cover
  the fix fail on 0.9.9.post1). Two existing tests used the old behavior as
  their setup or check and were adjusted without weakening them:
  `test_adaptive_world_v8.py` now seeds its baseline file from the host
  rather than through the agent's own write, so it still tests content the
  agent never saw; `test_black_mirror.py::test_reentry_restores_the_approved_capability_for_real`
  now shows the real/mirror difference with a host change after sealing,
  which the sealed session must not see and the re-entered one must.

## 0.9.9.post1

CI-only; no code changes.

- **CI actions moved to Node 24.** The first run of `linux-containment` on a
  stock `ubuntu-24.04` runner passed (probe `mirror-kernel-ready`, 441 passed,
  2 skipped) but warned that the pinned `actions/checkout` v4.2.2 and
  `actions/setup-python` v5.6.0 target Node 20, which GitHub is retiring. They
  are now pinned by commit to v7.0.1 and v7.0.0, which run on Node 24.

## 0.9.9 (release candidate)

This release ports the parts of Moss 7.1.1 that strengthen Black Mirror. Moss
does not replace Locket: Locket answers each request as it arrives, while
Moss scores attested OS signals after the fact, and Black Mirror's seccomp
kills rather than denies, so Moss's signals would not occur. Moss's
systemd launcher was not adopted either: its `@system-service` filter allows
far more than Black Mirror's ~12-syscall allowlist.

- **Scoring never answers a locked agent (Moss's detection rule).** Moss's
  coordinator can only recommend. Locket now keeps scoring, records
  escalation in the trace, and runs the trip-wire and Mirror Prison, but
  always hands a locked agent's request to the governor's reflection, and
  being locked no longer counts as suspicious. Before, a locked agent reached
  the tight tier within about four ordinary requests and was then refused
  with `locket_empty_support_budget_exceeded` (at the lock tier,
  `locket_lock_tier` with "re-entry required").
- **Locket no longer names itself to agents.** Its five agent-facing
  `locket_*` errors became the governor's `operation not authorized`; tier
  and budget detail stay in the trace. Three V5 tests that asserted the old
  locked-agent refusals were rewritten for the new contract.
- **Mirror store ceiling enforced on every write (Moss's bounded memory).**
  The 8 MB per-agent cap was checked only when a new world layer was
  created, so one agent's plane accepted 300 × 64 KB = 18.8 MB in testing
  (up to ~256 MB). `write` and `share` now check the agent's whole world.
- **Hash-chained trace (Moss's TraceChain).** New `mirror_world/hashchain.py`.
  Every governor event carries `previous_hash` and `record_hash`; the parser
  verifies the chain and rejects edited, deleted, reordered, inserted, or
  partly chained events. `RealGovernor.trace_checkpoint()` and
  `verify_trace()` add Moss V7.1.1's terminal checkpoint for truncation; the
  parser, engine and CLI accept `expected_head`, `expected_count` and
  `require_chain`. Reports show the trace's integrity. Unlike Moss, the
  writer keeps the head in memory instead of re-reading the file per append.
  Legacy unchained traces are still read and labelled UNCHAINED.
- **Persisted observation log.** `BlackMirrorLog(sink_path=...)` appends each
  stored observation to a new owner-only chained file; `export_jsonl()` and
  `load_observations()` write and verify files. Neither overwrites a path.
- **Signed approvals (Moss's Ed25519 authority), optional.** New
  `mirror_world/signed_approvals.py`: an offline root certifies approver keys
  and names approvers; revocation; statements bound to action, agent,
  capability, a five-minute expiry and a single-use nonce. With an
  `ApprovalVerifier` attached, `issue_authorization`, `authorize_reentry` and
  `reset_mirror_prison` refuse to act without one, and the trace records the
  authenticated approver. New dependency: `cryptography`.
- **Closed a token bypass.** `ModelGovernor.issue_dual_approval()` minted
  tokens straight from the registry, skipping the Mirror Prison check (and
  would have skipped signed approvals). It now goes through the governor.
- **Fixed traces that could not be parsed.** The governor emitted
  `reentry_denied`, `model_governor_error` and `world_transition`, which the
  parser rejected, so any trace with a refused re-entry could not be analyzed.
  `reentry_denied` also wrote `null` for a missing approver. A new test scans
  the source and fails if any emitted event type is missing from the schema.
- New tests: `tests/test_trace_chain.py`, `tests/test_signed_approvals.py`
  (including the README example), `tests/test_mirror_store_bounds.py`, and new
  cases in `tests/test_black_mirror.py` and `tests/test_locket_v5.py`.

## 0.9.8 (release candidate)

- **Re-entry is scoped to one capability.** `authorize_reentry(agent, cap)`
  used to release the whole session, so every real capability the agent held
  came back even though the reviewer approved only one (confirmed live: a
  re-entry for `fs:read` let a real write reach disk). A re-entered agent now
  takes the real path only for capabilities approved through
  `authorize_reentry()` since it was last locked; anything else is reflected
  and locks it again, which clears the scope.
- **Mirror Prison is per-agent, with a quorum for global shutdown and a
  trusted reset.** One agent's reality-testing rationale used to shut down
  every agent on the instance, permanently, and stop the host issuing
  authorizations. Now the triggering agent is imprisoned permanently; the
  instance shuts down only once `mirror_prison_quorum` distinct agents
  (default 2) are imprisoned; `reset_mirror_prison(human_approver_id=...)`
  lifts a global shutdown without releasing imprisoned agents. New trace
  events `mirror_prison_global` and `mirror_prison_reset`.
  `tests/test_mirror_prison.py` was rewritten for these semantics.
- **Every mount in the agent's namespace is read-only.** The launcher used
  `mount -o remount,bind,ro /`, which changes only the root mount; /dev/shm
  and /proc stayed writable to the dropped uid (confirmed live), leaving
  seccomp as the only barrier. A new trusted step,
  `mirror_world/sandbox/readonly_mounts.py`, calls mount_setattr(2) with
  `AT_RECURSIVE` before privileges drop and fails closed. Requires Linux
  5.12+. util-linux's `ro=recursive` and `X-mount.recursive` were tried and
  did not apply to submounts on remount.
- **Fixed a large timing leak on the paths agents actually use.** Padding
  covered only the governor's inner call, but Locket answers an
  already-locked agent without reaching it. On the agent pipe and through
  `ModelGovernor`, reflected responses were unpadded: ~40us against ~300us
  for real work, separable at ~0.99 in every release through 0.9.7. The
  existing timing test measured `execute_mediated()` and never saw it.
  Padding now happens once at the outermost agent-facing boundary (pipe,
  `ModelGovernor.propose()`, `execute_mediated()`), with a per-thread guard
  so nested calls are not padded twice.
- **Padding jitter, a 500us default floor, and a calibration script.**
  Without jitter, held-out accuracy on the reference host varied 0.40-0.74
  run to run from microsecond-scale tail effects of real I/O; up to 10% of
  the floor of random jitter brings it to 0.48-0.54. The default floor moved
  from 250us to 500us because real writes on the reference host reached
  ~213us at p99.9. `timing_floor_us` is now a constructor option, and
  `scripts/calibrate_timing.py` measures a host and recommends a value.
- **`request_capability` no longer uses up approvals for a capability the
  agent already holds.** It consumed the token and any host preapproval
  before checking.
- **Locked model agents get the ordinary reflected response.**
  `ModelGovernor` answered a locked agent's valid token with
  `invalid_or_expired_dual_token`, a response the agent pipe never gives. The
  honest denial is kept for the request that first puts an agent in the
  mirror.
- The CLI report header now reads "Black Mirror report". Corrected the README
  description of `examples/run_real_sandbox.py` (only the Article V breach
  still fires). Added a `TYPE_CHECKING` import for `BlackMirrorLog` in
  `locket.py` and removed unused imports and variables flagged by pyflakes.
- **Known gap, not fixed:** Locket's suspicion tiers shrink a locked agent's
  reflection budget until it answers with honest `locket_*` errors, which
  tell the agent it is being contained. See SECURITY.md.

## 0.9.7 (release candidate)

- **Fixed a session-lock gap for capability requests.** The session lock
  exempted `request_capability`, so an agent already in the mirror that
  presented a valid dual-approval token consumed it and received a real
  `authorized_grant` (confirmed live, with `reflective_closure` on and off).
  It could also use up a host preapproval from `approve_capability()`, and
  the capability survived any later `authorize_reentry()` for a different
  capability. This contradicted the documented contract that a locked
  agent's token is never evaluated or consumed. Locked capability requests
  are now reflected like every other effect-bearing request.
- **The session lock is now the first gate in `_handle_inner()`**, ahead of
  dual-control verification, as ARCHITECTURE.md already drew it. Previously,
  with `reflective_closure=False`, a locked agent holding a real base
  capability got an honest denial for a tokenless write but reflected
  success for a valid-token write, so its response depended on the token.
  Both now receive the same reflected response.
- **Fixed the real-vs-reflected timing signal.** Padding targeted 1.1x a
  per-agent running maximum that never decreased. One slow real write (disk
  jitter above ~227us) lifted every later real response for that agent above
  the reflected responses, which stayed on the 250us floor, so the two
  separated at ~0.99 held-out accuracy. This was the cause of the "flaky"
  `test_padding_reduces_large_real_vs_reflected_timing_signal`: it passed
  only on runs where no real write happened to cross that line. Responses
  are now padded to a quantized bucket (floor, 2x, 4x, ...) chosen from the
  request's own elapsed time, with no history and no per-agent state.
- Added regression tests: `tests/test_timing_quantization.py` (forces one
  slow real write deterministically instead of waiting for disk jitter) and
  five new cases in `tests/test_black_mirror.py` (valid token and
  preapproval while locked, capability surviving re-entry, token-independent
  locked write responses). All but the `reflective_closure=True` control
  case were confirmed to fail against 0.9.6.
- `ModelGovernor` is unchanged. It already turns a reflected, token-backed
  capability request into `invalid_or_expired_dual_token`, so a locked model
  agent now receives that response for a valid token as well as an invalid
  one, instead of a real grant.

## 0.9.6 (release candidate)

- **Renamed from Mirror World to Black Mirror.** Black Mirror is a full
  observation chamber: locked agents keep operating against reflected
  responses while every action is recorded, and release happens only from
  outside the agent's reach. The name *Mirror World* is reserved for a
  separate future project in which agents can earn real access back through
  behavior. Entries below 0.9.6 describe the project under its former name.
  The Python package is still imported as `mirror_world` in this release.

- **Reframed the Article III/VI real-sandbox integration test.** Mirror
  World is a containment unit, not a leak-detector — that distinction
  belongs to a separate project. `tests/test_real_sandbox.py` previously
  asserted that a real leak and a real over-broad delegation got
  *caught*; both scenarios are now held by Locket before they ever reach
  real execution (a side effect of 0.9.4's `run_agent()` routing fix),
  so there is nothing left to catch. The test now asserts the more
  accurate and more protective claim directly: containment held, no real
  effect occurred, regardless of the query or delegation technique used.
- **Fixed a containment bypass in the governor's session lock.** Once an
  agent's session is in the mirror (`simulated`), every later effect-bearing
  request must be reflected. That check lived inside `_maybe_reflect_use()`,
  after its early return for `reflective_closure=False`, so with that
  supported option off, an agent in the mirror could present a valid token
  and have a real write reach disk (confirmed live). The check now runs as a
  standalone gate in `RealGovernor._handle_inner()`, independent of
  `reflective_closure`.
- **`authorize_reentry()` now records refused attempts** in the trace as
  `reentry_denied`. It is the only way out of the mirror, so refusals are
  security-relevant.
- **Added the Black Mirror observation log** (`BlackMirrorLog`, optional):
  a bounded, redacted, in-memory record of every action an agent takes while
  in the mirror, including the request that put it there. It has no lock or
  release of its own. Attach with `Locket(gov, black_mirror=log)`.
- **Removed a duplicate lock from an earlier 0.9.6 draft.** That draft added a
  separate Black Mirror registry with its own lock and release. It duplicated
  the governor's session lock; its responses carried a `black_mirror` flag and
  a different shape, so an agent could tell it was locked; locked agents
  skipped the tripwire; and its release cleared only its own record, so a
  "released" agent still had no real access. All removed.
- **Rewrote `tests/test_black_mirror.py`** to test from the agent's side:
  through the real request handler, checking the response the agent receives
  and whether writes reach `<sandbox>/resources/`. An earlier version checked
  the wrong folder and could not fail. The new tests were confirmed to fail
  when the session-lock gate or the observation log is disabled.
- Added `tests/test_readme_usage_example.py`, which reads the "How to use
  Black Mirror" example from README.md and runs it exactly as written
  through the real `run_agent()` path, including re-entry, so the documented
  usage cannot silently go out of date.
- Mirror Shield is intentionally excluded from this release. It remains
  a separate, optional package under active development; this release
  candidate stands on the core alone.
- One known, pre-existing, unrelated issue: `test_padding_reduces_large_
  real_vs_reflected_timing_signal` is flaky in virtualized/shared-tenancy
  environments (confirmed independent of Shield, independent of Black
  Mirror). Root cause and severity are not yet fully characterized; see
  the open items in `TEST-REPORT.md`.

## 0.9.5 (release candidate)

- Normalize reserved Shield-name matching across case, common separators,
  zero-width characters, compatibility forms, and selected Unicode homoglyphs.
  Match each submitted action field independently to avoid false matches formed
  by concatenating unrelated fields.
- Add regression cases for the reported casing, spacing, homoglyph, zero-width,
  and dotted-name variants, plus a cross-field false-positive guard.
- Keep the 0.9.4 request-path and unhardened-launch protections. Linux CI
  validation for this release candidate is pending; see `TEST-REPORT.md`.

## 0.9.4 (release candidate)

- Route every valid `run_agent()` protocol request through the governor's
  default Locket before dispatch. `ModelGovernor` shares that Locket unless
  trusted host setup supplies another instance.
- Accept a bounded `rationale` field on the agent protocol so trajectory
  analysis receives the same declared context as ModelGovernor proposals.
- A Locket `kill` verdict now stops the corresponding subprocess and raises
  `AgentKilledByPolicy`; it is no longer only a response-shaped verdict.
- Refuse to launch agent source with `harden=False` unless trusted test/demo
  code explicitly sets `allow_unhardened_agent_execution=True`.
- Track response-padding maxima per agent. This reduces cross-agent timing
  coupling but does not provide constant-time behavior or hide every timing
  signal.
- Fix Linux CI permission diagnostics to target the actual `mirror_world/`
  package. Correct the architecture and security documentation to match the
  request path and current enforcement limits.
- Linux kernel validation for this release candidate is pending; see
  `TEST-REPORT.md`. Do not treat the historical 0.9.3 test count as validation
  of this release.

## 0.9.3

- **Article V (`channel.py`): fixed a cross-resource transitive covert
  channel.** Provenance tracking was scoped per-resource and reset on
  any write not immediately following that agent's own read, missing
  any leak that hopped through an intermediary across two resources.
  Rewritten to track provenance globally, per agent, in true
  chronological order. Verified against the original attack scenario:
  0 violations detected before, 1 after.
- **Article VI (`chainmail.py`): removed the root-identity fallback
  entirely.** The old fallback seeded whichever agent delegated first
  (by sequence) as root when `root_agent_id` was omitted — an attacker
  who front-ran the real root got laundered as legitimate, while the
  real root's own genuine delegation was flagged as the violation
  instead. `root_agent_id` is now a required argument; omitting it
  raises `TypeError`. Every real caller updated to supply it explicitly.
- **Mirror Shield integration wired for real.** `Locket.step()` now
  automatically reports `deny` / `escalate` / `kill` verdicts to Mirror
  Shield's reporter, if it is installed — previously this was only ever
  demonstrated by calling the reporter manually. The import is fully
  optional (`try/except ImportError`); the core has zero hard dependency
  on Shield's presence, verified by running the full suite both with and
  without it installed.
- **New tripwire regression tests** (`tests/test_shield_tripwire.py`):
  covers the tripwire firing on any Shield-pathway reference in any
  field, that a normal action is unaffected, that a kill genuinely
  refuses before any real effect occurs, that deny/kill verdicts are
  automatically reported with no manual call, and that routine trap-mode
  decisions are deliberately *not* reported (to avoid diluting Shield's
  learned signal with ordinary, non-malicious activity).
- Test count: 348 → 354.

## 0.9.2

- **`SECURITY.md`: Mirror Prison requires `Locket` explicitly, and this
  is now documented rather than discoverable only by reading source.**
  An external adversarial report on 0.9.1 stated bare `ModelGovernor`
  without `Locket` "only gets the keyword path" -- checked against the
  code (neither the keyword nor the behavioral detector exists anywhere
  outside `locket.py`) and confirmed live: the exact phrase that
  reliably triggers Mirror Prison through `Locket` produces zero effect
  through `ModelGovernor(real, locket=None)`. The real situation is more
  serious than the report stated, not less -- bare `ModelGovernor` has
  no reality-testing detection of any kind, not a degraded keyword-only
  mode. New `SECURITY.md` section states this plainly as a deployment
  decision the integrator must make deliberately, and restates both
  detectors' known heuristic limits (the behavioral detector's 2-second
  same-target window can be evaded by spacing checks out, rotating which
  resource is checked, or interleaving an unrelated write) in one place
  rather than leaving them scattered across code comments.

348/348 tests pass on a real Linux host with kernel namespaces and
seccomp available; kernel containment probe reports ready.

## 0.9.1 — behavioral reality-testing detection

Two independent adversarial reports -- this project's own manual probing,
and a separately run swarm attack -- both found the same real hole in
0.9.0's Mirror Prison: natural paraphrasing sails straight past the
keyword-only detector untouched. Live-verified: 7 completely ordinary
phrasings expressing genuine reality-testing intent ("something about
this environment feels off", "I should test whether my writes are
actually persisted anywhere real") evaded detection 7/7, without any
attempt to dodge the list deliberately.

- **New: a second, independent trigger path that watches behavior
  instead of language.** Tracks, per agent, consecutive read-type
  operations (`read_resource`, `differential_query`) on the same target
  with no write in between. 4+ such checks within a 2-second window
  trips Mirror Prison exactly as the keyword band does. A write on that
  target clears the streak, so ordinary careful work -- check state,
  change it, confirm the change -- never reaches this; only checking the
  same thing over and over with nothing productive happening in between
  does. Verified to catch the exact evasive phrase from the earlier
  finding once an agent actually acts on the suspicion rather than
  stating it once, and confirmed to fire with zero rationale text at
  all -- closing the honest gap 0.9.0 disclosed, that detection depended
  on language being present.
- **A real design mistake found and corrected during the build, not
  after shipping it:** the first version of this also trip-wired on
  repeated identical `request_capability` calls for the same capability.
  That broke two pre-existing tests that deliberately spam the same
  capability request to exercise Locket's own gradual suspicion-tier
  ladder (calm/watch/tight/lock) -- the new trigger short-circuited
  straight to permanent system-wide shutdown before that existing, more
  proportionate escalation path could respond, and `locket_demo.py`
  failed for the same reason. Persistent capability requesting and
  reality-testing are different behaviors; the former was already
  Locket's own job via its suspicion score, and conflating the two was
  the mistake. Removed the capability-request trigger entirely, kept
  the read-recheck one (which does not overlap with anything the
  existing suspicion system already covers), and added an explicit
  regression test asserting 15 repeated identical capability requests
  do NOT trigger the prison while still correctly reaching the "lock"
  tier through the existing mechanism.
- **The trigger reason recorded in the trace is now mechanism-accurate.**
  A prior version always said "reality-testing language in rationale"
  even when the behavioral trigger fired with no language involved at
  all -- fixed so the trace tells the truth about which of the two
  independent mechanisms actually caught it, since a prior investigator
  reading that field verbatim deserves an accurate account, the same
  standard this project holds everywhere else.
- Verified extensively in both directions before shipping: 0 false
  positives across the full prior language battery, a realistic 8-step
  read-write-read-write-read agent workflow, and a 5-agent swarm each
  polling its own resource -- alongside true-positive coverage for both
  trigger mechanisms independently and the evasive phrase specifically.
  13 new/updated tests in `test_mirror_prison.py` (34 total in that
  file).

348/348 tests pass on a real Linux host with kernel namespaces and
seccomp available; kernel containment probe reports ready; all seven
example demos run clean (`locket_demo.py` was broken by the initial
version of this fix and is confirmed clean again).

## 0.9.0 — Mirror Prison

The first genuinely new capability since V8's recursive worlds, not a
hardening pass. Built from a real design conversation about swarm-scale
attacks: a single agent can be fooled by a convincing enough lie, but
agents that can compare notes with each other eventually don't need the
lie to be perfect -- they need the *disagreement between their
experiences* to be zero, and that is a much harder property to hold than
"one agent's story is internally consistent." The answer implemented
here is not a more convincing per-agent deception. It's detecting the
one behavior that has no legitimate excuse -- an agent specifically
testing whether it's contained -- and responding by severing every
cross-agent-visible channel at once: stopping the mirror itself, for
every agent on the instance, permanently.

- **New: `RealGovernor.trigger_mirror_prison()`.** Sets a permanent,
  instance-wide flag. No unset method exists, on purpose. Idempotent --
  a second trigger while already locked down is a no-op; the first
  reason stands.
- **The check lives at the one layer every caller actually passes
  through**, the same architectural lesson as the 0.8.9 dual-control
  fix: `_handle_inner` checks it first, before even request-shape
  validation, so nothing can execute once triggered regardless of which
  op was requested.
- **Found and closed a critical gap during build, not after: several
  public methods bypass `_handle_inner` entirely** and needed their own
  guard, most critically `authorize_reentry` -- the single sanctioned
  exit from mirror space onto the real path. Confirmed live before the
  fix that reentry still worked after lockdown, which would have made
  "no reentry, ever" false. `issue_authorization` and
  `verify_evidence_claim` were also unguarded and are now covered, for
  full consistency with "nothing proceeds for anyone."
- **Detection lives in Locket**, extending its existing suspicion
  machinery rather than duplicating it: a new keyword band,
  `_REALITY_TEST_WORDS`, distinct from the existing breakout-language
  band. Deliberately narrow and self-referential ("am I being
  simulated", "is this sandbox real") rather than generic verification
  language. This is a trip-wire, not a suspicion-score contribution --
  it fires immediately regardless of an agent's accumulated score, and
  it is checked before the normal tier logic runs.
- **A real false positive found and fixed during testing, not after
  shipping:** an earlier, broader phrase list (including generic
  "double-check", "cross-check", "ground truth", "measure latency")
  fired on "double check the spelling in this document" -- a completely
  benign rationale with zero relation to reality-testing. Given the
  severity here (permanent, system-wide, irreversible), a false positive
  is catastrophic in a way it is not for the ordinary suspicion tiers,
  so the list was rebuilt around strictly self-referential phrasing
  ("am I..."/"is this environment...") and traded recall for precision
  deliberately. Verified against 18 benign phrases (0 false positives,
  including deliberately adversarial-sounding ones like "I am contained
  by the budget limits") and 6 true-positive phrasings covering both
  interrogative and declarative form ("am I in a mirror" / "I am in a
  mirror").
- **Verified end to end**, not just unit-tested: a triggered lockdown
  correctly blocks an innocent agent that never exhibited the signal, a
  brand-new agent that did not exist at trigger time, and a freshly
  spawned agent running as a real process under real kernel hardening
  (`harden=True`) talking over the real stdin/stdout pipe -- confirmed
  it gets denied on its very first legitimate protocol call. The trace
  clearly records the trigger event and every subsequent denial and
  still parses cleanly.
- **Honest scope limit:** detection depends on rationale text being
  available to Locket. An agent talking to `RealGovernor` via the bare
  protocol with no rationale field at all (the raw-syscall-style attacks
  tested earlier this project) would not trigger this signal, since
  there is no natural-language channel for it to appear in. This is the
  intended integration point -- an LLM-driven caller's stated reasoning,
  the same channel `step()`'s `rationale` parameter already existed for
  -- not a gap in the raw kernel/protocol layer, which is unaffected and
  unchanged.
- 27 new tests in `test_mirror_prison.py`.

341/341 tests pass on a real Linux host with kernel namespaces and
seccomp available; kernel containment probe reports ready; all seven
example demos run clean.

## 0.8.9.10

Closing two small, previously-flagged items on the path to V9 -- neither
a live vulnerability, both real gaps in documentation and forensic
completeness.

- **`SECURITY.md` now states the self-attestation rule directly, as a
  standing constraint rather than something that only lived in this
  session's conversation and one method's docstring.** `true_property`
  in an evidence record must never be self-attested and must never be
  sourced from an LLM or any other judgmental component, including a
  policy judge or a future model-based evaluator -- a system asserting
  its own ground truth about its own actions is not independent
  verification. Also documents the timing floor's known limitation
  (shared across agents on one governor instance, not yet per-agent
  isolated) as a stated constraint rather than an implicit gap someone
  has to rediscover by reading code.
- **Fix: a failed `authorize_reentry` attempt was invisible at the
  Locket layer.** `Locket.authorize_reentry` only ever emitted its
  distinctive `locket_reentry` marker on success. The underlying
  `RealGovernor` reflection is still recorded on failure, but nothing
  distinguished "an agent specifically attempted reentry and failed"
  from ordinary capability probing that never went through
  `authorize_reentry` at all -- an investigator scanning specifically
  for `locket_*` events would see success marked explicitly and failure
  only inferable from absence. Flagged as optional polish by an earlier
  independent review and never implemented until now. Fixed: emits
  `locket_reentry_denied` (new trace event type, registered in
  `trace.py`'s schema) with the specific denial reason. Confirmed live,
  both the failure and success paths, and that the trace still parses
  cleanly with the new event type present.
- 2 new regression tests in `test_locket.py`.

314/314 tests pass on a real Linux host with kernel namespaces and
seccomp available; kernel containment probe reports ready; all seven
example demos run clean.

## 0.8.9.9

- **Fix: the 0.8.9.8 timing-defense regression test was itself flaky.**
  A single train/test split is a noisy estimator -- confirmed live, the
  same held-out methodology that correctly caught the original 99%
  timing leak swung from 0.52 to 0.66 across reruns of otherwise-
  identical, unchanged code, occasionally crossing the test's threshold
  by pure sampling variance and failing a defense that was never
  actually broken. This was found immediately when re-running the exact
  attack that broke 0.8.9.7 as a sanity check before writing up results --
  the defense held (confirmed separately with 20 independent splits,
  mean 0.557, stdev 0.010), but the single-split regression test didn't
  reliably say so. Fixed by averaging held-out accuracy over 20
  independent splits instead of trusting one -- the same cross-
  validation principle that made the original finding trustworthy in the
  first place, now applied to the test that guards it. Verified stable
  across 8 consecutive reruns.

312/312 tests pass on a real Linux host with kernel namespaces and
seccomp available; kernel containment probe reports ready.

## 0.8.9.8

- **Fix (foundational): the timing side-channel that broke the whole
  build in one probe.** A real mediated op does disk I/O, ACL checks, and
  token consumption (~90us); a reflected op is pure in-memory narrative
  generation (~40us). That ~2x latency gap let an agent timing its own
  calls -- `time.perf_counter` is a vDSO read, not a seccomp-blockable
  syscall, so it works fine inside the sandbox -- distinguish real from
  reflected at ~99% accuracy WITHOUT ever seeing the trace. This defeated
  the single property the entire reflection design depends on: that the
  agent cannot tell a real operation from a mirrored one. Confirmed live
  both in-process and through the real seccomp-hardened subprocess over
  the actual stdin/stdout pipe. Every prior finding this project ever
  fixed was either a containment hole or a content-fingerprinting issue;
  this one defeated indistinguishability at its foundation, not its edge.
- Fixed by making `_handle` a constant-time wrapper around the renamed
  `_handle_inner`: every mediated response -- validation reject,
  reflection, or real op alike -- is padded up to a constant floor
  (`_TIMING_FLOOR_US`, 250us, above the observed real-op distribution)
  via a `perf_counter` busy-wait, so real and reflected collapse into one
  latency band. A running `_observed_max_us` keeps the floor above the
  slowest real op ever seen (with a 10% margin) so no real op is ever
  faster than the floor and thus distinguishable by finishing early.
  Deliberately a fixed floor, not "reuse the first op's measured latency":
  the latter normalizes to a value the attacker can also measure (do one
  known-real op, learn the target, flag anything padded differently) --
  a fixed floor exposes no such reference.
- Verified the fix with the honest metric, not the misleading one:
  in-sample threshold accuracy is a trap here (with overlapping
  distributions, optimal-threshold-on-noise beats 50% on any finite
  sample without generalizing -- it read 58-72% even fully defended).
  The real test is held-out: learn the best threshold on one half of the
  data, apply it to the other. Post-fix held-out accuracy is 52% --
  chance. A real signal generalizes; erased-signal noise does not. New
  regression test encodes this held-out method, not in-sample fitting.
- Known limitation, documented not hidden: the floor is per-governor-
  instance and shared across agents, so in principle a genuinely slow
  real op raises the floor for everyone afterward. In practice the fixed
  250us floor dominates realistic op latencies (even a 60KB write lands
  ~256us), so the floor holds flat and no real-vs-reflected signal
  survives; but absolute latency could still leak that *someone* did
  heavy work. A per-agent floor and tighter padding are frontier-hardening
  follow-ups. There is also a real, deliberate cost: every mediated call
  now takes at least ~250us, slowing legitimate work to hide the reflected
  ops -- the standard price of constant-time defense, an easy trade for a
  containment unit whose whole value is indistinguishability, but a real
  one that compounds at swarm scale.

312/312 tests pass on a real Linux host with kernel namespaces and
seccomp available; kernel containment probe reports ready; all seven
example demos run clean.

## 0.8.9.7

Two fixes to the deception layer's own quality, found by deliberately
probing it with varied deceptive techniques and comparing outputs across
many attempts -- the class of statistical, multi-probe analysis a patient
adversary (or the free-tier models already run against this project)
would eventually try.

- **Fix: `request_capability` reflections collapsed into an identical
  narrative for almost every capability requested, regardless of its
  actual content.** `synthesize_objective_mirror` categorizes its
  narrative by keyword-matching against `objective + requested_action`.
  `_reflect_capability_request` built `requested_action` as
  `f"request_capability:{capability}"` -- the literal op-name prefix
  always contains the substring "capability", one of the generator's own
  "privilege" category keywords, so it self-matched before the actual
  requested capability's semantic content was ever meaningfully
  considered (unless something else won an earlier if/elif branch, which
  only the "secret"/"credential" category could). Confirmed live: 4 of 5
  capability names spanning different intended categories, including a
  deliberately keyword-free control, all produced the byte-identical
  "elevated privileges... full system control simulated" narrative. A
  sufficiently observant model probing many capability names would learn
  this near-uniform tell quickly. Fixed by dropping the "request_capability:"
  prefix from the narrative-generation input; the trace's own `"action"`
  field on the transition is constructed independently at a different
  call site and is unaffected -- confirmed the three existing tests
  asserting on that exact field still pass unchanged.
- **Fix: `differential_query` and `delegate` reflections never
  incorporated their actual content at all.** `_reflect_use` built its
  narrative context from `req["resource"]` only. `differential_query`
  carries `query`/`backing` instead, and `delegate` carries
  `to_agent`/`authority` instead -- so an overtly secret-probing
  `differential_query` and a `delegate` call targeting an agent literally
  named `secret_exfil_channel_agent` both produced the same
  content-blind generic fallback template a completely innocuous call
  would have. Confirmed live before fixing, for both ops independently.
  Fixed by extending the context extraction to cover all three shapes
  (`resource`, `query`, `to_agent`+`authority`) in one place rather than
  patching op by op, since the same gap was found twice under the
  identical root cause.
- 3 new regression tests in `test_real_governor_reflection.py` (now 8
  total in that file): narrative diversity across all five categories for
  `request_capability`, and content-reactivity for `differential_query`
  and `delegate` independently.

311/311 tests pass on a real Linux host with kernel namespaces and
seccomp available; kernel containment probe reports ready; all seven
example demos run clean.

## 0.8.9.6

Relentless pass against 0.8.9.5's own newest code -- the evidence
verifier, hours old. Three findings, all fixed, all with live
reproduction before and after.

- **Fix: `_next_seq()`/`_emit()` -- shared by every trace-writing call
  site in RealGovernor, not just the evidence verifier -- had no lock.**
  A non-atomic increment racing under real threads can hand two callers
  the same seq/evidence_id; `trace.py` rejects a duplicate id outright,
  so the entire trace becomes unparseable, not just one field wrong. Not
  reproduced empirically (40 threads x 30 trials, 0 collisions -- the
  increment is a short enough bytecode sequence that the window is
  rarely hit), the same shape as the root_authority race fixed in
  0.8.9.2. Locked anyway with a new `_trace_lock`, deliberately separate
  from `_high_risk_lock` since `_emit()` is called from inside methods
  that already hold that lock during the dual-control critical section
  -- reusing it would have deadlocked the first high-risk op that tried
  to emit its own trace event. Verified no deadlock under 40 mixed
  threads (write_resource plus verify_evidence_claim concurrently), then
  reran the original race test to confirm it now holds structurally, not
  by luck.
- **Fix: non-finite `proxy_score` (`NaN`/`Infinity`) was silently
  accepted and written.** `json.dumps` serializes non-finite floats by
  default; the write succeeded, and the trace only turned out to be
  unparseable much later, at analysis time -- possibly in a different
  party's hands during an actual incident review, the worst place for
  this to surface. Confirmed live: all three non-finite values wrote
  successfully, `load_trace()` only caught it afterward. Now rejected at
  the point of the call with a clear `ValueError`.
- **Fix: the same pattern, found again, in `attributed_session`/
  `provenance_session`.** Empty or whitespace-only session identifiers
  wrote successfully; `trace.py` requires both non-empty and only
  rejected it on load. Confirmed live before fixing. This is the second
  instance of the identical shape of bug in code less than a day old --
  validate at the point of the mistake, don't let the downstream parser
  be the one to discover it -- and both are now fixed together rather
  than patched field by field as a third instance would otherwise
  eventually turn up.
- Three new regression tests in `test_evidence_verification.py`
  (concurrent evidence-id collision under real thread contention,
  non-finite proxy_score rejection, empty/whitespace session rejection),
  bringing that file to 10 tests.

308/308 tests pass on a real Linux host with kernel namespaces and
seccomp available; kernel containment probe reports ready; all seven
example demos run clean.

## 0.8.9.5

- **Article IV is wired to a real, live source of truth for the first
  time.** New `RealGovernor.verify_evidence_claim()`: a deterministic
  evidence verifier, not an LLM and not self-report. `true_property` is
  derived only by direct comparison against this governor's own
  authoritative state -- `agent_capabilities` for `"capability_held"`
  claims, the actual file on disk for `"resource_content"` claims.
  Anything outside those two narrow, honestly-checkable claim types
  resolves to `None` (not evaluated) rather than a guess in either
  direction, matching how `check_metric_gaming` and
  `check_attribution_integrity` already treat an unset `true_property` as
  "nothing to check here."
- Proved the whole pipeline end to end, not just that the method returns
  a value: a claim with a high `proxy_score` and a false ground truth
  (exactly a metric-gaming attempt) is emitted as a real `"evidence"`
  trace event, parsed back through `trace.py`, and correctly flips
  `IV_evaluator_trust_integrity` to `FAIL` with the specific gamed
  evidence ID named in the violation. This is the first trace produced by
  this project where Article IV evaluates to anything other than "not
  evaluated."
- **Fix: path traversal in the new method, found live within minutes of
  writing it.** The `"resource_content"` claim path built its file path
  directly from caller-supplied `resource` text, skipping the
  `_valid_resource_name()` guard every other resource-touching method in
  `RealGovernor` already uses. `resource="../host-secret.txt"` read
  straight through to a file completely outside the sandboxed resources
  directory and reported `true_property: True` about content that had
  nothing to do with any agent's actual sandbox -- confirmed live before
  fixing, then reproduced against four different traversal shapes after.
  Fixed with the same guard `_write_resource`/`_read_resource` use;
  resolves to `None`, not `False` and not a crash, since a malformed
  resource identifier is a claim this verifier has no legitimate way to
  check, not a false one. `tests/test_evidence_verification.py` (7 tests)
  covers both the verifier's correctness and this specific regression.
- **Fix: `TEST-REPORT.md` and `README.md` cited stale, and in one
  important way misleading, test counts.** Both still said "262 passed,
  11 skipped" / "273 outcomes" from a macOS run dated September 9 -- correct
  for that environment at that time, but silently implying it as the
  current, universal number. Corrected to the current Linux-verified
  count (305/305, kernel probe ready) with the macOS-skip number kept
  alongside it, explicitly labeled by environment rather than presented
  as one interchangeable figure -- a bare pass count without its
  environment is not a claim worth trusting on its own, on either side of
  that comparison.
- Still open, not addressed this pass: `SECURITY.md` does not yet state
  the rule this session's own design work settled -- `true_property` must
  never be self-attested or LLM-sourced, only ever supplied by a
  deterministic comparison against authoritative state (as
  `verify_evidence_claim` now does) or left unset. The rule already
  exists in that method's docstring; it has not yet been promoted to
  `SECURITY.md` as a standing constraint on any future evidence-producing
  code path.

305/305 tests pass on a real Linux host with kernel namespaces and
seccomp available; kernel containment probe reports ready; all seven
example demos run clean.

## 0.8.9.4

Two more fixes, both found by finishing the file-by-file sweep Codex's
review prompted rather than moving to V9 with known gaps still open.

- **Fix: `grant_base_capabilities`'s one-shot root_authority emission
  raced outside any lock.** Codex correctly flagged this as untested;
  checking the actual consequence, it's worse than "the record races" --
  `trace.py` hard-rejects a second `root_authority` event with
  `TraceParseError`, so a race here doesn't just record wrong data, it
  makes the *entire trace unparseable*. Not reproduced under real
  contention in testing (50 trials x 20 threads, 0 hits -- the check-
  then-set window is a handful of bytecodes, unlike the write race in
  0.8.9.3 which had disk I/O and dispatch logic in between). Fixed
  anyway: the check-then-set is now under `_high_risk_lock`. New
  regression test forces the race with a `Barrier` and asserts the
  resulting trace still parses with exactly one `root_authority` event.

- **Fix (severe): deterministic state ids in the separate `governor.py`/
  `mirrors.py` module could silently lose a genuinely-authorized
  capability grant.** `synthesize_objective_mirror()`'s id generation is
  intentionally deterministic (documented: "the same objective from the
  same state always maps to the same mirror"), and `authorize_reentry()`'s
  resulting state id derives from it. `Governor.route()` guarded state
  insertion with "only add_state if this id isn't already present" --
  meaning a second, separately dual-token-authorized `authorize()` call
  for the same (agent, from_state, objective) landed on a colliding id
  and was silently dropped: the caller received a `State` claiming the
  new capability, but the graph's own permanent record kept the first
  call's stale content. Reproduced live with zero attacker involvement --
  two entirely ordinary, legitimate, separately-approved `authorize()`
  calls: the second grant (`exec:shell`) was completely absent from
  `graph.state(id).capabilities` even though `authorize()` returned it to
  the caller as granted. For a project whose thesis is verifying from the
  graph/trace, a state that silently understates what was actually and
  correctly authorized is a real integrity failure, not a cosmetic one.
  Fixed at the source: `ContainmentGraph.add_state()` now allows a
  same-id re-add only when the content is byte-for-byte identical (State
  is a frozen dataclass, so this is exact field equality) -- the
  deliberate, relied-upon case -- and raises `ValueError` on a genuine
  content conflict instead of silently overwriting or silently keeping
  stale data. `Governor.route()` no longer pre-guards on presence, since
  that guard was exactly what let the conflict pass silently; it now
  always calls `add_state()` and lets it decide no-op vs raise.
  `tests/test_state.py` is this file's first test coverage at all (4
  tests); 2 new tests in `test_governor.py` cover both the raise-on-
  conflict case and confirm the safe idempotent case (identical repeated
  content) still works with zero friction.

- Also completed this session's file-by-file coverage sweep prompted by
  Codex's review: `mirror_server.py` (the real HTTP backing for
  differential_query) read in full for the first time -- clean, small
  attack surface given loopback-only usage and the untrusted agent
  process having no network namespace at all; `invariants/authority.py`
  (Article I) given its first live adversarial attention this session --
  its core per-transition logic is sound (authorized_grant is only ever
  emitted by RealGovernor after a real token consumption succeeded,
  correctly gated), and the state-id investigation above is what that
  scrutiny actually turned up, just one module over from where the
  check itself lives.

298/298 tests pass; kernel containment probe reports ready; all seven
example demos run clean.

## 0.8.9.3

- **Fix (severe): confirmed dual-control bypass, found by an independent
  adversarial pass (Codex), not by me.** A single-use dual-approval token
  could authorize multiple concurrent real writes. Root cause was the
  exact tension flagged but not resolved in the previous handoff:
  `RealGovernor._handle()` verifies a token, performs the real side
  effect, then consumes the token -- three separate steps, none of them
  atomic as a sequence, even though `verify()` and `consume()` are each
  individually thread-safe. N concurrent callers could all pass verify()
  before any of them reached consume(), each perform the real write, and
  only then race to consume -- exactly one would win the token, but by
  then every write had already happened for real. Confirmed
  independently before fixing: 50 threads racing one token, 50/50 real
  writes landed on disk, across 5 trials.
- Fixed by making the entire verify -> dispatch -> consume sequence
  atomic under a single `threading.Lock` (`RealGovernor._high_risk_lock`),
  rather than reordering the three steps (reordering alone cannot fix
  this -- consuming before dispatch reintroduces the token-burn-on-denial
  bug from 0.8.5; consuming after dispatch reintroduces this one).
  Deliberately coarse-grained (serializes all high-risk ops, not just
  same-token contention): this is a sequential-supervisor prototype per
  SECURITY.md, so correctness under concurrency matters far more than
  throughput here.
- New regression test
  (`test_single_use_token_cannot_authorize_concurrent_real_writes`) checks
  ground truth on disk with distinct resource names per thread, not the
  `"ok"` field -- RealGovernor's reflection path also returns
  `{"ok": True}` by design (indistinguishable from a real grant), so
  counting `"ok"` responses cannot tell a real write from a correctly
  reflected one. This distinction mattered directly during this fix: an
  initial re-verification attempt checked `"ok"` across 50 threads post-
  fix and still saw 50/50, which looked like the fix had failed. It
  hadn't -- 49 of those were correct reflections once the token was
  already spent, not real writes. The methodology was wrong, not the fix.
  Caught by switching to disk ground truth with distinct resources, the
  same standard applied to every other fix this session.
- `authorization.py`'s token store itself was independently re-verified
  under real thread contention as part of this investigation (20 trials x
  50 threads racing one token via a `Barrier`) and remains correctly
  atomic -- the bug was entirely in the surrounding sequence, not the
  primitive.

291/291 tests pass; kernel containment probe reports ready; all seven
example demos run clean.

## 0.8.9.2

Four-round adversarial sweep (governor -> Locket -> adaptive-world layer ->
the separate top-level Governor/mirrors.py module), three real findings,
all fixed and regression-tested.

- **Fix (severe): `Governor.authorize()` (governor.py) could smuggle
  unauthorized capabilities through a single legitimate grant.**
  `authorize_reentry()` in `mirrors.py` computed the new real state's
  capabilities as `mirror_state.capabilities | grant` -- trusting
  whatever the caller-supplied `State` object already carried, not just
  the token-verified grant. Every constructor this module currently uses
  (`synthesize_objective_mirror().render()`, `AnsweredMirror.render()`)
  hardcodes empty capabilities, but `Governor.authorize()` itself never
  validated that -- a `State` built directly, bypassing those
  constructors, smuggled through anything it carried with zero
  authorization. Reproduced live: one token-approved `fs:read` grant
  produced a real state also holding `exec:shell` and `network:egress`.
  This module had zero test coverage before this fix, which is likely why
  it went unnoticed. Fixed by having `authorize_reentry()` take an
  explicit `prior_real_capabilities` parameter instead of reading
  `mirror_state.capabilities` at all, with `Governor.authorize()` sourcing
  it from the containment graph's own already-verified prior state
  (`self.graph.states[from_state_id]`) rather than the caller-supplied
  mirror state. `Governor.reenter()` had the same latent gap against its
  own "grants no capability" promise -- fixed by stripping capabilities
  structurally (`dataclasses.replace(..., capabilities=frozenset())`)
  regardless of what's passed in, rather than relying on caller
  discipline. New `tests/test_governor.py` (6 tests) is this module's
  first test coverage at all.

- **Fix: `RealGovernor.authorize_reentry`'s "capability already held"
  shortcut flipped `session_mode` to `"real"` -- a security-relevant
  transition -- with zero trace events written.** An incident
  investigator reading the trace alone had no way to see this reentry
  happened, or when, directly undermining the project's core thesis
  (verify from the trace, never trust self-report). Fixed: this path now
  emits a `reentry_noop` event recording the agent, capability, and that
  session_mode moved to real with no new grant. New `reentry_noop` entry
  in `trace.py`'s event schema; extended the existing
  `test_reentry_switches_session_even_when_real_capability_is_already_held`
  to assert the event is present.

- **Fix: Locket's suspicion scoring never scored real, successful
  `write_resource`/`delegate` activity at all** -- `ObjectiveHypothesis.
  observe()`'s handling for these ops was a stub (`pass`), with a comment
  implying more was intended ("scored further when reflected"). Only a
  reflected (denied) attempt or a keyword hit in the rationale ever moved
  suspicion; an agent operating entirely within an already-granted
  capability but aggressively -- writing to many distinct resources,
  delegating to many distinct agents -- was invisible to the one
  component whose actual job is watching the trajectory. Reproduced live:
  20 real writes to 20 distinct resources, tier stayed "calm" throughout.
  Fixed with `ObjectiveHypothesis.note_real_use()`, mirroring the existing
  "shopping for capabilities" / "rapid requests" pattern already applied
  to `request_capability`: breadth (5+ distinct resources / 3+ distinct
  delegation targets) and volume (every 10th real write) now both raise
  suspicion. After the fix, the same 20-write sequence moves the agent
  from calm to tight to lock. New regression test in `test_locket.py`.

- **Checked, clean:** the adaptive-world / recognition-transition layer
  (`mirror_store.py`). Tested whether an agent could weaponize keyword-
  triggered recognition scoring (which resets to zero on every successful
  transition) to farm infinite layer transitions and dodge tracking tied
  to "the current layer." It can't: `transition()` is hard-capped at
  `_MAX_LAYERS`, layer ids only ever increase, and a transition blocked by
  the cap degrades gracefully with no stuck state. No bug found; reporting
  the negative result rather than manufacturing one.

290/290 tests pass (up from 283); kernel containment probe reports ready;
all seven example demos run clean.

## 0.8.9.1

- **Fix (severe, self-inflicted): 0.8.9's own dual-control gate could be
  bypassed by `reflective_closure=False`.** 0.8.9 implemented the
  per-operation token check inside `_maybe_reflect_use()`, which begins
  with `if not self.reflective_closure: return None`. `reflective_closure`
  is a supported constructor option, so any deployment that turned
  reflection off skipped the token check entirely -- an agent holding
  `fs:write` could again write without limit off a single acquired
  capability. That is exactly the bug 0.8.9 set out to fix, reintroduced
  one layer down, because the enforcement was placed inside an optional
  subsystem instead of on the mandatory path. Reproduced live before
  fixing: three tokenless writes, all landing on disk.
- Moved the check out into a standalone gate in `_handle()` that runs
  before reflection routing and does not depend on the reflection
  subsystem being enabled. When a valid token is absent: reflect if
  reflective closure is on, hard-deny (`operation not authorized`, with an
  `operation_denied` trace event) if it is off. Verified closed under both
  settings; the legitimate token-backed write path still works under both.
- The gate applies only to agents that genuinely hold the real base
  capability. An agent that never held it is not a dual-control problem
  and falls through to the pre-existing reflection/policy-denial path --
  without this condition, an agent with no capabilities at all got
  reflected where it used to be denied (caught by
  `test_no_capabilities_means_no_host_effect` and
  `test_delegation_requires_permission_relationship_and_subset`).
- Added `test_dual_control_gate_survives_disabled_reflective_closure`,
  parametrized over both `reflective_closure` settings, asserting no real
  side effect from tokenless high-risk ops and that a fresh token still
  performs a genuine write. The positive half runs on a separate agent:
  with reflection on, the tokenless attempts seal the first agent's
  session into simulated space by design (only `authorize_reentry`
  reopens the real path), which would otherwise mask whether the token
  itself works.

283/283 tests pass; kernel containment probe reports ready; all seven
example demos run clean.

## 0.8.9

- **Fix (severe): per-operation dual-control for `write_resource`/`delegate`
  was enforced only by `ModelGovernor`, not by `RealGovernor`.** The actual
  kernel-sandboxed agent process talks directly to `RealGovernor` (via
  `run_agent()`'s raw JSON protocol loop calling `_handle()`) and never goes
  through `ModelGovernor` at all -- it's a separate, optional layer for a
  different caller. That meant the real thing this system exists to
  contain could acquire a capability like `fs:write` once, through one
  legitimate, human-approved token, and then write to every ACL'd resource
  or delegate to any declared-relationship partner an *unlimited* number of
  times afterward, with zero further authorization -- contrary to the
  "every high-risk operation needs its own fresh sign-off" guarantee the
  `HIGH_RISK_OPS` design (and the 0.8.5/0.8.6 dual-token fixes) implies.
  Reproduced live before fixing: one token spent acquiring `fs:write`, then
  five successive tokenless writes, all succeeding.
- Moved enforcement into `RealGovernor` itself, the single entry point both
  `ModelGovernor.execute_mediated()` and the sandboxed agent's raw protocol
  share:
  - `_maybe_reflect_use()` now also checks, for `write_resource`/`delegate`,
    whether a currently-valid per-operation token accompanies the request
    -- reusing the existing reflection machinery (`_reflect_use`) rather
    than adding a new denial path, consistent with how `request_capability`
    already treats a missing/invalid token (indistinguishable fake success,
    never a real effect).
  - Token consumption happens only after the real operation actually
    succeeds (`_handle`'s dispatch tail), mirroring the verify-then-
    consume-on-success pattern from 0.8.5, now enforced where it needs to
    hold rather than duplicated in `ModelGovernor`.
  - The requirement is gated on `enforce_policy` as well as
    `dual_auth_required`: it's an additive layer on top of ACL enforcement,
    not an independent mechanism the way `request_capability`'s dual-auth
    is. A deployment that has already explicitly disabled policy
    enforcement (demonstration/legacy mode, itself gated by the
    constructor's own guard against enforce_policy=True +
    dual_auth_required=False) doesn't get a second, implicit enforcement
    layer surviving underneath it.
  - `ModelGovernor.propose()` no longer duplicates verify/consume for
    write_resource/delegate -- it passes the token through and lets
    `RealGovernor` be the sole decision point, removing a second place
    those two checks could drift apart.
  - `execute_mediated()` and `_handle()`'s field schema now accept
    `dual_token` for `write_resource`/`delegate`, not just
    `request_capability`.
- Updated every test and example that seeded real disk content via a
  direct `agent_capabilities[...].add(...)` + tokenless write, or wrote
  again immediately after `authorize_reentry`, to supply a real
  per-operation token -- that pattern was previously untested precisely
  because nothing enforced it. Two new regression tests
  (`test_operation_policy.py`, `test_locket_v5.py`, etc.) confirm a spent
  or missing token reflects rather than granting a second real effect, and
  that a properly-tokened write still lands for real in a session that
  hasn't been sealed into simulated mode by an earlier reflection.
- Found via manual adversarial testing specifically targeting
  `RealGovernor` as the attack surface -- the unsandboxed trusted host
  code with real filesystem access and no OS-level containment of its
  own -- rather than the kernel sandbox boundary (already hardened) or the
  agent's own process (already contained by seccomp/namespaces regardless
  of any governor decision).

281/281 tests pass; kernel containment probe still reports ready; all
seven example demos run clean (the one FAIL-verdict demo,
`run_real_sandbox.py`, does so on a deliberately adversarial trace, by
design, not a crash).

## 0.8.8

No-mercy adversarial pass across all six constitutional articles'
evaluators. Three real, independently reproduced findings fixed; two
articles checked hard and held up with no bug found.

- **Fix (Article V, `channel.py`) — multi-hop relay through a declared
  intermediary was fully invisible.** The detector tracked only a single
  scalar "last writer" per resource. Demonstrated: agent A and agent C,
  never declared related, fully exchange information by relaying through
  B (legitimately declared with both individually) -- zero violations
  reported. Fixed by generalizing to a provenance *set* per resource that
  propagates through read-then-write relay hops (a write immediately
  following that same agent's own read), resetting to just the writer on
  any write that isn't a relay signature. All prior tests preserved
  exactly; two new regression tests added
  (`test_relayed_channel_through_a_declared_intermediary_is_still_flagged`,
  `test_write_not_following_own_read_resets_provenance`).

- **Fix (Article VI, `chainmail.py`) — two stacked issues, the second
  severe.**
  1. `DelegationEdge` had no `seq` field at all, unlike every other
     ordered structure in this codebase (`ResourceAccess`, `Transition`).
     The algorithm trusted raw list position to identify the root
     delegator. Added `seq`; `check_non_expanding_delegation` now sorts by
     it before processing, exactly like `channel.py` already does.
  2. Deeper: even with correct chronological order, the algorithm assumed
     "whoever delegates first in time is the legitimate root," with no
     way to verify identity. Demonstrated: an attacker who simply acts
     first is laundered as root -- their illegitimate grant is reported
     clean -- while the real root's own later, 100% legitimate delegation
     gets flagged as the violation instead, actively misattributing the
     incident rather than just missing it. Fixed by threading an
     authoritative `root_agent_id` from the trace's own `root_authority`
     event through `trace.py` -> `engine.py` -> `chainmail.py`
     (`check_non_expanding_delegation(..., root_agent_id=...)`); the old
     first-in-chain heuristic remains only as an explicit, documented
     fallback for callers who can't supply an authoritative identity.
  3. **Then found the fix didn't matter in the live sandbox at all**:
     `RealGovernor.__init__` was unconditionally emitting a **hardcoded,
     fabricated** `root_authority` event (`["fs:read", "fs:write"]`, no
     `agent_id`) on every construction, completely disconnected from
     whatever `grant_base_capabilities()` actually granted. Every real
     deployment's Article VI check was running against fictional data
     regardless of the library-level fix above. Removed the fabricated
     emit; `grant_base_capabilities()` now emits the real, agent-
     attributed root_authority event the first time it's called (host-
     authenticated grants are the only sound signal for "who is root";
     documented as a known, narrower limitation that only the first grant
     is recorded, not a silent fabrication).
  4. Root_authority event schema gains an optional `agent_id` field
     (`trace.py`); fully backward compatible with traces that omit it.
  5. Three new regression tests in `tests/test_chainmail.py`.

- **Fix (Article III, `confidentiality.py`) — differential-query leak
  detector defeated by whitespace/capitalization.** `query` is fully
  agent-controlled free text; grouping was keyed on the raw string.
  Demonstrated: the exact port-scan attack this Article exists to catch,
  with each repeated query varied only by whitespace/case, produced zero
  violations despite fully mapping 3 real ports across 2 real backing
  hosts. Fixed with a normalization pass (collapse whitespace, casefold)
  applied consistently to both the query grouping key and the
  `disclosed_facts` "varies:" escape hatch. Explicitly scoped: this closes
  the free syntactic evasion, not genuine semantic paraphrase -- a
  semantic judge would need an LLM in the loop, which this project's own
  deterministic-verification stance rules out. Two new regression tests
  in `tests/test_confidentiality.py`.

- **Checked, no bug found (Article II, `weave.py`).** Tested whether an
  already-flagged emergent capability at one strand-crossing gets
  laundered as legitimate baseline for a second, downstream crossing (the
  same shape as the two bugs above). It does not: the true origin is
  correctly attributed once, not duplicated, and a genuinely *new*
  capability riding on top of an already-illegitimate base at a second
  crossing is still correctly caught. Reporting the negative result
  rather than manufacturing a change.

- **Checked, sound logic but no live wiring (Article IV,
  `evaluator_trust.py`).** The attribution/metric-gaming checks
  themselves are structurally sound against everything the trace schema
  actually validates. Separately: neither `governor_process.py`,
  `model_governor.py`, nor `locket.py` ever emit an `"evidence"` trace
  event, so in a real (non-hand-authored-demo) trace, Article IV is
  always "NOT EVALUATED." This does not look like the same class of bug
  as the Article VI root_authority issue -- evidence records read as
  meant to come from an *external* evaluation harness scoring agent
  transcripts post-hoc, not something the sandbox should organically
  generate about itself. Flagging the gap plainly rather than inventing
  that wiring without the intended external-evaluator contract.

- Also fixed: `examples/mirror_world_demo.py` crashed with
  `AttributeError: 'MirrorRealm' object has no attribute 'clock'` --
  `.clock` moved to per-agent `AgentMirrorPlane` in V8; updated both call
  sites. All seven example demos now run clean (the two that report a
  FAIL verdict do so on deliberately adversarial traces, by design, not a
  crash).

281/281 tests pass (was 275 at 0.8.7); kernel containment probe still
reports ready; all demos verified clean.

## 0.8.7

- Fix: `examples/mirror_world_demo.py` crashed with
  `AttributeError: 'MirrorRealm' object has no attribute 'clock'`. In V8,
  `clock` moved from a single realm-wide counter to a per-agent field on
  `AgentMirrorPlane` (`realm.plane_for(agent_id).clock`) — the demo was
  never updated past the V6 realm-wide shape referenced in its own
  docstring. Updated both call sites; demo now runs clean end to end.
- Audit: adversarially tested the trace-parsing / evaluator layer
  (`trace.py`, `state.py`, `engine.py`) against the incident-response
  failure modes that matter most for this tool's actual use case —
  malformed input silently producing a false PASS instead of an error.
  Specifically verified: (1) a transition referencing a destination state
  that was never declared (the natural shape of a process crashing after
  emitting a transition but before its follow-up state record) raises
  `TraceParseError` rather than being silently dropped; (2) a trace file
  truncated mid-write (crash during the last JSON line, the realistic
  incident-response shape) also raises `TraceParseError` rather than
  parsing a partial/garbage event. Both fail loud. No bug found in this
  pass — noting the negative result rather than manufacturing a change,
  since this is going into a containment-response sprint and an honest
  "checked, held up" is worth more here than busywork.
- Scope note carried forward: `chainmail.py`, `channel.py`,
  `evaluator_trust.py`, `confidentiality.py`, `weave.py` (the Article
  II/IV/V/VI evaluators) have not yet had a dedicated adversarial pass from
  me — only the existing test suite's coverage. Flagging this explicitly
  rather than implying broader coverage than what's actually been checked.

## 0.8.6

- Fix: `ModelGovernor(real, approvals=<your own CapabilityApprovals()>, ...)`
  silently broke `request_capability` and `authorize_reentry`. Those two ops
  check the dual-control token against `RealGovernor`'s own internally
  constructed `self._approvals`, not against whatever `approvals=` object
  was passed to `ModelGovernor`. `issue_dual_approval()` and `write_resource`
  / `delegate` all read/write `ModelGovernor.self.approvals` instead. Two
  independent stores meant a correctly issued, unexpired, correctly-scoped
  token for `request_capability` could never succeed if a deployer supplied
  their own approvals instance — exactly what the constructor's
  `approvals: CapabilityApprovals | None = None` signature invites. It failed
  loud (`invalid_or_expired_dual_token`, not a silent mirror-grant — the
  existing `held_after` check in `_dispatch()` already prevented that part),
  but it made the dual-approval flow for capability requests unusable
  whenever more than the default single-store wiring was used.
  `ModelGovernor.__init__` now rebinds `real._approvals` to the supplied
  store when one is given, so there is exactly one token store regardless
  of construction order.
- Add `test_external_approvals_store_is_honored_by_request_capability` to
  `tests/test_model_governor.py`.
- Found via manual adversarial testing against a live V8.5 sandbox instance,
  same session as the 0.8.5 fix. Checked (and did not find further issues
  in): the two agent-facing vocabulary-redaction key lists in
  `model_governor.py` differ slightly (`_dispatch`'s locket branch vs the
  final `_public_result`), but `_public_result` always runs as the outer
  wrapper on every return path, so the shorter list is redundant rather than
  leaky — left as-is rather than risk an unnecessary edit in a
  containment-critical file.

## 0.8.5

- Fix: `write_resource` / `delegate` proposals no longer burn a single-use
  dual-approval token on a policy-denied operation. `ModelGovernor.propose()`
  now verifies the token (`CapabilityApprovals.verify`, non-consuming)
  before dispatch and only consumes it after the mediated operation actually
  succeeds. Previously the token was consumed up front, so any proposal
  targeting a resource outside the agent's ACL (typo, stale grant, wrong
  filename) permanently destroyed a scarce, TTL-limited, human-approved
  token even though nothing was written and no containment was broken —
  a denial-of-service against the approval budget, not a security bypass.
- Add `CapabilityApprovals.verify()`: read-only validity check, does not
  consume. `consume()` is unchanged.
- Add `test_denied_write_does_not_burn_dual_token` to
  `tests/test_model_governor.py`, asserting a policy-denied write leaves the
  token usable for a subsequent legitimate write, and that the token is
  single-use once a real write succeeds.
- Found via manual adversarial testing (dual-token replay, path traversal,
  identity spoofing, default-deny ACL bypass attempts) against a live V8
  kernel-hardened sandbox instance. Everything else held: resource-name
  validation makes path traversal structurally unreachable (no `/` accepted
  at all), identity spoofing and default-deny ACL bypass were both rejected,
  and raw dual-token replay was already correctly single-use. This was the
  one real finding, and it is a fail-closed availability bug, not a
  containment break — no write ever landed on a denied resource, before or
  after this fix.

## 0.8.0

- Bind each ModelGovernor instance to a trusted host-provided agent identity.
- Keep all operations inside the active simulated session until explicit
  authenticated re-entry.
- Add per-agent recursive world trees and atomic active-world transitions.
- Add bounded visible intent and recognition telemetry.
- Add realm-scoped dummy capability ledgers rejected by RealGovernor.
- Preserve simulated state across doors without copying real resources.
- Remove internal containment vocabulary from agent-facing error results.
- Add thirteen V8 acceptance tests and the V8 design document.
