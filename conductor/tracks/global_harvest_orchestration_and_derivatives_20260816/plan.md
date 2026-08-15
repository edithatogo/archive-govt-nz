# Implementation Plan — Track 19: Global Harvest Orchestration, Derivatives, and CI/CD Quality Frontiers

## Phase 1 — Unified Harvester CLI Orchestrator
- [x] Task: Implement `tools/harvest_ckan.py` chaining Discovery, Policy, Ingestion, and Preservation.
- [x] Task: Write tests in `tests/tools/test_harvest_ckan.py`.
- [x] Task: Phase Verification & Checkpoint.

## Phase 2 — Automated Wayback Triangulation
- [x] Task: Implement `src/archive_govt_nz/wayback_triangulation.py` and `tools/recover_broken_urls.py`.
- [x] Task: Write tests in `tests/test_wayback_triangulation.py`.
- [x] Task: Phase Verification & Checkpoint.

## Phase 3 — Columnar Analytical Derivatives Engine
- [x] Task: Implement `src/archive_govt_nz/analytical_derivatives.py` and `tools/build_analytical_derivatives.py`.
- [x] Task: Write tests in `tests/test_analytical_derivatives.py`.
- [x] Task: Phase Verification & Checkpoint.

## Phase 4 — Catalogue Drift Detection Engine
- [x] Task: Implement `src/archive_govt_nz/drift_engine.py` and `tools/detect_catalogue_drift.py`.
- [x] Task: Write tests in `tests/test_drift_engine.py`.
- [x] Task: Phase Verification & Checkpoint.

## Phase 5 — Bleeding-Edge Quality Gates, Benchmarks, and CI/CD
- [x] Task: Implement `tools/mutation_global_policy.py` and integrate into `tools/check.py`.
- [x] Task: Implement `tools/check_slops.py` and `tools/benchmark_cas.py`.
- [x] Task: Implement `.github/workflows/weekly-catalogue-drift.yml`.
- [x] Task: Full verification with `tools/check.py`, PR, and merge.
