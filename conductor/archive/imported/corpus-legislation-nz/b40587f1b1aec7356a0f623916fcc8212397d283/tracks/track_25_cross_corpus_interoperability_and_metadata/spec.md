# Spec - Cross Corpus Interoperability And Metadata

## Status
done

## Goal

Extend the legislation corpus roadmap with validated researcher artifacts and SOTA metadata patterns aligned with `corpus-nz-hansard` while preserving the legislation corpus as an API-first legal text pipeline.

## Acceptance Criteria

- Legislation roadmap includes DuckDB/search/RAG, RDF/DCAT/PROV-O, Croissant, RO-Crate, Frictionless, and Akoma Ntoso/legal-document export considerations.
- Derived artifacts are versioned, validated, and optional.
- Hansard tracks are cited as reference patterns for search/RAG, linked data, endpoint contracts, and validation manifests.
- Publication-surface metadata remains aligned across GitHub, Hugging Face, Zenodo, OSF, and future metadata endpoints.

## Out of Scope

- Implementing all endpoint exporters in this track.
- Replacing the core legislation schema with Akoma Ntoso or RDF.
- Adding heavy dependencies to the base install before endpoint tracks justify them.

## Evidence Recorded

- `docs/cross_corpus_interoperability_hansard.md` maps Hansard reference
  patterns to legislation-specific decisions.
- `docs/corpus-family-design.md` links the Track 25 interoperability contract.
- `docs/researcher_quickstart.md` points researchers to optional derived
  artifact families without claiming they are already published.
- `docs/implementation_status.md` records the roadmap status.
