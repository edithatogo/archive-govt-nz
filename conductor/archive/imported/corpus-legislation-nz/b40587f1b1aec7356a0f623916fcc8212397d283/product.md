# Product Context

## Product summary

`corpus-legislation-nz` is an API-first pipeline for building and maintaining a
New Zealand legislation corpus. It ingests data from the official NZ
Legislation API, normalizes records, preserves provenance, writes optimized
Parquet shards, and publishes the live corpus to Hugging Face Datasets with
annual archive snapshots on Zenodo.

## Primary users

- Maintainers operating the corpus pipeline.
- Researchers or downstream consumers who need a stable legislation dataset.
- CI/CD and release automation that validates, packages, and publishes corpus
  artifacts.

## Core goals

- Keep the repository code-only and easy to audit.
- Make sync, validation, manifest generation, and archive publication
  idempotent.
- Preserve source provenance for every record.
- Minimize upload churn by comparing stable content hashes and preserving
  unchanged records.
- Keep live dataset publishing and annual archiving reproducible and safe to
  rerun.

## Key capabilities

- Discover and sync legislation records from the official NZ Legislation API.
- Normalize legislation data into machine-friendly records.
- Extract and preserve raw XML or HTML provenance when available.
- Write partitioned Parquet shards for efficient downstream use.
- Generate manifests and checksums for auditability.
- Publish the live dataset to Hugging Face Datasets using Xet-aware uploads.
- Produce annual Zenodo archive bundles and draft deposits.
- Validate corpus state and coverage with deterministic local commands.

## Non-goals

- This repository is not a general legal analysis tool.
- It is not a manual curation interface for editing legislation content.
- It does not assume perfect corpus completeness unless a deterministic seed
  inventory or official bulk source has been reconciled.

## Product constraints

- The source of truth is the official NZ Legislation API and the repository
  metadata produced from it.
- External publishing steps depend on API credentials and should stay
  non-destructive by default.
- The pipeline must remain safe to rerun in CI and on a maintainer workstation.

## Corpus family naming and sibling alignment

Preferred systematic project label: `corpus-nz-legislation`.

Sibling corpus label: `corpus-nz-hansard`.

Agents should use these labels in new roadmap, requirements, design, and environment-planning documents. Existing published URLs must remain stable unless a dedicated migration track verifies redirects, citations, DOI metadata, Hugging Face dataset references, and release notes.


## Versioning, CI/CD, and provenance target

The product target is a SOTA, evidence-backed automation system: SemVer for package/CLI behaviour, independent dataset and schema versions, manifest-hash release evidence, Hugging Face revision tracking, Zenodo DOI snapshots, protected production publication, and artifact attestations or SLSA-style provenance for release outputs.
