# Plan - Source Redundancy Resolver and Provenance

## Phase 1 - Resolver Policy and Schema

- [x] Task: Define source priority and adoption policy.
    - [x] Specify canonical, fallback-assisted, secondary-corroborated, and
      rescued-source statuses.
    - [x] Define manual-review gates for non-canonical source promotion.
- [x] Task: Define retrieval-attempt provenance schema.
    - [x] Include source name, URL, method, timestamp, status, content hash,
      warning/error text, confidence, and rights note.
    - [x] Align with shared NZ corpus core provenance fields.
- [x] Task: Conductor - User Manual Verification 'Resolver Policy and Schema' (Protocol in workflow.md)

## Phase 2 - Integration Points and Review Output

- [x] Task: Add tests for resolver ordering and reporting.
    - [x] Cover successful API XML, official HTML fallback, alternate dated URL,
      website fallback, and NZLII candidate states.
    - [x] Cover deterministic hash/manifest behaviour.
- [x] Task: Implement resolver state model or adapter contract.
    - [x] Keep source adapters pluggable and independently testable.
    - [x] Preserve all failed attempts for auditability.
- [x] Task: Extend review outputs.
    - [x] Count records by source status and fallback method.
    - [x] Emit manual-review queues for secondary-source or low-confidence
      records.
- [x] Task: Conductor - User Manual Verification 'Integration Points and Review Output' (Protocol in workflow.md)

## Phase 3 - Documentation and Track Coordination

- [x] Task: Document resolver usage across Tracks 37-39.
    - [x] Explain how feed signals enqueue API refreshes.
    - [x] Explain how website and NZLII fallbacks are gated.
- [x] Task: Update archive and public wording caveats if needed.
    - [x] Preserve official-source primacy and source-rights warnings.
    - [x] Avoid public completeness claims until reconciliation evidence exists.
- [x] Task: Conductor - User Manual Verification 'Documentation and Track Coordination' (Protocol in workflow.md)
    - [x] Verified `docs/source_redundancy_resolver.md` now names Tracks 37-39
      and explains how feed signals, official website fallback evidence, and
      NZLII reconciliation plug into the resolver.
    - [x] Verified fallback/secondary rights notes, manual review gates, and
      conservative public completeness/coverage-status rules are documented.

## Validation Evidence

- `uv run pytest -q -p no:cacheprovider tests\test_source_redundancy.py tests\test_bootstrap_review.py tests\test_nzlii_reconcile.py` - 27 passed.
- `uv run ruff check src\nz_legislation_corpus\source_redundancy.py tests\test_source_redundancy.py tests\test_bootstrap_review.py` - passed.
- `uv run ruff format --check src\nz_legislation_corpus\source_redundancy.py tests\test_source_redundancy.py tests\test_bootstrap_review.py` - passed.
- `uv run ty check src\nz_legislation_corpus\source_redundancy.py tests\test_source_redundancy.py tests\test_bootstrap_review.py` - passed.
- `uv run python -c "import json, pathlib; json.loads(pathlib.Path('schemas/source_redundancy.schema.json').read_text(encoding='utf-8')); print('schema ok')"` - passed.
