# Run log

2026-09-01 UTC: live target/donor and parser/consumer inventory completed. Original dirty workspace retained; isolated worktree created from exact main.

2026-09-01 UTC: first focused run failed 21 tests because the custom boolean resolver shared mutable loader state with schema loading. Corrected by copying resolver tables and reading JSON Schema as JSON; the failed attempt remains part of this run history.

2026-09-01 UTC: first mutation attempt killed 10/11; publication-gate independence survived. A retry was started with the wrong target and interrupted (exit 130). The corrected and expanded runner killed 14/14 mutations; no prior result was reclassified as success.

2026-09-01 UTC: three read-only adversarial reviews found runtime enforcement, semantic contradiction, duplicate-name, URI-format, redaction and evidence gaps. All in-scope findings were implemented and covered. Focused integrated lane passed 124 tests with 100% statement/branch coverage for the critical module.

2026-09-01 UTC: first native harness attempt passed lock, Conductor, format, lint and types, then Python 3.14 xdist workers crashed with bus errors during collection. Retry used `tools/check.py --pytest-workers 1 --pytest-distribution loadscope` and passed all 4,267 tests plus every remaining repository gate. Generated donor snapshot side effects were preserved as a quarantine patch and restored from HEAD.

2026-09-01 UTC: hosted Codecov initially reported 91.28% patch coverage for direct-CLI rejection branches. Added independent-dimension and text-receipt tests without changing thresholds. Focused lane increased to 126 tests; the final rebased native harness passed 4,318 tests at 97.43% repository coverage with four xdist workers.

2026-09-01 UTC: final head `64753cc0` passed every hosted check, including Windows in 10m12s and Codecov patch coverage. PR #331 merged as `bd53d7c7` at 10:54:33Z and issue #330 closed. Exact-head readback completed; track marked complete.
