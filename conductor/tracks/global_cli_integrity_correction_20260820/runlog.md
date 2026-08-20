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
- 2026-08-20T10:22:36Z: Live CLI help and a bounded capture probe established
  documentation drift: global capture returned `not_configured` with exit 2,
  while README/runbook text described it as a harvest; the migration interface
  map described nonexistent nested verbs and `--json` syntax; README claimed
  the donor was archived despite the required unarchived gate.
- 2026-08-20T10:31:29Z: Review-fix commit `ab81d80` reconciled README, runbook,
  interface grammar, exit meanings, compatibility shim identities, and donor
  state. Ruff, BasedPyright, and 67 targeted migration/CLI tests passed.
  `bash scripts/validate.sh` then passed again with 733 tests, 95.87% coverage,
  all schema and mutation gates, hygiene, CAS benchmark, audit, licence,
  secrets, and SBOM checks. Generated timestamp/live-snapshot changes were
  restored and not committed.
- 2026-08-20T10:32:49Z: Two adversarial tests failed against the corrected CLI:
  an internal `cas/sha256` symlink produced zero observed failures, and read-only
  CAS verification created `cas/tmp`. This established the red phase for the
  second and final CAS path-boundary fix loop.
- 2026-08-20T10:40:53Z: Commit `e105de1` rejects the internal namespace symlink
  and opens `ContentAddressedStore` without directory creation for verification.
  Ruff and BasedPyright passed; 52 focused integrity/object-store tests passed;
  `cli_integrity.py` retained 100% line and branch coverage. The full locked
  harness passed with 735 tests, 95.88% branch-aware coverage, and all schema,
  mutation, hygiene, benchmark, audit, licence, secrets, and SBOM gates green.
  Generated timestamp/live-snapshot churn was restored and not committed.
  Documentation-only commit `2694c17` removed volatile exact test counts from
  README; its migration contract tests and repository formatting/lint passed.
