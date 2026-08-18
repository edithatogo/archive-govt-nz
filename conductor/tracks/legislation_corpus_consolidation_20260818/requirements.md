# Legislation Corpus Consolidation Requirements (MoSCoW)

## Must Have
- **MUST-1**: Execute Mandatory Pre-Acquisition Discovery (`pre-acquisition-discovery.json` & `.md`).
- **MUST-2**: Audit baseline SHAs and build comprehensive capability matrix and workflow route table for all 25 donor workflows.
- **MUST-3**: Reconcile donor Conductor tracks and all 65 donor issues individually with supporting receipts.
- **MUST-4**: Preserve external publication identities (`edithatogo/corpus-legislation-nz`, `edithatogo/corpus-legislation-nz-historical`, Zenodo `10.5281/zenodo.20592540`).
- **MUST-5**: Implement canonical legislation and gazette adapters (`adapters/nz_legislation.py`, `adapters/nz_gazette.py`) and domain modules (`domains/legislation/`, `domains/gazette/`).
- **MUST-6**: Distinguish legal document identity layers (work, expression, manifestation, normalised record).
- **MUST-7**: Provide CLI operations (`archive-govt-nz legislation ...`) and backward-compatible `nzlc` CLI wrapper.
- **MUST-8**: Implement differential parity test suites (fixtures, historical batches, live public smoke, publication package).
- **MUST-9**: Maintain >95% branch coverage and pass all 19 local and remote assurance gates.

## Should Have
- **SHOULD-1**: Implement NZ Gazette progression roadmap and source coverage manifests (`config/source-sets/nz-gazette.yml`, `docs/domains/gazette/source-coverage.md`).
- **SHOULD-2**: Provide disaster recovery and replay procedures for legislation.

## Won't Have
- **WONT-1**: Do not copy or merge `edithatogo/legislation` (it remains standalone).
- **WONT-2**: Do not commit large corpus raw payloads or Parquet binaries directly to Git.
