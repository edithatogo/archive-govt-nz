# Run log

- 2026-08-20T09:30:02Z: Created local successor branch
  `codex/global-cli-correction` at service-correction head `580a134`. PR #156
  remained the only open PR and all of its hosted checks were green.
- 2026-08-20T09:30:02Z: Full Conductor validation remained blocked by
  pre-existing control-plane defects: missing `conductor/vcs.md` and index
  links, legacy metadata, and registry parsing mismatches. These defects are
  recorded separately and do not establish CLI correctness.
- 2026-08-20T10:19:10Z: Replaced the merged PR #150 evidence stubs. The initial
  adversarial slice failed 11 of 11 tests against the inherited implementation.
  Production-shaped CAS, archive structure and fixity, closed provenance,
  semantic search, publication-package rights/destination/fixity, and Python
  3.14 runtime checks are now implemented at commit `7616ddb`.
- 2026-08-20T10:19:10Z: Self-review added fail-closed controls for symlinked CAS
  objects, non-archive fixity entries, contradictory publication rights, and
  aggregate integrity failure naming. Ruff and BasedPyright passed; the affected
  suite passed 103 tests.
- 2026-08-20T10:19:10Z: `bash scripts/validate.sh` passed: 733 tests at 95.87%
  branch-aware coverage, 21 schemas and 11 representative documents, all
  mutation gates, hygiene, CAS benchmark, dependency audit, licence inventory,
  secret scan, and SBOM validation. Generated timestamp/live-snapshot changes
  were restored and were not committed.
