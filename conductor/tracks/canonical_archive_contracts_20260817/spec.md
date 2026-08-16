# Track 4 Specification: Canonical Archive Contracts

## Purpose
Define the common universal data model, source identifiers, manifest schemas, and append-only ledger contracts before implementation assimilation begins.

## Context & Objectives
1. Harmonize source identifiers across CKAN catalogues, agency registries, social-media accounts, video channels, and newsletter subscriptions.
2. Define universal `ArchiveObject`, `CaptureEvent`, `SourceManifest`, `PreservationManifest`, and `PublicationReceipt` models.
3. Formally link W3C PROV-O provenance, cryptographic SHA-256 CAS fixity, rights dispositions, and tombstone/withdrawal semantics into every manifest schema.

## Deliverables
- `schemas/archive/v1/source-manifest.schema.json`
- `schemas/archive/v1/preservation-manifest.schema.json`
- `schemas/archive/v1/capture-event.schema.json`
- `schemas/archive/v1/publication-receipt.schema.json`
- Universal data contract definitions in `src/archive_govt_nz/core/`
