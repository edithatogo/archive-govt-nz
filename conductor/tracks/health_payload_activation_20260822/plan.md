# Plan: Health Payload Activation

## Phases

### Phase 1: Evidence Audit
- [x] Audit recorded snapshots (`moh-resource-metadata.json`,
      `moh-resource-classification.json`, discovery evidence) for licence fields.

### Phase 2: Eligibility Engine (TDD)
- [x] Implement `tools/evaluate_health_payload_eligibility.py` with open-licence
      allowlist, fail-closed default, optional licence-map input, v1 receipt.
- [x] Test suite `tests/tools/test_evaluate_health_payload_eligibility.py`
      (11 tests: eligible path, restricted/unknown licence, missing identity,
      malformed inputs, receipt counts).

### Phase 3: Baseline Receipt
- [x] Generate honest baseline receipt (158 evaluated / 0 eligible).

### Phase 4: Assurance Gate
- [x] Run full `tools/check.py`; record result.

> **Status: COMPLETED** — All phases verified. Reviewed and closed 2026-08-22.
> Activation path: future live CKAN licence enrichment → `--licence-map` →
> re-evaluation → separately gated capture for any newly eligible resources.