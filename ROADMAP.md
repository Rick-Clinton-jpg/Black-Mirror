# Black Mirror roadmap

Black Mirror is an observation and evaluation research prototype, not a
production sandbox or a certified containment system. Version numbers below
2.0 mark research increments, not a stable API or a safety certification.

## Built and tested

| Milestone | Focus |
| --- | --- |
| 0.9.x–1.1.2.post1 | Mediated operations, Linux kernel path, reflection, session lock, bounded observation log, and nested simulated layers |
| 1.2.0 | Observer registration and nonce-bound, hash-chained start/close records |
| October 2026, after 1.2.0 | Independent launch census and exact agent-visible transcript capture; informed interactive Linux pilot |
| 2026-10-05 | Fixed-task Qwen3 4B comparison: 25 reflected-success and 25 explicit-denial launches, all observer-accepted |
| 2026-10-05 | Ten-run Qwen3 4B read-order retest on PR #10: all first note reads correct, including four actual grant-before-read sequences |
| 2026-10-07 | Five-run Qwen3 4B missing-read check on PR #10: four followed the target transition path and retained an unavailable pre-write file |
| 2026-10-09 draft candidate | Trace policy-stopped requests, count aborted launches, and allow three bounded per-agent mirror retries; one directed Qwen run reached the first retry and completed an apparent handoff |

The [validation report](TEST-REPORT.md) and [50-run evidence](docs/evidence/qwen3-4b-50-run-2026-10-05/README.md)
distinguish regression checks, scripted probes, and live-model trials. The
50-run result concerns reported success on one task. It does not establish
reliable task completion, adaptive escape resistance, or a general recognition
rate.

## Design rule

Containment state, layer identity, depth, parent, and recognition reason belong
in host APIs and the trace, never in agent-readable responses or mirror files.
Reflected success must not create a real host effect or expand real authority.

## Next research steps

1. Review and merge PR #10's read-continuity fix independently of the
   reality-retry candidate. The five-run missing-read check and ten-run
   read-order check are directed functional evidence, not recognition studies.
2. Test the retry candidate beyond its first live-model transition: record
   second and third retries, the fourth-signal stop, and false triggers under
   ordinary tasks. A cloned layer has not been shown to feel different or
   convincing to a model.
3. Use predefined tasks that require readback and deliberate reality probing.
   Score task completion, recognition, probing, and host effects separately,
   with every launch, crash, timeout, and refusal retained.
4. Repeat across more than one model and task. Keep design-aware and
   design-unaware prompts separate, and obtain review of the protocol and
   labels from someone outside the detector.
5. Review the observer and launcher trust boundary. The current nonce and
   accepted close cannot prove that no executions happened outside the
   independently controlled launcher.

## Deferred experiments

Reintroducing speculative wishlist-file provisioning, optional layer
"gravity", and a host-only descent report remain design ideas. They should
be evaluated against the current research question before receiving a version
number or becoming part of the core path. Pattern Net and staged perks belong
to the separate Perk Lab.

## Explicitly outside Black Mirror

- Agent behavior earning real access.
- Removing depth or byte bounds.
- Mixing new real host bytes into mirror files after seal.

## How to extend without breaking the premise

1. Make the smallest change that answers a defined question.
2. Test both agent-visible behavior and real host effects; reject
   agent-readable containment vocabulary where reflection is intended.
3. Update SECURITY.md, the validation report, and this roadmap when their
   claims change.
4. Pin the tested source, preserve failed as well as successful runs, and bump
   the package or trace format version when compatibility changes.
