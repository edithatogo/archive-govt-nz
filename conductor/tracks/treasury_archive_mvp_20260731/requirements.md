# Treasury Archive MVP Requirements

## Requirement interpretation

These requirements refine the project-level requirements for the Treasury MVP.
Acceptance evidence must identify these stable IDs. A Must requirement cannot be
silently deferred; an unresolved Must leaves the track gated or incomplete.

## Must

### M-01: Reproducible foundation

Provide a locked Python 3.14 package, typed non-interactive CLI, structured
output, documented exit states, and one repository-wide validation command.

### M-02: CKAN capability evidence

Probe the versioned data.govt.nz CKAN Action API and record catalogue, deployed
version, response, transport, time, and integrity evidence without assuming
generic CKAN behaviour.

### M-03: Complete live Treasury scope

Resolve the Treasury organisation and reconcile every dataset in the complete
live organisation-filtered scope. Preserve raw paginated responses and never
hard-code the dated baseline count of 54.

### M-04: Complete metadata preservation

Preserve the raw CKAN representation and provenance for every discovered
Treasury dataset before normalization.

### M-05: Explicit resource eligibility

Evaluate every discovered resource through a versioned, configurable,
fail-closed policy covering scheme, redirects, time, bytes, storage,
decompression, type, filenames, rights, access, quarantine, and retry state.
Every resource receives an explicit outcome.

### M-06: Bounded streaming capture

Attempt every eligible resource through bounded streaming with atomic writes,
incremental hashing, safe retry, redaction, interruption handling, and verified
promotion.

### M-07: Immutable content identity

Use SHA-256 as the interoperable object identity, record BLAKE3 additionally,
verify existing objects before deduplication, and prevent mutable overwrite.

### M-08: Transactional operational ledger

Use migrated SQLite state with foreign keys and integrity constraints for
observations, attempts, objects, retries, versions, transformations, and
publication stages. Provide deterministic exports.

### M-09: Change-driven versioning

Create versions only for defined material change, record unchanged
verification, retain prior history, and represent withdrawal or disappearance
with tombstones.

### M-10: Versioned provenance

Produce JSON Schema-validated manifests linking sources, inputs, objects,
software, environment, parameters, transformations, validation, rights,
outcomes, limitations, and publication evidence.

### M-11: Core derivatives

Produce reconciled normalized dataset, resource, observation, relationship,
attempt, object, version, and publication tables in Parquet and JSONL while
retaining raw CKAN JSON.

### M-12: Material HTTP receipts

Create redacted WARC 1.1 records when HTTP transaction context is material and
validate their relationship to archived objects.

### M-13: Stage-based evidence

Generate paired Markdown and JSON evidence that distinguishes discovery,
eligibility, attempt, capture, validation, change, transformation, failure,
restriction, quarantine, upload, remote verification, and release.

### M-14: Recovery and reconciliation

Prove schema validity, object integrity, manifest closure, ledger integrity,
idempotency, interruption recovery, unchanged reruns, and bounded release
reconstruction without SQLite or DuckDB.

### M-15: Hardened automation

Provide least-privilege, immutable-action-pinned GitHub Actions for validation,
safe scheduled discovery and capture, security, release packaging, gated
publication, and remote verification.

### M-16: Rolling Hugging Face archive

After credential and publication approval, publish permitted originals,
derivatives, schemas, cards, manifests, and evidence to a rolling Hugging Face
dataset and independently verify the remote revision, paths, representative
records, sizes, Parquet endpoints, and Viewer state.

### M-17: Immutable Zenodo release

After explicit deposition and DOI approval, publish a checksum-pinned release
for an exact verified archive manifest and independently verify its DOI,
metadata, files, sizes, and checksums.

### M-18: Quality thresholds

Achieve 100% line and branch coverage for critical integrity, policy,
credential, recovery, versioning, and publication logic, and at least 95% line
and branch coverage overall. Apply property, state-machine, mutation, contract,
security, and recovery tests according to risk.

### M-19: Traceability and solo governance

Cross-reference this track with one GitHub parent issue, nested phase subissues,
pull requests, and task commits. Do not require a second-person review,
CODEOWNERS approval, team assignment, or reviewer count.

## Should

### S-01: Preservation-standard evaluation

Evaluate OCFL, RO-Crate, and BagIt with bounded Treasury fixtures and record
conformance tooling, benefits, gaps, maintenance, and adoption decisions.

### S-02: Source-friendly operation

Use identifiable user-agent strings, bounded concurrency, rate limits,
backpressure, conditional requests, safe range requests, and jitter.

### S-03: Supply-chain evidence

Generate dependency, licence, vulnerability, workflow-security, SBOM,
attestation, and signed-release evidence where supported.

### S-04: Compatibility lanes

Test current stable dependencies and isolate Python, CKAN-client, and archival
tool pre-releases without silently rewriting production locks.

### S-05: Clean-environment reproduction

Document and verify setup, validation, bounded capture, recovery, and
publication verification from clean environments.

## Could

### C-01: Rust performance component

Add a Rust hot-path component only after benchmarks, failure-contract tests, and
an approved design amendment demonstrate a material advantage.

### C-02: Static archive status site

Generate a read-only status site from the evidence ledger after the CLI and
machine-readable reports are proven.

### C-03: Additional preservation mappings

Add W3C PROV, DCAT, Croissant, or other standards-based exports after bounded
evaluation.

### C-04: Advanced transfer optimization

Add source-specific parallelism, chunking, or delta transfer when evidence
shows the baseline bounded streaming design is insufficient.

## Won't, in this track

### W-01: Health scope

Do not capture Ministry of Health or broader health datasets.

### W-02: Other organisations

Do not expand live capture beyond the Treasury organisation.

### W-03: Always-on application

Do not add a custom frontend, always-on API, or managed orchestration service.

### W-04: Authoritative search projections

Do not treat a graph or vector database as preservation truth and do not build
semantic embeddings in this MVP.

### W-05: Unbounded or unsafe capture

Do not download without byte, time, redirect, decompression, storage, and
quarantine controls.

### W-06: Silent deletion or exclusion

Do not erase preserved history because the source changes, and do not omit
unavailable, restricted, oversized, quarantined, or failed resources from
coverage.

### W-07: Ungated publication

Do not expose credentials, publish quarantined or restricted objects, create a
DOI without explicit approval, or infer publication from a green workflow.

### W-08: Premature upstream modification

Do not modify or submit to upstream CKAN projects without a reproduced need,
maintainer-owned fork or clone, tests, and review of contribution and AI
disclosure policies.
