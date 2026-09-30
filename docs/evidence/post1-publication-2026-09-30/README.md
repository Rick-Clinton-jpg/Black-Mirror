# Black Mirror 1.1.2.post1 publication validation

Run date: 2026-09-30. These checks used the post1 publication candidate. Its runtime code, tests, examples and workflow are byte-for-byte identical to 1.1.2. Only documentation, metadata and evidence were changed.

## GitHub Actions

- [First project run](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36728594698), commit `5fefb7400a8ba2d3b55bb9f995f6f87275a571ea`; job `109931850575`.
- Install: `black-mirror-1.1.2.post1`, Ubuntu 24.04 GitHub runner, Python 3.12.14, pytest 8.4.2.
- Kernel probe: exit 0, `mirror-kernel-ready`.
- Full suite: **469 passed, 2 skipped in 20.31s**, including passing timing tests.
- `github-ci.log` is the decoded job log; `github-ci-run.json` records run identity and status.

## UTM Linux

- Same existing Ubuntu 26.04.1 aarch64 VM and Python 3.14.4 environment described in [the original evidence](../Black-Mirror-Evidence/FINDINGS.md).
- Editable install used system-site packages with no build isolation or dependency installation.
- Kernel probe: exit 0, `mirror-kernel-ready`.
- Full suite: **469 passed, 2 skipped in 8.13s**.
- `install.log`, `kernel-probe.log` and `linux-tests.log` preserve the output.

Both sets of skips are the optional `mirror_shield` tests. These are regression checks; no new live-model containment session was run for post1. `SHA256SUMS.json` covers all files here except itself.
