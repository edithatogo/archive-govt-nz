# Specification — Track 19: Global Harvest Orchestration, Derivatives, and CI/CD Quality Frontiers

## Architecture Design

### 1. Unified Harvester Orchestrator (`tools/harvest_ckan.py`)
- Reads `--base-url`, `--workers`, `--concurrency-per-host`, and output paths.
- Sequences Discovery (`GlobalCkanDiscovery`), Classification (`classify_global_manifest`), Capture (`run_global_batch_capture`), and Packaging (`build_ro_crate_metadata`, `build_bagit_package`).
- Emits unified execution receipt `evidence/global-harvest-summary.json`.

### 2. Wayback Triangulation Engine (`src/archive_govt_nz/wayback_triangulation.py`)
- Queries `https://web.archive.org/cdx/search/cdx?url={url}&output=json&limit=1&filter=statuscode:200`.
- If available snapshot found, streams snapshot content into CAS and records recovery receipt linking original URL, snapshot URL, timestamp, and object ID.

### 3. Columnar Derivatives Engine (`src/archive_govt_nz/analytical_derivatives.py`)
- Ingests CSV/TSV data streams from CAS.
- Uses `pyarrow` to parse tabular schema and write snappy-compressed Parquet derivatives to `derivatives/parquet/{dataset_id}_{resource_id}.parquet`.
- Emits derivative manifest `evidence/analytical-derivatives-manifest.json` with source hash, derivative hash, row count, column count, and compression ratio.

### 4. Catalogue Drift Engine (`src/archive_govt_nz/drift_engine.py`)
- Diffs two `GlobalCkanScope` or scope manifests:
  - Added datasets / resources
  - Removed datasets / resources
  - Updated metadata timestamps
  - License mutations
- Emits drift report `evidence/catalogue-drift-report.json`.

### 5. Quality & CI/CD Gates
- `tools/mutation_global_policy.py`: Mutates rights decision thresholds and tests failure recovery.
- `tools/check_slops.py`: Verifies zero dead comments, placeholder tokens, or loose mock artifacts.
- `tools/benchmark_cas.py`: Verifies minimum 50MB/s hashing and chunking throughput on local CAS engine.
- `.github/workflows/weekly-catalogue-drift.yml`: Scheduled weekly workflow running automated drift audits against `data.govt.nz`.
