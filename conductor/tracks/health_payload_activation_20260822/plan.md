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

### Phase 5: Licence Evidence Acquisition (DEC-HEALTH-001 Option 1)
- [x] Implement `tools/fetch_health_dataset_licences.py` (live/offline modes,
      raw-response preservation, bounded client reuse).
- [x] Execute live read-only probe: 28/28 datasets observed, responses preserved.
- [x] Fix `license_id` field-spelling handling (CKAN spelling) with tests.
- [x] Rebuild licence map offline: 27 CC-BY-4.0, 1 empty.
- [x] Re-evaluate eligibility: 157 payload-eligible / 1 decision-required.
- [/] Final full assurance gate.
- [x] Final full assurance gate: **ALL 20 STAGES GREEN**, 944 tests passed,
      zero failures.

> **Status: COMPLETED** — All phases verified. Reviewed and closed 2026-08-22.
> DEC-HEALTH-001 resolved via Option 1: 157/158 resources payload-eligible on
> CC-BY-4.0 evidence; capture remains behind Track 14's separate gates.