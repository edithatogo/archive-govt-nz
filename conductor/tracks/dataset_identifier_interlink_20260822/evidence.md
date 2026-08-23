# Evidence: Dataset Identifier Interlinking

## Deliverables
- `tools/build_identifier_interlink.py` — deterministic interlink engine.
- `tests/tools/test_build_identifier_interlink.py` — 14 tests.
- `evidence/identifier-interlink.json` — baseline manifest (2026-08-22):
  - legislation: 0 (pre-first-harvest honest state)
  - health-dataset: 28, health-resource: 158
  - publication-hf: 3, publication-zenodo: 1
  - findings: 0, status: passed

## Invariants
1. Malformed per-domain identifiers are always reported as findings.
2. Cross-domain raw-ID collisions are surfaced, never silently merged.
3. The manifest is rebuildable purely from committed evidence (offline).