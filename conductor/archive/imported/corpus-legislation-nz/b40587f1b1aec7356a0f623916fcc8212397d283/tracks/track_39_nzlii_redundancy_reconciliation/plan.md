# Plan - NZLII Redundancy Reconciliation

## Phase 1 - Source Inventory and Policy

- [x] Task: Document NZLII collections, URL patterns, and access caveats.
    - [x] Identify relevant legislation collection entry points.
    - [x] Record robots/access/rate-limit considerations.
- [x] Task: Define NZLII candidate-match schema.
    - [x] Include source URL, title/date fields, content hash, confidence, and
      match classification.
    - [x] Keep fallback status separate from canonical source status.
- [x] Task: Conductor - User Manual Verification 'Source Inventory and Policy' (Protocol in workflow.md)
    - [x] Verified source inventory records collection URL patterns, conservative
      access policy, non-canonical status, source role, and caveats.

## Phase 2 - Matching and Reconciliation Reports

- [x] Task: Add tests for NZLII candidate matching.
    - [x] Cover exact, probable, ambiguous, missing, and out_of_scope classifications.
    - [x] Cover no-write reconciliation mode.
- [x] Task: Implement or specify candidate discovery and matching.
    - [x] Use official metadata as the primary query/matching input.
    - [x] Preserve all NZLII retrieval and matching provenance.
- [x] Task: Generate reconciliation reports.
    - [x] Compare NZLII candidates with seed inventory and bootstrap failures.
    - [x] Emit manual-review queues for ambiguous candidates.
- [x] Task: Conductor - User Manual Verification 'Matching and Reconciliation Reports' (Protocol in workflow.md)
    - [x] Verified reconciliation output covers classifications, seed comparison,
      bootstrap failure comparison, review-report comparison, and manual-review
      queues without writing canonical records.

## Phase 3 - Optional Text Rescue Path

- [x] Task: Define guarded text rescue rules.
    - [x] Require official source failure and explicit fallback marking.
    - [x] Keep rescued text out of canonical promotion until reviewed.
- [x] Task: Document operational use and review requirements.
    - [x] Explain rights/provenance caveats.
    - [x] Link reconciliation output to Track 07 review evidence.
- [x] Task: Conductor - User Manual Verification 'Optional Text Rescue Path' (Protocol in workflow.md)
    - [x] Verified text-rescue triage rows preserve selected NZLII provenance,
      bootstrap failure provenance, fallback status, review requirement, and
      `canonical_promotion_allowed: false`.

## Validation Evidence

- `uv run pytest -q -p no:cacheprovider tests\test_nzlii_reconcile.py tests\test_source_redundancy.py tests\smoke\test_cli_smoke.py` - 26 passed.
- `uv run ruff check src\nz_legislation_corpus\nzlii_reconcile.py src\nz_legislation_corpus\cli.py tests\test_nzlii_reconcile.py` - passed.
- `uv run ruff format --check src\nz_legislation_corpus\nzlii_reconcile.py src\nz_legislation_corpus\cli.py tests\test_nzlii_reconcile.py` - passed.
- `uv run ty check src\nz_legislation_corpus\nzlii_reconcile.py src\nz_legislation_corpus\cli.py tests\test_nzlii_reconcile.py` - passed.
