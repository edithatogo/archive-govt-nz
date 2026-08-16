# Track 14 Specification: Post-Consolidation Extension and RIOPA Interoperability

## Purpose
Prepare `archive-govt-nz` to serve as a reusable, research-grade archival component and producer-consumer foundation for the broader RIOPA public data ecosystem (including `corpus-nz-hansard`, `fyi-archive`, `hathi-nz`, and RIOPA Public Data) without physically merging unrelated codebases.

## Context & Objectives
1. Adopt standard RIOPA provenance, rights, and BagIt/RO-Crate publication protocols.
2. Provide clean producer-consumer export contracts and streaming CAS interfaces for upstream and downstream scholarly corpora.
3. Identify reusable shared abstractions (such as generic CAS storage or CDX triangulation) for future extraction into standalone libraries once at least two independent consumers exist.

## Deliverables
- `docs/interoperability/riopa-integration-spec.md`
- Export interface contracts for downstream research consumers
