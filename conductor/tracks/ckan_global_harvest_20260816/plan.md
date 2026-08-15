# Implementation Plan — Track 18: Global CKAN Catalog Harvester

## Phase 1 — Global Catalogue Discovery & Manifest Generation
- [x] Task: Write failing tests for unconstrained `package_search` discovery and count reconciliation.
- [x] Task: Implement global CKAN catalogue discovery tool (`tools/discover_global_ckan.py`).
- [x] Task: Execute global discovery against `data.govt.nz` and emit canonical discovery manifest.
- [x] Task: Phase Verification & Checkpoint.

## Phase 2 — Automated Rights & Policy Classification
- [x] Task: Write failing tests for bulk rights classification rules and tombstone assignments.
- [x] Task: Implement bulk policy evaluation tool to classify ~20k+ resources into admitted vs tombstone sets.
- [x] Task: Emit rights classification manifest and verified capture candidates list.
- [x] Task: Phase Verification & Checkpoint.

## Phase 3 — Bounded Concurrent Ingestion
- [x] Task: Write tests for per-host rate limiting, byte budgeting, and CAS streaming promotion.
- [x] Task: Implement batch capture runner with concurrency and per-domain throttling.
- [x] Task: Execute batch capture of eligible open resources into CAS object store.
- [x] Task: Phase Verification & Checkpoint.

## Phase 4 — Broken URL Reconciliation & Fallback Triangulation
- [x] Task: Generate structured Broken URL & Exception Ledger (404, 410, DNS, timeouts).
- [x] Task: Implement batch triangulation against Wayback Machine / CKAN DataStore fallback.
- [x] Task: Generate RO-Crate JSON-LD and BagIt preservation manifests.
- [x] Task: Produce final unified catalog preservation ledger and health summary.
- [x] Task: Phase Verification & Checkpoint.

