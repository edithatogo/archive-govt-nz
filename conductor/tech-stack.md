# Technology Stack

## Stack policy

Archive Govt NZ uses current stable releases with locked, reproducible
environments. Dependency automation may test pre-releases and nightly builds,
but production promotion requires compatibility, security, provenance, and
recovery evidence.

Novel components must be replaceable projections rather than authoritative
preservation state.

## Languages

### Python 3.14

Python 3.14 is the primary implementation language for:

- CKAN discovery and metadata retrieval;
- archive orchestration and CLI commands;
- provenance and manifest generation;
- validation and format transformation;
- Hugging Face and Zenodo integration;
- evidence reporting.

Use complete type annotations and strict static analysis.

### Rust

Rust stable may implement proven hot paths such as streaming retrieval, hashing,
archive packaging, or large-manifest verification. A Rust component requires a
benchmark, failure-contract tests, and a demonstrated advantage before adoption.

Use PyO3 and maturin only where an in-process Python binding is preferable to a
stable command or file interface.

## Application architecture

The initial product is a library-first, non-interactive CLI with scheduled jobs.
There is no always-on application service or custom frontend.

Components communicate through typed domain models, versioned manifests,
content-addressed objects, explicit receipts, and stable command contracts.

An HTTP API or web interface may be introduced only for a demonstrated consumer
need and must not become the sole route to archive evidence.

## CKAN integration

- Use the versioned CKAN Action API.
- Use current `ckanapi` for supported API semantics and interoperability.
- Use an async streaming HTTP client for bounded resource downloads, conditional
  requests, redirects, retry policy, range support, and transport evidence.
- Treat `ckanext-archiver` and `ckanutils` as comparative design and upstream
  contribution candidates, not default runtime dependencies.
- Probe the deployed data.govt.nz behaviour rather than assuming it matches the
  newest CKAN server release.
- Preserve CKAN responses before normalization.
- Identify upstream defects with minimal reproductions and local tests before
  proposing an issue or pull request.
- Fork or clone upstream projects under the maintainer's GitHub account before
  modifying them.
- Follow each upstream contribution, authorship, CLA/DCO, disclosure, and
  AI-assistance policy.

## Core Python tooling

- `uv` for Python acquisition, dependency resolution, lockfiles, environments,
  scripts, builds, and dependency groups.
- `pyproject.toml` as the package and tool configuration authority.
- `ckanapi` for CKAN Action API interoperability.
- `httpx` with `anyio` for async, streamed HTTP retrieval.
- `pydantic` and `pydantic-settings` for typed contracts and configuration.
- `cyclopts` for the typed CLI, non-interactive command contracts, and
  structured JSON output.
- `tenacity` or an equivalent bounded retry policy where retries are safe.
- `orjson` only where benchmarks justify it; standards-compatible canonical
  serialization remains authoritative.

## Preservation and provenance formats

### Authoritative layers

- Original metadata responses and source resource bytes.
- SHA-256 for broadly interoperable integrity verification.
- BLAKE3 as an additional high-throughput content identifier where useful.
- Versioned JSON manifests validated by JSON Schema.
- WARC 1.1 records where preserving HTTP transaction context is material.
- OCFL-compatible object layout for durable version inventories.
- RO-Crate and W3C PROV mappings for research-object and transformation
  provenance.
- DCAT-compatible catalogue metadata and Croissant metadata where applicable.
- BagIt-compatible transfer packages for bounded export and recovery workflows.

Adoption of each preservation standard requires a focused design decision and
conformance fixtures; the initial track need not implement every format.

### Derived tabular layers

- Apache Arrow as the in-memory interchange model.
- Parquet as the primary analytical and Hugging Face representation.
- JSON Lines for streamable, diffable interchange where nested records matter.
- CSV only as a compatibility derivative with explicit schema and encoding.
- Polars and PyArrow for typed transformation.
- DuckDB for local analytical validation, reconciliation, and reporting.

No derivative replaces an original object.

## Persistence

### Content-addressed object store

Originals and durable derivatives are immutable objects identified by strong
hashes. Manifests link source identifiers, observations, representations,
transformations, and publications to those objects.

Payloads are excluded from the GitHub source repository.

### SQLite operational ledger

SQLite provides transactional local state for:

- discovery checkpoints;
- capture attempts;
- retry scheduling;
- object and observation relationships;
- publication stages;
- resumability and idempotency.

Use schema migrations, foreign keys, integrity checks, WAL where appropriate,
and deterministic exports. SQLite is operational state, not the only
preservation record.

### Parquet and DuckDB

Versioned Parquet datasets are portable analytical projections. DuckDB queries
them directly for coverage, reconciliation, validation, and reporting. These
outputs must be reproducible from originals and manifests.

## Graph and semantic projections

Represent the archive graph canonically as versioned entity and relationship
tables plus standards-based identifiers.

A dedicated property-graph or RDF engine may be added when benchmarked queries
justify it. Its indexes and database files remain rebuildable derivatives.

Semantic embeddings and vector indexes are optional later-stage derivatives:

- every vector records the source object hash, input selection, model identifier,
  immutable model revision, software environment, parameters, and licence;
- Lance/LanceDB is the preferred first evaluation path;
- DuckDB VSS may be used for bounded experiments;
- vector state never determines preservation truth;
- retrieval quality, drift, bias, cost, and reproducibility require evaluation
  before public claims.

## Publishing

### GitHub

GitHub stores source, schemas, documentation, compact manifests, CI definitions,
issues, and release evidence. Large archive payloads do not enter the source
repository.

GitHub issues use parent issues and nested subissues where supported. Each issue,
pull request, and relevant commit cross-references its Conductor track and task.

### Hugging Face

Hugging Face hosts the rolling dataset archive:

- originals where rights and platform constraints permit;
- Parquet and other purpose-specific derivatives;
- dataset cards;
- provenance and transformation manifests;
- schema and validation artefacts;
- remotely verified publication receipts.

Use Hub revision history and Xet-backed storage where appropriate. Confirm
Dataset Viewer, Parquet endpoints, sizes, splits, and representative records
after publication.

### Zenodo

Zenodo receives intentional, immutable, checksum-pinned release snapshots.
Each deposition records the exact manifest, version, source coverage, rights,
known limitations, software revision, and Hugging Face relationship.

Creating or publishing a DOI remains an explicit external publication gate.

## Quality engineering

### Python

- Ruff for formatting and linting.
- A strict Python type checker.
- pytest for tests.
- Hypothesis for property-based and state-machine testing.
- respx or equivalent deterministic HTTP contract fixtures.
- coverage with branch measurement and risk-based thresholds.
- mutation testing for integrity, versioning, and policy-critical modules.
- JSON Schema conformance and golden-manifest tests.

### Rust

- rustfmt and Clippy with warnings denied.
- cargo-nextest for test execution.
- proptest for property-based testing.
- cargo-mutants for critical logic where practical.
- criterion for benchmark evidence.

### Archive harness

- deterministic fixtures containing no restricted source payloads;
- simulated redirects, partial downloads, retries, timeouts, changed content,
  tombstones, checksum failures, and publication drift;
- record/replay tests with redacted responses;
- crash and resume testing;
- idempotency and reconciliation testing;
- recovery reconstruction from manifests and objects;
- live read-only smoke tests separated from deterministic CI.

Every Conductor implementation track contains a MoSCoW `requirements.md`.
Design-bearing tracks contain `design.md` with Mermaid diagrams covering
components, data flow, trust boundaries, state transitions, and failure paths.

## CI/CD and supply-chain security

GitHub Actions provides pull-request, merge, scheduled, release, and manually
approved publication workflows.

Required automated checks should include, as applicable:

- format, lint, strict typing, unit, property, integration, and recovery tests;
- Python and Rust lockfile verification;
- dependency vulnerability and licence checks;
- CodeQL and secret scanning;
- workflow linting and security analysis;
- pinned third-party Actions;
- generated SBOMs;
- provenance attestations and signed release artefacts;
- reproducible manifest and schema checks;
- least-privilege workflow permissions;
- environment-scoped publication credentials;
- remote post-publication verification.

The bootstrap local gate uses `pip-audit` with the OSV advisory service,
`pip-licenses` with a fail-closed denied-term policy, `detect-secrets` over
source scope, and `cyclonedx-bom` with strict CycloneDX 1.6 validation.
Machine-readable receipts are generated under ignored `build/` paths and are
not treated as hosted evidence.

Dependency automation opens focused updates and runs the full relevant harness.
Pre-release compatibility lanes do not silently update production locks.

The solo-maintainer workflow does not require a second reviewer, CODEOWNERS
approval, team assignment, or mandatory reviewer count. It relies on strong
automated evidence and explicit human gates for credentials, publication,
rights, security exceptions, and destructive actions.

## Initial deployment model

- Local development on Windows with reproducible cross-platform tooling.
- Linux GitHub Actions runners for canonical CI and scheduled archive jobs.
- GitHub for code and evidence.
- Hugging Face for rolling archive datasets.
- Zenodo for immutable citable releases.
- No always-on server, custom frontend, external graph service, or managed vector
  service in the initial implementation.
