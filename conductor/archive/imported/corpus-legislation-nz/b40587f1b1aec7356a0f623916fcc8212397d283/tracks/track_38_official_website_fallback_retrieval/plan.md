# Plan - Official Website Fallback Retrieval

## Phase 1 - Policy and Fallback Contract

- [x] Task: Define browser fallback policy.
    - [x] State allowed and disallowed retrieval behaviours.
    - [x] Define when browser fallback may run and when it must fail closed.
- [x] Task: Define fallback provenance and warning contract.
    - [x] Add fields for retrieval method, source URL, previous failure reason,
      rendered capture hash, and fallback confidence.
    - [x] Define review-report indicators for browser fallback use.
- [x] Task: Conductor - User Manual Verification 'Policy and Fallback Contract' (Protocol in workflow.md)

## Phase 2 - Focused Retrieval Tooling

- [x] Task: Add tests for fallback ordering and provenance.
    - [x] Cover API/XML/HTML failure followed by official page retrieval.
    - [x] Cover fail-closed behaviour when browser retrieval is blocked.
- [x] Task: Implement a small failed-record retry planner.
    - [x] Accept a small failed-record list from caller code.
    - [x] Retry only the requested records with conservative pacing.
- [x] Task: Integrate Playwright diagnostics where appropriate.
    - [x] Keep browser setup optional and separate from normal sync.
    - [x] Capture artifacts for triage without broad crawling.
- [x] Task: Conductor - User Manual Verification 'Focused Retrieval Tooling' (Protocol in workflow.md)

## Phase 3 - Review and Documentation

- [x] Task: Extend review output for browser fallback.
    - [x] Count browser fallback records separately from XML-to-HTML fallback.
    - [x] Surface unresolved blocked pages for manual triage.
- [x] Task: Document operational use.
    - [x] Provide commands, rate-limit guidance, and provenance caveats.
    - [x] Explain why stealth mode is not part of the standard path.
- [x] Task: Conductor - User Manual Verification 'Review and Documentation' (Protocol in workflow.md)

## Validation Evidence

- `uv run pytest -q tests/test_website_fallback.py tests/test_artifact_provenance.py` passed.
- `uv run ruff check src/nz_legislation_corpus/website_fallback.py tests/test_website_fallback.py` passed.
- 2026-07-01: `nzlc plan-website-fallbacks` produced a deterministic retry
  plan for one official queued record and one offsite blocked record.
- 2026-07-01: `nzlc website-fallback-diagnostics` produced a bounded
  Playwright diagnostics plan without running a browser by default.
- 2026-07-01: Review fixes added explicit browser fallback warning/provenance
  fields to full-bootstrap review output, post-run capture hashes for rendered
  diagnostics, and fail-closed URL revalidation before Playwright execution.
- 2026-07-01: Validation passed:
  `uv run python -m pytest -q -p no:cacheprovider tests\test_website_fallback.py tests\test_source_redundancy.py tests\test_bootstrap_review.py tests\smoke\test_cli_smoke.py -q`;
  `uv run ruff check --no-cache src\nz_legislation_corpus\website_fallback.py src\nz_legislation_corpus\cli.py src\nz_legislation_corpus\bootstrap_review.py tests\test_website_fallback.py tests\test_bootstrap_review.py`;
  `uv run ruff format --check src\nz_legislation_corpus\website_fallback.py src\nz_legislation_corpus\cli.py src\nz_legislation_corpus\bootstrap_review.py tests\test_website_fallback.py tests\test_bootstrap_review.py`;
  `uv run ty check src tests`.
