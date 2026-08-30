# Plan: Source-Evidenced, Namespace-Aware Legislation Normalisation

1. **Phase 1: Contract and Track Specifications (Commit A)**
   - Update MoSCoW requirements and execution plan with strict normalisation rules.
   - Validate YAML contracts using `tools/validate_contracts.py`.

2. **Phase 2: Source-Evidenced Normalisation Implementation (Commit B)**
   - Implement bounded `_SafeHTMLTextExtractor(HTMLParser)` to eliminate regex-based HTML tag removal.
   - Implement safe XML parsing with namespace stripping, entity expansion prevention, and structured element inspection in `src/archive_govt_nz/domains/legislation/normalise.py`.
   - Update `normalise_legislation_payload` signature to require `retrieval_timestamp: str` and optional source metadata.
   - Extract type, status, expression, dates, sections, schedules from structured metadata with no blind defaults.
   - Ensure unknown values remain `LegislationType.OTHER` and `VersionStatus.UNKNOWN` with `status_uncertain=True`.

3. **Phase 3: Comprehensive Test Matrix & Verification (Commit B)**
   - Create test suite covering Acts, Bills, Regulations, repealed/historical expressions, unknown status, multiple expressions, XML with namespaces, HTML, schedules, malformed input, and controlled fallbacks.
   - Verify 100% patch coverage and execute `tools/check.py`.


## 2026-08-30 record preservation

- [x] Preserve the original historical plan verbatim in [plan.original.md](plan.original.md) and record its hash.

The checkbox above records preservation only. Original phase prose has no individual task checkmarks; this reconciliation does not assert or reverify its historical completion. Existing completion claims remain attributable to the original record.
