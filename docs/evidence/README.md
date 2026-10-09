# Black Mirror Evidence

The [Black Mirror Evidence bundle](Black-Mirror-Evidence/FINDINGS.md) contains the independent Linux validation and live-model containment session recorded on 2026-09-30.

The bundle retains the original reports, runner attribution, raw traces, and checksums. Start with `FINDINGS.md`; `SHA256SUMS.json` covers the original evidence files, using paths relative to the bundle folder.

[The VM-local Qwen open-code trial](qwen-vm-native-2026-10-09/README.md) records
three registered attempts, including an OOM abort and a worker-protocol
failure. Its one completed model sequence exposed a malformed-request gap in
the hash-chained trace. The exact exchanges, host checks, source variants,
verification script, and original checksummed ZIP are retained.

[The 50-run Qwen3 4B trial](qwen3-4b-50-run-2026-10-05/README.md) compares
ordinary denial with reflected success under the hardened Linux path. Its
protocol, per-run scores, exact model exchanges, host checks, and full
checksummed evidence archive are retained together.

[Publication validation](post1-publication-2026-09-30/README.md) records the post1 rerun and the first successful CI run in Black-Mirror itself. Statements inside the original bundle describe the repository state when that evidence was collected.

[The informed interactive Linux pilot](live-interactive-pilot-2026-10-03/README.md)
records one Codex conversation choosing actions against reflected success and
ordinary denial. It includes exact adapter transcripts, observer records,
host-effect checks, the tested source archive, and every development launch
outcome. It is an exploratory two-run pilot, not a blinded or independent
model-behavior comparison.
