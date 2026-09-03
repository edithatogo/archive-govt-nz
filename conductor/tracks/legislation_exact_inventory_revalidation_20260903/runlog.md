# Run log

- 2026-09-03: fetched target main at `dcc8f37f5642fc6b4337c49bd482b126325e6b6c`.
- 2026-09-03: confirmed donor archived with reachable main
  `b40587f1b1aec7356a0f623916fcc8212397d283`.
- 2026-09-03: initial focused contract run failed 9 tests because the exact config
  and workflow did not exist; the v3 fixture characterization passed.
- 2026-09-03: no source acquisition or publication was performed.
- 2026-09-03: first full validation stopped at Ruff format because three test
  literals required the repository's single-quote normalization; formatted the
  owned test and retained this failed attempt.
- 2026-09-03: second full validation reached basedpyright and rejected access to
  typed v2 fields without first narrowing the parser's legacy-compatible union;
  added the explicit `SourceSetConfig` assertion and retained this failed attempt.
- 2026-09-03: third full validation passed lock, Conductor, format, lint and types;
  4,552 of 4,553 tests passed at 97.50% coverage. Unrelated existing Hypothesis
  test `test_union_algebra` exceeded its 200 ms deadline once (358.61 ms) and then
  passed during Hypothesis replay, so the harness classified it as flaky. No
  implementation or threshold was changed.
- 2026-09-03: the immediate focused rerun of `test_union_algebra` passed. The next
  full harness encountered the same unrelated cold-load timing class in Prompt 08
  property test `test_archive_order_does_not_change_roots` (288.27 ms once, then
  52.75 ms on replay); 4,552 of 4,553 tests again passed at 97.50% coverage.
  No deadline, test, or threshold was weakened.
- 2026-09-03: the affected property passed immediately in isolation; the next
  required full harness passed all 4,553 tests at 97.50% coverage and completed
  schema, parity, mutation, hygiene, performance, dependency, licence, secret and
  SBOM gates.
- 2026-09-03: self-review added an explicit 64 MiB CAS byte bound alongside the
  128 MiB total-state bound; no live dispatch was performed.
