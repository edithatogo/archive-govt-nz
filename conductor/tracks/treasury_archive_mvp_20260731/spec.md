# Treasury Archive MVP Specification

## Track classification

MVP / Bootstrap

## Overview

Build the first production-grade vertical slice of Archive Govt NZ by
discovering, preserving, validating, versioning, and publishing the complete
live Treasury dataset scope exposed through data.govt.nz.

The MVP establishes reusable archival foundations while proving them against a
real priority organisation. It must not hard-code the observed catalogue count
or treat one successful run as proof of continuing completeness.

## Observed baseline

Read-only reconnaissance on 2026-07-31 observed:

- catalogue: `https://catalogue.data.govt.nz/`
- CKAN Action API version: `3`
- deployed CKAN version: `2.10.9`
- organisation name: `the-treasury`
- organisation ID: `4d08a178-e03b-4e97-b79d-83d9a7a35744`
- datasets returned by the organisation filter: `54`

The count of 54 is dated evidence, not a permanent acceptance constant.
Implementation must reconcile the live scope at each run.

## Goals

1. Create a reproducible Python 3.14 project and typed non-interactive CLI.
2. Inventory every dataset currently attributed to the Treasury organisation.
3. Preserve raw CKAN metadata responses and every eligible resource.
4. Record explicit outcomes for every dataset and resource.
5. Store originals as immutable content-addressed objects.
6. Detect material changes and create versions without duplicating unchanged
   content.
7. Produce transparent analytical derivatives and preservation receipts.
8. Prove interruption recovery, idempotency, reconciliation, and bounded
   reconstruction.
9. Automate scheduled archival and evidence generation through hardened GitHub
   Actions.
10. Publish and remotely verify a rolling Hugging Face dataset after explicit
    credential approval.
11. Prepare and, only after explicit approval, publish a checksum-pinned
    immutable Zenodo release.

## Users

### Maintainer

A solo maintainer who needs deterministic commands, strong automated checks,
bounded failures, resumable operation, and exact evidence of local and hosted
state.

### Researchers and data users

Users who need original government files, queryable derivatives, licences,
provenance, version history, and clear limitations.

### Automated consumers

Systems that consume stable JSON schemas, JSONL or Parquet tables, hashes,
manifests, and publication receipts.

## Functional requirements

### FR-1: Project and CLI foundation

The repository must provide:

- a locked Python 3.14 environment managed with `uv`;
- a typed installable package;
- a non-interactive CLI;
- structured JSON output for automation;
- explicit exit semantics for success, unchanged state, partial success,
  restricted state, retryable failure, and terminal failure;
- one repository-wide validation command.

Rust must not be introduced in this track without benchmark evidence and an
approved design amendment.

### FR-2: CKAN capability probe

Before archival, the system must:

- query the versioned CKAN Action API;
- record the catalogue URL, API version, observed CKAN version, observation
  time, and response hash;
- distinguish HTTP status from the CKAN `success` envelope;
- identify pagination and response behaviour from live read-only probes;
- fail closed on incompatible or malformed responses.

### FR-3: Treasury scope discovery

The system must:

- resolve Treasury by stable organisation name and ID;
- enumerate the complete live organisation-filtered dataset scope;
- paginate until the reported result set is reconciled;
- preserve raw response pages;
- detect duplicates, missing identifiers, pagination drift, and count drift;
- emit a dated scope manifest and coverage report;
- avoid assuming the 2026-07-31 count of 54 remains current.

### FR-4: Dataset metadata preservation

For every discovered dataset, preserve:

- the raw `package_show` or equivalent CKAN response;
- dataset identifiers, organisation, groups, tags, licence fields, temporal
  fields, modification timestamps, extras, and resources;
- response time, source URL, status, CKAN envelope state, and content hashes;
- normalized dataset and relationship records without modifying the raw object.

### FR-5: Resource eligibility and policy

Evaluate every resource through a versioned, configurable policy addressing:

- supported URL schemes;
- redirect count and destination policy;
- connect, read, and total time bounds;
- maximum streamed bytes and storage budget;
- claimed and detected media type;
- filename and path safety;
- decompression and archive-member limits;
- licence, rights, access, and authentication state;
- malware or suspicious-content quarantine;
- retry classification;
- operator-approved exceptions.

Every resource receives an explicit eligibility and attempt outcome. No resource
may disappear silently from coverage reporting.

### FR-6: Streaming capture

For every eligible resource, the system must:

- use bounded streaming rather than loading the entire response into memory;
- hash while streaming;
- write atomically through a temporary object;
- verify final size and hashes before promotion;
- retain relevant response metadata;
- support safe conditional and range requests where the source permits;
- cleanly resume or restart after interruption;
- avoid exposing signed URLs, credentials, or sensitive headers.

### FR-7: Content-addressed storage

The archive must:

- identify objects with SHA-256;
- record BLAKE3 as an additional high-throughput identity;
- prevent mutable overwrite of existing objects;
- verify an existing object before deduplicating;
- store source filenames only as sanitized metadata, not trusted paths;
- distinguish original, metadata, receipt, and derivative object roles.

Large payloads must remain outside the GitHub source repository.

### FR-8: Operational ledger

Use SQLite for transactional local state covering:

- catalogue observations;
- datasets and resources;
- capture attempts and outcomes;
- object identities;
- retries and checkpoints;
- version relationships;
- transformations;
- publication stages.

The ledger must enforce foreign keys and integrity constraints and support
deterministic export. It must not be the only preservation record.

### FR-9: Change-driven versioning

The system must:

- distinguish observation time from source modification time;
- compare normalized metadata and resource object identities;
- create a new version only for defined material changes;
- record unchanged verification without duplicating content;
- represent disappearance or withdrawal through tombstones;
- never automatically erase prior captured versions;
- evolve versioning policy only through versioned rules and migration evidence.

### FR-10: Manifests and provenance

Produce versioned, JSON Schema-validated records for scope and discovery,
dataset observations, resource attempts, content objects, archive versions,
transformations, validation, and publication.

Records must link inputs, outputs, software revision, environment, parameters,
times, hashes, licences, outcomes, and limitations.

### FR-11: Derived representations

The MVP must produce:

- raw CKAN JSON;
- normalized dataset, resource, observation, relationship, attempt, object,
  version, and publication tables;
- Parquet as the primary analytical representation;
- JSONL as a streamable interchange representation;
- explicit schemas and deterministic ordering.

Derivatives must be reproducible from preserved inputs and receipts.

### FR-12: Preservation receipts

The MVP must:

- create WARC 1.1 records when HTTP transaction context is materially required;
- evaluate OCFL, RO-Crate, and BagIt against bounded Treasury fixtures;
- document conformance, tooling maturity, benefits, limitations, and adoption
  decisions;
- avoid claiming conformance until corresponding checks pass.

Full implementation of every evaluated preservation standard is not required
unless an approved amendment promotes it into the track's Must requirements.

### FR-13: Evidence ledger and reporting

Generate paired Markdown and JSON reports that separate:

- discovered;
- eligible;
- attempted;
- captured;
- validated;
- unchanged;
- versioned;
- transformed;
- derivative validated;
- unavailable;
- oversized;
- quarantined;
- restricted;
- failed;
- uploaded;
- remotely verified;
- released.

Each status must include its scope, timestamp, evidence reference, and material
limitations.

### FR-14: Local validation and recovery

The MVP must prove schema validity, object hash integrity, manifest closure,
ledger integrity, deterministic reruns, crash and resume behaviour, idempotent
reconciliation, bounded release reconstruction, and separation of originals and
derivatives.

### FR-15: GitHub Actions automation

Provide least-privilege workflows for:

- pull-request validation;
- scheduled read-only discovery;
- scheduled or manually enabled capture;
- dependency and pre-release compatibility testing;
- security analysis;
- release packaging;
- explicitly gated Hugging Face publication;
- explicitly gated Zenodo preparation and publication;
- remote post-publication verification.

Third-party Actions must be pinned to immutable commit SHAs. Workflow success
must not be reported as archive or publication success without object-level and
remote evidence.

### FR-16: Hugging Face publication

After explicit credential approval, the MVP must:

- create or target the approved `archive-govt-nz` dataset namespace;
- publish the rolling Treasury archive with originals where permitted,
  derivatives, schemas, dataset card, manifests, and evidence;
- use an idempotent upload and reconciliation process;
- verify remote paths, integrity evidence, splits, representative rows, size
  information, and Dataset Viewer state;
- record uploaded and remotely verified states separately.

No token may be printed, stored in the repository, or placed in public evidence.

### FR-17: Zenodo release

After successful local and Hugging Face verification, the MVP must:

- build an immutable release package referencing exact source and derivative
  manifests;
- include checksums, software revision, coverage, rights, provenance, and known
  limitations;
- validate release metadata before upload;
- require explicit approval before creating or publishing a DOI;
- read back and verify the resulting deposition and files;
- distinguish draft, uploaded, published, and remotely verified states.

## Non-functional requirements

### Correctness

- Critical integrity, versioning, policy, credential, recovery, and publication
  logic has 100% line and branch coverage.
- Overall production code has at least 95% line and branch coverage.
- Property and state-machine tests cover invariants.
- Mutation tests exercise critical decision logic.

### Security

- Treat all public metadata, filenames, URLs, redirects, media types, and archive
  contents as untrusted.
- Use resource bounds and fail-closed defaults.
- Quarantine suspicious objects without making them public.
- Redact credentials, signed URLs, authentication headers, personal
  information, and unrelated local paths.
- Use least-privilege workflow permissions and environment-scoped credentials.
- Generate dependency, licence, vulnerability, SBOM, and workflow-security
  evidence.

### Performance and resilience

- Stream resources with bounded memory.
- Support configurable concurrency and backpressure.
- Respect source capacity through identifiable user-agent, rate limits, retry
  bounds, and jitter.
- Avoid repeated transfer of unchanged content when validators are reliable.
- Recover safely from interruption without corrupting accepted objects.

### Portability

- Support local Windows development.
- Use Linux GitHub Actions as canonical CI.
- Keep authoritative records in open, documented formats.
- Do not require an always-on service.

### Maintainability

- Use strict typing, clear domain boundaries, versioned schemas, and deterministic
  generation.
- Maintain a dedicated Rust style guide before introducing Rust code.
- Cross-reference Conductor tasks, GitHub parent issues, nested subissues, pull
  requests, and commits.

## Acceptance criteria

The track is accepted only when:

1. A clean environment can run the documented setup and repository gate.
2. The live Treasury scope is fully reconciled at run time.
3. Every discovered dataset and resource has an explicit terminal or retry state.
4. Every eligible resource is attempted under the approved policy.
5. Accepted objects pass integrity verification and immutable-store checks.
6. A second unchanged run creates no duplicate versions or objects.
7. Change, withdrawal, corruption, quarantine, timeout, oversize, and
   interruption scenarios behave as specified.
8. Normalized JSONL and Parquet outputs validate and reconcile with manifests.
9. A bounded release reconstructs without SQLite, DuckDB, graph, or vector
   database files.
10. Coverage, lint, strict typing, schema, security, mutation, and recovery
    gates pass.
11. Scheduled workflows are safe by default and cannot publish without explicit
    gates.
12. The rolling Hugging Face dataset is uploaded and independently remotely
    verified after credential approval.
13. An immutable Zenodo release is published and remotely verified only after
    explicit DOI approval.
14. Evidence accurately distinguishes local, uploaded, verified, and released
    states.
15. Documentation enables a clean environment to reproduce the bounded archive
    and validation results.

If external credentials or approval are not supplied, implementation may be
locally complete but the track remains explicitly gated rather than falsely
marked fully accepted.

## Out of scope

- Ministry of Health and broader health dataset capture.
- Other government organisations.
- A custom frontend or always-on API.
- Authoritative graph or vector storage.
- Semantic embeddings or retrieval evaluation.
- Automated source deletion mirroring.
- Unbounded capture.
- Private or authenticated government sources without separate approval.
- Full implementation of every preservation standard before evaluation.
- Upstream CKAN library modification without a reproduced defect, maintainer
  fork, tests, and contribution-policy review.
