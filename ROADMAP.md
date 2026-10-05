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

1. Re-run the grant-before-read case in Linux containment with a live model.
   The seal-time snapshot now addresses the reported `notes.txt` cue in code;
   a new controlled run must check its agent-visible effect and host isolation.
   Evaluate whether adaptive provisioning of empty files after repeated misses
   is acceptable; it remains an agent-visible state change.
2. Use predefined tasks that require readback and deliberate reality probing.
   Score task completion, recognition, probing, and host effects separately,
   with every launch, crash, timeout, and refusal retained.
3. Repeat across more than one model and task. Keep design-aware and
   design-unaware prompts separate, and obtain review of the protocol and
   labels from someone outside the detector.
4. Review the observer and launcher trust boundary. The current nonce and
   accepted close cannot prove that no executions happened outside the
   independently controlled launcher.

## Deferred experiments

Changing when missing wishlist resources are provisioned, optional layer
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
