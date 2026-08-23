# Implementation Plan: Common Multi-Platform Publication & Distribution Hub

### Phase 1: Distribution Contracts, Packaging Router & Manifest Schemas
- [ ] Task: Define JSON schema `schemas/publication-manifest-v2.schema.json` supporting multi-platform deposition metadata.
- [ ] Task: Implement `src/archive_govt_nz/dist/router.py` orchestrating multi-target exports (Hugging Face, Zenodo, OSF, GitHub Releases).
- [ ] Task: Implement `src/archive_govt_nz/dist/packaging.py` creating deterministic RO-Crate 1.1 and Croissant dataset archives.
- [ ] Task: Add characterization tests for packaging and payload bundle generation.
- [ ] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 2: Target Adapters (Hugging Face, Zenodo, OSF) & Dry-Run Verification
- [ ] Task: Implement `src/archive_govt_nz/dist/hf_adapter.py` for automated Parquet table and snapshot syncing.
- [ ] Task: Implement `src/archive_govt_nz/dist/zenodo_adapter.py` supporting compliant versioned deposition creation.
- [ ] Task: Implement `src/archive_govt_nz/dist/osf_adapter.py` for institutional open-science snapshot mirroring.
- [ ] Task: Add dry-run and mock verification tests for all publication adapters (>=95% coverage).
- [ ] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 3: CLI/MCP Integration, Fixity Verification & Mutation Gates
- [ ] Task: Implement `src/archive_govt_nz/dist/verifier.py` validating remote published fixity against local CAS digests.
- [ ] Task: Wire publication operations into CLI (`archive-govt-nz publish`) and FastMCP server.
- [ ] Task: Add publication mutation testing gates in `tools/mutation_medallion.py`.
- [ ] Task: Validate full 20-stage gate harness (`tools/check.py`).
- [ ] Task: Conductor Track Review & Final Certification.

