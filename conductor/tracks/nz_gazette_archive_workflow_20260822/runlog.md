# Run Log: NZ Gazette Archive Workflow

- 2026-08-22: Track created and registered. Phase 1 infrastructure audit complete:
  adapter, domain models, schema, and source-set config verified reusable;
  service/discovery/validation/manifest layers and CI workflow identified as gaps.
- 2026-08-22: Phase 2 complete (TDD). Implemented `validate.py`, `discovery.py`,
  `service.py` with 15 passing domain tests. Safe HTMLParser text extraction
  replaces any regex approach; fail-closed discovery on missing notice IDs.
- 2026-08-22: Phase 3 complete (TDD). Implemented `tools/run_gazette_harvest.py`
  with full outcome taxonomy; 12 orchestrator tests including negative controls.
  Orchestrator patch coverage 99% (requirement >=95% met). Ruff format/lint and
  pyright clean on all new files.
- 2026-08-22: Phase 4 complete. Added `.github/workflows/scheduled-gazette-harvest.yml`
  (weekly Thursday 04:00 UTC, pinned SHAs matching existing workflows, credential
  env wiring, receipt artifact upload).
- 2026-08-22: Phase 5 complete. Full 19-stage gate `tools/check.py`: ALL STAGES
  GREEN. 723 tests passed; total coverage 95.78% (>=95% required); pyright
  0 errors; all 7 mutation suites passed; hygiene/slop gate passed; CAS
  benchmark 511 MB/s; dependency audit, licence inventory, secret scan, SBOM
  validation all passed.

## Review Verdict: COMPLETED

All 5 phases complete. MoSCow Must requirements M-01 through M-06 satisfied:
deterministic orchestrator with outcome taxonomy and checkpoint promotion,
fail-closed typed discovery, schema-consistent normalisation without regex,
chronology-enforcing validation, scheduled pinned CI workflow, and >=95%
orchestrator patch coverage with negative controls. Publication remains gated;
historical gazette sources remain deferred per registry gate.