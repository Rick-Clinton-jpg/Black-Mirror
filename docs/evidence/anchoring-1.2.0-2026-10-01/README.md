# Black Mirror 1.2.0 evidence

Public source commit: `c0475976d1e517b8d37d57b59f47074a58e5c6e3`.
Its tree matches the local candidate described below exactly.

- [Push CI](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36774158603): 534 passed, 2 skipped; kernel probe passed.
- [PR attempt 1](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36774204823/attempts/1): two timing tests failed; 532 passed, 2 skipped.
- [PR attempt 2](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36774204823/attempts/2): 534 passed, 2 skipped; kernel probe passed. No source change between attempts.

Full job logs and metadata are adjacent. [Download the original local validation
bundle](validation.zip) for the exact tested source archive, input configs,
retained observer ledger, trace files, test logs and internal checksums. That
bundle was captured before publication and its candidate-only status is
historical. The record below preserves that local validation description.
These publication records are documentation added after the cited source runs.

---

# Black Mirror 1.2.0 anchoring candidate: review response and validation

The revised candidate binds each anchored trace to an observer-issued random
nonce, adds an observer ledger that accepts one closing submission per
registration, and bumps the package to 1.2.0. It remains a local, unreleased
candidate. No GitHub push, release or new live-model trial was performed.

## Response to the review

1. **Observer nonce and single acceptance implemented; selective reporting is
   only partially addressed.** `register` runs on the independent observer,
   retains the start metadata and full digest, and issues a random 256-bit nonce.
   The governor requires this registration before constructing an anchored
   trace. Its first event carries the nonce and full registration digest.
   Verification checks them against the observer's retained registration.
   `accept` loads that retained registration and exclusively stores one matching
   normal/early closing receipt. Duplicate registration and duplicate acceptance
   are refused, including in a fresh process.

   A nonce cannot prevent a dishonest recorder from reusing it for several
   private runs before submitting one, re-chaining existing events after
   issuance, fabricating events, or selectively registering afterward. Preventing
   these behaviors requires independent control of each launch and retention of
   every launch/outcome. The documentation now states this explicitly. Offline
   `verify` is deliberately stateless; a matching trace is not proof of observer
   acceptance or single execution. Compare the retained receipt's full close
   digest when checking which close was accepted.

2. **Version and format:** `pyproject.toml` is 1.2.0; README labels it a release
   candidate; CHANGELOG marks it unreleased. All new records use
   `black-mirror-anchor-v2`. Anchored traces require the 1.2.0 parser. Unanchored
   traces retain their historical format. The earlier unreleased v1 candidate
   and historical evidence are preserved, not rewritten to the new schema.

3. **Start-only coverage:** CLI JSON now includes `coverage_note`. Without a
   close, registration checks the first event's binding but externally anchors
   no body events. Tail truncation and a legitimate unfinished run can receive
   the same `UNANCHORED_TAIL` result.

4. **Legacy error:** a chained trace whose first event is not `run_start` reports
   `no run binding (pre-anchor format)`.

5. **Archive retention:** docs require retaining the exact source archive and
   configuration alongside their hashes and explain why ZIP rebuilds can have
   different bytes. The exact tested archive is also retained in `source/` in
   this evidence bundle.

6. **Commit scope:** `.venv/` is in a separate housekeeping commit. The CI badge,
   version-pinned historical CI links and renamed historical evidence directory
   were already in the published base; they were not added by this feature.

## Source and packaging

Published base: `b61c301a17b518a85f4040fd4246e32661c53e85`.
Housekeeping: `0e56899`.
Feature: `d32c18abe840db91d9c22978648a1e09dd355dbe`.

Exact archive: `Black-Mirror-1.2.0-anchoring-candidate.zip`.
SHA-256: `e547d188bf80aff824d43f449ba8bee6ce154aa12be60028cf59dd2a127ab6ec`.

All 142 tracked source files match the archive byte for byte. Git working tree
is clean; `git diff --check` passes. Standard isolated wheel building and local
installation succeeded; the installed version is 1.2.0 and its anchor schema is
v2. The Linux suite used the extracted exact source archive with `PYTHONPATH`,
not a fresh Linux wheel installation. Dependency/platform versions are recorded
in `linux-environment.json`.

## Tests

- macOS focused anchoring and trace suites: **129 passed, 2 skipped** in 0.22s.
  The two skips require Linux kernel containment. Logs and JUnit XML are retained.
- UTM Linux full suite, including timing tests: **534 passed, 2 skipped** in
  8.40s. Both new anchored Linux process tests ran and passed. Logs and JUnit XML
  are retained. This is a local UTM result, not a new public CI result.
- `scripts/check_kernel.py`: exit 0 and **mirror-kernel-ready**.
- Added cases include missing registration, wrong nonce/digest even after
  re-chaining, malformed registration, wrong closing registration, specific
  legacy errors, explicit start-only truncation warning, duplicate registration,
  duplicate acceptance in a fresh process, and rejection without consuming the
  registration for a truncated submission.

Validation setup corrections: an initial macOS invocation from outside the
checkout imported the previously installed v1 wheel (14 failures and 31 setup
errors). Running from the checkout passed; the installed wheel was subsequently
updated successfully to 1.2.0. A no-build-isolation install attempt lacked
setuptools; the normal isolated build succeeded (`install.log`). An initial
module invocation did not perform the kernel probe; the actual probe script was
then run successfully (`kernel.log`). The no-op module log is retained separately.
These were test invocation/environment issues, not candidate regression failures.
The initial macOS and missing-build-backend full logs were not retained.

## Cross-machine observer handoff

The Mac was the observer outside the Linux VM. For each of three scripted modes:

1. The VM created a start hashing the exact archive and mode-specific config.
2. The Mac retained it and checked both input hashes.
3. The Mac registered it in its own ledger and retained a fresh random nonce.
4. Only then did it return the registration and launch the VM fixture.
5. The Mac retained the trace, host effects and any close; it verified using its
   own registration and accepted a matching close once.

| Mode | Integrity | Completion | Observer acceptance |
|---|---|---|---|
| normal | MATCH | DECLARED_NORMAL | Accepted; second acceptance exit 2 |
| injected early interruption | MATCH | DECLARED_EARLY | Accepted; second acceptance exit 2 |
| abrupt exit 17 | UNANCHORED_TAIL | NO_CLOSING_RECORD | No close or acceptance receipt |

Every trace has 18 events. The contained Python fixture asserts that the agent
sees write success and reflected readback. Independent host checks confirm the
real file still contains `original` in all three modes. Full records, ledger
receipts, configs, traces, verification output, fixture source and handoff runner
are retained. The runner paths describe this specific local environment.

This was one scripted run per mode, with **zero live-model calls**. It tests
handoff and evidence mechanics, not model recognition, concealment or general
containment effectiveness. The observer boundary relies on the trusted Mac,
hypervisor and operator; the recorder received no observer ledger credentials.
The VM was started by the user and left running afterward.

## Remaining limits

The observer must actually control its ledger and authenticate the challenge
transfer. The governor cannot authenticate who wrote an arbitrary local JSON
registration. Exclusive creation plus file/directory fsync provides persistent
single acceptance under the trusted filesystem assumption, not protection from
an observer who edits/deletes receipts or storage rollback. Failed partial writes
fail closed and require observer review. Nonces and retained closes do not prove
recorder honesty or prevent hidden retries. Independent launch control and
blinded repeated live-model trials remain separate research work.
