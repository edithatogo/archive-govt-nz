# Requirements — Track 19: Global Harvest Orchestration, Derivatives, and CI/CD Quality Frontiers

## Functional Requirements
1. **Harvester Orchestration**: Provide a unified CLI tool `tools/harvest_ckan.py` executing discovery -> policy -> domain-throttled capture -> preservation packaging with deterministic stdout and ledger receipts.
2. **Wayback / CDX Recovery**: Provide `src/archive_govt_nz/wayback_triangulation.py` and `tools/recover_broken_urls.py` that queries CDX API endpoints (Internet Archive / National Library) for broken URLs (404/410/DNS failure) and fetches available historical snapshots into CAS.
3. **Analytical Columnar Derivatives**: Provide `src/archive_govt_nz/analytical_derivatives.py` and `tools/build_analytical_derivatives.py` that reads captured CSV/TSV data from CAS and generates queryable Parquet files with zero mutation to raw files.
4. **Catalogue Drift Detection**: Provide `src/archive_govt_nz/drift_engine.py` and `tools/detect_catalogue_drift.py` that computes additions, removals, schema drifts, and license changes between discovery manifests.
5. **Quality & CI/CD Frontiers**:
   - Mutation suite for global policy: `tools/mutation_global_policy.py`.
   - Hygiene and slops verification gate: `tools/check_slops.py`.
   - Automated CAS performance benchmarking gate: `tools/benchmark_cas.py`.
   - Scheduled catalogue drift GitHub Actions workflow: `.github/workflows/weekly-catalogue-drift.yml`.
