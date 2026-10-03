# Public GitHub CI cumulative snapshot through run #29

Recorded 2026-10-03 after PR #6 merged. This is a fixed historical snapshot of
the `Security regression tests` workflow in `Rick-Clinton-jpg/Black-Mirror`.
Each row is the pytest summary in the latest completed attempt of one
`linux-containment` job. All 29 listed runs completed successfully and each
job logged `mirror-kernel-ready` before pytest.

**Total: 15,601 passing test-case executions and 58 skips across 29 workflow
runs (15,659 reported outcomes).** The current `main` run, #29, reported
**561 passed, 2 skipped**. The two skips in each listed run are optional
`mirror_shield` checks when that package is not installed.

These are repeated regression checks across pushes, pull requests, and
historical branches. They are not 15,601 distinct tests, independent agent
trials, escape attempts, or proof of containment. This tally excludes local
and UTM runs and earlier attempts of rerun jobs. In particular, the failed
first attempt of run #4 is documented separately in `TEST-REPORT.md` and is
not included here. The table uses one latest-attempt result per workflow run.

| Workflow run | Passed | Skipped |
| --- | ---: | ---: |
| [#1](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36728594698) | 469 | 2 |
| [#2](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36729153539) | 469 | 2 |
| [#3](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36774158603) | 534 | 2 |
| [#4](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36774204823) | 534 | 2 |
| [#5](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36775449564) | 534 | 2 |
| [#6](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36775455518) | 534 | 2 |
| [#7](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36782549208) | 534 | 2 |
| [#8](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36782554446) | 534 | 2 |
| [#9](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36785250904) | 534 | 2 |
| [#10](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36785390766) | 540 | 2 |
| [#11](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36785428550) | 540 | 2 |
| [#12](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36858707066) | 540 | 2 |
| [#13](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36858931831) | 544 | 2 |
| [#14](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36858958944) | 544 | 2 |
| [#15](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36894045308) | 534 | 2 |
| [#16](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36894115143) | 534 | 2 |
| [#17](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36971362663) | 543 | 2 |
| [#18](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/36971407098) | 543 | 2 |
| [#19](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/37083412197) | 543 | 2 |
| [#20](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/37083538950) | 549 | 2 |
| [#21](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/37083587875) | 549 | 2 |
| [#22](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/37084149311) | 549 | 2 |
| [#23](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/37084153734) | 549 | 2 |
| [#24](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/37085207589) | 549 | 2 |
| [#25](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/37085211463) | 549 | 2 |
| [#26](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/37112504253) | 561 | 2 |
| [#27](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/37112507121) | 561 | 2 |
| [#28](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/37113164302) | 543 | 2 |
| [#29](https://github.com/Rick-Clinton-jpg/Black-Mirror/actions/runs/37113197564) | 561 | 2 |

Sum: `15,601 passed + 58 skipped = 15,659 reported outcomes`.
