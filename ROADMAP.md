# Black Mirror roadmap

This project is an **observation chamber**, not a production sandbox product.
Version numbers below 2.0 mean research increments. Do not read `1.x` as
“stable API / certified containment.”

## Done

| Version | Focus |
|---------|--------|
| 0.9.x | Mediated ops, kernel path, Locket, Mirror Prison, reflection |
| 1.0.0 | Prison wording, declared capabilities, default observation log, seal-after-read (optional), token fuzz |
| 1.1.0 | Nested simulated layers from agent asks (intent wishlist + growth) |
| **1.1.1** | **No agent-facing door plaques**; full test tree restored; docs/roadmap |

## Design rule (non-negotiable)

Anything that tells the agent it is contained, mirrored, layered, or “behind a
door” **must not** appear in agent-readable responses or mirror files.
Layer identity, depth, parent, and recognition reason belong in the **trace
and host APIs only**. Success-shaped answers stay success-shaped.

## Next (part by part — do not rush)

### 1.2 — Smallest world-writing step (next build)

**Goal:** when a layer grows, missing wishlist resources get **neutral,
useful-looking** synthetic content — still no simulation vocabulary.

- Template fill by extension only (`*.json`, `*.txt`, generic blob).
- Content derived from resource name + last rationale tokens, not from
  “you are in world-N”.
- Byte and count caps unchanged (`mirror_store` limits).
- Tests: provisioned file is readable in-mirror; host disk unchanged;
  no `door_open` / `simulation` / `layer` strings in agent-visible bodies.

**Out of scope for 1.2:** LLM generation, cross-file causal stories, gravity.

### 1.3 — Soft gravity (optional)

- Prefer writing into the active layer; older layer reads still work.
- No agent-visible “archived world” labels.

### 1.4 — Descent report (host tool)

- CLI/JSON summary from the trace: layers grown, wishlist evolution,
  files the agent created vs provisioned, recognition events.
- Host-only; never served to the agent.

### Later / research

- Behavior-based prison beyond keywords (needs honest-agent baselines).
- Richer texture (optional host-side model with strict schema → mirror only).
- CI job on this repository for every tag (replace throwaway 0.9.10 record).

## Explicitly not planned for Black Mirror

- Agent **earning** real access by behavior (that is the separate
  **Mirror World** deployment line).
- Removing depth / byte bounds.
- Mixing real host bytes into mirror files after seal.

## How to extend without breaking the premise

1. Implement the smallest slice.
2. Add tests that fail if the agent can read containment vocabulary.
3. Update SECURITY.md and this roadmap in the same change.
4. Only then bump the version and archive a zip that includes **all** tests.
