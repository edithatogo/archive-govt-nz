# Plan - Cross Corpus Interoperability And Metadata

## Phase 1 - Cross-corpus roadmap mapping

- [x] Review `corpus-nz-hansard` tracks for search/RAG, RDF, Akoma Ntoso, and metadata endpoints.
- [x] Map which patterns apply to legislation and which are Hansard-specific.
- [x] Document optional artifact governance in legislation docs.

## Phase 2 - Researcher artifacts

- [x] Add or refine DuckDB/Polars examples for Hugging Face Parquet access.
- [x] Define optional search/RAG index contract with citation/provenance requirements.
- [x] Define validation manifest requirements for derived indexes.

## Phase 3 - Interoperability metadata

- [x] Define Croissant metadata scope for ML-ready discovery.
- [x] Define RO-Crate and Frictionless descriptors for research-object packaging.
- [x] Define DCAT/PROV-O metadata surface and stable URI policy.
- [x] Evaluate Akoma Ntoso export as a generated endpoint, not the internal schema.

## Phase 4 - Publication environments

- [x] Decide whether derived artifacts publish to Hugging Face, Zenodo, OSF, GitHub release assets, or all/none.
- [x] Require each environment to declare access policy, file layout, checksums, and citation guidance.
- [x] Cross-link equivalent Hansard derived artifacts where useful.

## Verification

- [x] Roadmap docs mention the optional endpoint families.
- [x] No base dependency expansion occurs without a separate implementation track.
- [x] Conductor tracks.md registers this track.

## Evidence

- Roadmap contract: `docs/cross_corpus_interoperability_hansard.md`.
- Linked docs: `docs/corpus-family-design.md`,
  `docs/researcher_quickstart.md`, and `docs/implementation_status.md`.
- No code or dependency files were changed for endpoint implementation.
