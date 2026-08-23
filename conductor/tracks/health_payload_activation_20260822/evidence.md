# Evidence: Health Payload Activation

## Deliverables
- `tools/evaluate_health_payload_eligibility.py` — deterministic fail-closed
  eligibility engine; pure/offline by default; accepts future licence-map
  enrichment without code changes.
- `tests/tools/test_evaluate_health_payload_eligibility.py` — 11 tests.
- `evidence/health/eligibility-receipt.json` — baseline receipt:
  158 evaluated, 0 payload-eligible, 158 decision-required.

## Invariants
1. Absent licence evidence never admits a payload (fail-closed default).
2. Open-licence recognition limited to explicit allowlist identifiers.
3. Eligible licence without a retrievable HTTPS URL stays closed.
4. No rights decisions made; capture remains behind existing separate gates.