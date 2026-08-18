# Corrective Legislation Consolidation Requirements (MoSCoW)

## Must Have
- **MUST-01**: Invalidate unsupported PR #124 closeout receipts while preserving their historical provenance.
- **MUST-02**: Enforce no-future-dated-receipt policy across all JSON ledgers and tests.
- **MUST-03**: Create parent GitHub tracking issue for the corrective migration programme.
- **MUST-04**: Build exact live programmatically derived inventory of `corpus-legislation-nz` (`live-inventory.json` & `.md`).
- **MUST-05**: Import immutable donor Conductor tree into `conductor/archive/imported/corpus-legislation-nz/749918c251da59dc890c19dfda2ab9a021fd8ca6/`.
- **MUST-06**: Assimilate the complete, mature donor implementation into `src/archive_govt_nz/domains/legislation/` (API client, XML/HTML parser, discovery, validation, manifests, coverage, period-sharded checkpoints, parquet/jsonl corpus generation, change detection).
- **MUST-07**: Replace regex-only normaliser with robust `xml.etree.ElementTree` parser extracting actual statutory types, in-force dates, assent dates, sections, and schedules without wall-clock substitutes.
- **MUST-08**: Ensure CLI (`archive-govt-nz legislation ...`), `nzlc` compatibility entrypoint, and MCP server execute the real domain engine against actual manifests and checkpoints.
- **MUST-09**: Establish real multi-source workflow orchestration for `config/source-sets/legislation.yml` with typed error handling and artifact receipts.
- **MUST-10**: Reconcile all 68 historical batches and 33,693 candidate work IDs with actual checksums and run IDs.
- **MUST-11**: Generate executable differential parity receipts with run IDs, manifest hashes, and mismatch lists.
- **MUST-12**: Individually reconcile all donor GitHub issues, keeping open/blocked states accurate.
- **MUST-13**: Implement fine-grained rights classifications (legislation text, HTML, metadata, logos).
- **MUST-14**: Pass 100% of target quality assurance gates (`tools/check.py`) with >=95% branch coverage and 100% patch coverage.

## Won't Have
- **WONT-01**: Do not merge or archive standalone product `edithatogo/legislation`.
- **WONT-02**: Do not delete historical PR #124 artifacts; mark them `invalidated` with explicit superseded links.
- **WONT-03**: Do not claim Gazette is complete while official/historical integrations remain in progress.
