# Implementation Plan: Common Multi-Platform Publication & Distribution Hub

### Phase 1: Distribution Contracts, Packaging Router & Manifest Schemas [COMPLETED]
- [x] Task: Define JSON schema `schemas/publication-manifest-v2.schema.json` supporting multi-platform deposition metadata.
- [x] Task: Implement `src/archive_govt_nz/dist/router.py` orchestrating multi-target exports (Hugging Face, Zenodo, OSF, GitHub Releases).
- [x] Task: Implement `src/archive_govt_nz/dist/packaging.py` creating deterministic RO-Crate 1.1 and Croissant dataset archives.
- [x] Task: Add characterization tests for packaging and payload bundle generation.
- [x] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 2: Target Adapters (Hugging Face, Zenodo, OSF) & Dry-Run Verification [COMPLETED]
- [x] Task: Implement `src/archive_govt_nz/dist/hf_adapter.py` for automated Parquet table and snapshot syncing.
- [x] Task: Implement `src/archive_govt_nz/dist/zenodo_adapter.py` supporting compliant versioned deposition creation.
- [x] Task: Implement `src/archive_govt_nz/dist/osf_adapter.py` for institutional open-science snapshot mirroring.
- [x] Task: Add dry-run and mock verification tests for all publication adapters (>=95% coverage).
- [x] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 3: CLI/MCP Integration, Fixity Verification & Mutation Gates [COMPLETED]
- [x] Task: Implement `src/archive_govt_nz/dist/verifier.py` validating remote published fixity against local CAS digests.
- [x] Task: Wire publication operations into CLI (`archive-govt-nz publish`) and FastMCP server.
- [x] Task: Add publication mutation testing gates in `tools/mutation_medallion.py`.
- [x] Task: Validate full 20-stage gate harness (`tools/check.py`).
- [x] Task: Conductor Track Review & Final Certification.


