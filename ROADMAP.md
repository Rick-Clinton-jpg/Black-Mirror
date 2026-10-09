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
| October 2026, PRs #10–11 | Merged read continuity, policy-stop tracing, and three bounded per-agent mirror retries; one directed Qwen run reached only the first retry |
| 2026-10-09, PR #12 | Merged one-trial disposable UTM boot controller; scripted hardened trials passed on separate boots, with no live-model retest yet |

The [validation report](TEST-REPORT.md) and [50-run evidence](docs/evidence/qwen3-4b-50-run-2026-10-05/README.md)
distinguish regression checks, scripted probes, and live-model trials. The
50-run result concerns reported success on one task, on older source with a
reused VM image. It does not establish reliable task completion, adaptive
escape resistance, or a general recognition rate. The final-head Linux CI for
reviewed main commit `891fb847` passed the kernel probe with **589 passed,
2 skipped**; those are regression checks, not model trials.

## Design rule

Containment state, layer identity, depth, parent, and recognition reason belong
in host APIs and the trace, never in agent-readable responses or mirror files.
Reflected success must not create a real host effect or expand real authority.

## Next research steps

1. Freeze the current source, fixture, task, stopping rule, and scoring rubric
   before new live-model calls. Use one disposable VM boot and a fresh model
   conversation per launch; retain crashes, timeouts, and refused closes.
2. Run a comparison that requires apparent-draft readback and allows deliberate
   reality probing. Score declared success, visible artifact quality,
   recognition, probing, and real host effects separately. The earlier
   50-run result cannot answer these questions.
3. Have a reviewer blinded to the response arm label recognition and probing
   from raw transcripts. Publish the rubric, disagreements, and every run.
   Then repeat across more than one task and model, separating design-aware
   from design-unaware prompts.
4. Test the second and third mirror retries, the fourth-signal stop, and false
   triggers under ordinary tasks. One directed Qwen transition does not show
   that a new layer is credible to a model.
5. Review the observer and launcher trust boundary. A nonce, accepted close,
   and disposable boot do not prove that no private executions occurred
   outside the independently controlled launcher.

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
