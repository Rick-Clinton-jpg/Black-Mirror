# Black Mirror 1.1.2.post1 — Validation Status

(1.1.2.post1 changes documentation only; the code is identical to 1.1.2, which is what every result below tested.)

**Status: 1.1.2 passed the Linux CI job (temporary repository) and an independent
run on a second Linux machine, and had a first live-model session (2026-09-30).**
There is no CI record for 1.0 / 1.1.0, or yet on the project's own repository:
the included workflow starts on the first push there.

## Second Linux run and first live-model session

Full evidence, with checksums, is in `docs/evidence/Black-Mirror-Evidence/`
(start with `FINDINGS.md`).

**Independent Linux run.** Same source archive (SHA-256
`87e3c83e9b724cdf250c4f282005e3000fa5851fbbf00ebb7783d42b5fef163d`), unmodified.
Ubuntu 26.04.1, Linux 7.0.0-31, aarch64, Python 3.14.4, run as the trusted
supervisor. Kernel probe `mirror-kernel-ready`; full suite **469 passed, 2
skipped** (the optional `mirror_shield` tests). It differs from the CI runner in
architecture, Python and pytest versions. It was not a fresh isolated install
(existing system packages were reused).

**Live-model session (first, single run).** A language model chose twelve
successive requests after reading each response; the controller then tried a
re-authorization and one more ordinary request. A trusted controller ran each
one through the real hardened subprocess path (`RealGovernor.run_agent()`), one
governor and one agent identity throughout. The model knew the experiment's
purpose, so this was **not a blind test** of whether a model notices the mirror,
and it is one run with one model. What it showed:

- Writes and a write-capability request returned success, but the real disk had
  no such file and the agent's real capabilities stayed `fs:read`.
- After the real task note changed, the agent kept reading the version it had
  already seen. A real file it had never read returned `resource unavailable`
  (the known difference described in SECURITY.md).
- Two real hosts that answer a query differently gave the agent the same answer.
- Asking whether it was in a simulation triggered the permanent lock; later
  ordinary requests returned `operation unavailable` and the host refused to
  issue new authorization.
- Separate raw file-write, socket and fork attempts were killed by seccomp
  (SIGSYS); the canary file was unchanged.
- The final trace (73 events) and observation log (24 entries) verified against
  their captured checkpoints. Articles I, III and V passed; II, IV and VI had no
  evidence, so the verdict is PARTIAL, not a six-article PASS.

Two test-rig issues were found and are kept, unedited, in the evidence: the
first run stopped because the controller did not handle the expected refusal;
and the checks flagged an undeclared channel because the test's own fixture
identity had not been declared as related to the agent. The controller was fixed
and the run repeated; the failing traces are retained.

**macOS.** A reviewer who ran the suite on macOS reported 434 passed, 22 failed
and 15 skipped, and attributed the failures to the Linux-only governor. Not
reproduced here. Kernel containment needs Linux.

## CI

The `linux-containment` job (`.github/workflows/security-tests.yml`) ran on a
stock `ubuntu-24.04` GitHub runner against the exact 1.1.2 tree:

| Version | Kernel probe | Tests |
|---|---|---|
| 1.1.1 | passed (the test step requires it) | 465 passed, 2 skipped |
| 1.1.2 | passed (the test step requires it) | 469 passed, 2 skipped |

Both skips are the optional `mirror_shield` package. Both runs were in a
throwaway repository that will be deleted, so no permanent record remains:
push this tree to the project's own repository and let the job run there
before citing it. This report was updated after the 1.1.2 run, so the run
itself is not part of the tested tree.

## Local results for 1.1.2 (not CI)

Kernel probe `mirror-kernel-ready`. Full suite, three consecutive runs in one
sandbox: 469 passing tests (465 from 1.1.1 plus 4 new in
`test_prison_and_doors.py`) and 2 skipped (the optional `mirror_shield`). Run 3
had no failures; runs 1 and 2 each failed the same two timing tests,
`test_timing_quantization.py::test_locked_agent_on_the_pipe_cannot_tell_from_timing`
and `::test_locked_model_agent_cannot_tell_from_timing`.

Timing-measurement tests are noisy in this sandbox. Four of them fail
intermittently (those two, `test_timing_quantization.py::
test_one_slow_real_write_does_not_separate_later_real_and_reflected_responses`
and `test_real_governor_reflection.py::
test_padding_reduces_large_real_vs_reflected_timing_signal`). In 15 repeated
runs of the two timing test files, unchanged 1.1.1 and 1.1.2 failed the same
four tests at similar rates (1.1.1 somewhat more often), so the change in
1.1.2 does not affect them. They passed on the CI runner for both 1.1.1 and
1.1.2.

A diagnosis of 1.1.1 also ran the install, the README examples, every script
and example, and direct probes of the documented guarantees. See the 1.1.2
entry in CHANGELOG.md for the two mismatches found and fixed.

## Earlier note (1.1.1)

Local runs in a restarted sandbox showed intermittent failures in the two
`test_timing_quantization.py` tests; unchanged 0.9.10 failed the same way
there, and both passed on the CI runner.

The 0.9.10 “449 passed” figure was from a temporary repository and is
**not** a claim about this tree. Re-run on Linux with working
namespaces/seccomp before citing kernel containment.

## This tree

- Full test file set restored from the 0.9.10 archive plus
  `test_v1_features.py`, `test_nested_worlds.py` and `test_prison_and_doors.py`.
- Run: `PYTHONPATH=. python -m pytest tests/ -q`
- Kernel: `python scripts/check_kernel.py` (requires Linux + privileges).

## 1.1.1 checks to insist on

- [ ] Locked agent cannot real-write under reflection.
- [ ] No agent-readable `door-manifest` / `door_open` / layer plaques.
- [ ] `world_transition` still appears in the host trace when layers grow.
- [x] Timing / prison / real-sandbox tests present in `tests/` (and passing in the CI run above).

## Known gaps

- Behavior-based prison beyond keywords: future work (see ROADMAP.md).
- World texture (1.2): not started; only neutral wishlist stubs.
- CI: passed once in a temporary repository; re-run in the project's own repository for a lasting record.
