# Project Requirements

## Purpose

These project-level requirements define the durable product constraints for
Archive Govt NZ. Implementation tracks refine them into testable task-level
acceptance criteria without silently weakening any Must requirement.

## Must

### Preservation

- Preserve original CKAN metadata responses and retrievable source files without
  unrecorded modification.
- Assign stable identifiers and cryptographic hashes to captured objects.
- Maintain append-only observations and change-driven versions.
- Record unchanged, failed, unavailable, withdrawn, deleted, and restricted
  source states.
- Preserve withdrawn versions with tombstones unless a verified legal, privacy,
  security, or rights decision requires restriction or removal.
- Keep original objects distinct from every derivative.

### Provenance and transparency

- Record discovery, retrieval, HTTP, time, source, licence, integrity, tool,
  environment, transformation, validation, and publication evidence.
- Produce complete transformation receipts that identify inputs, outputs,
  versions, parameters, validation, and known information loss.
- Provide paired human-readable Markdown and machine-readable, schema-validated
  evidence.
- Separate discovered, eligible, attempted, captured, validated, transformed,
  uploaded, remotely verified, and released states.

### Scope and priority

- Support data.govt.nz through the versioned CKAN Action API.
- Establish Treasury as the first organisational archive priority.
- Establish the Ministry of Health as the second organisational priority.
- Reconcile broader health and healthcare discovery through organisation, CKAN
  group, search, and complementary non-CKAN sources.

### Storage and release

- Store original and durable derived payloads in content-addressed object
  storage outside the GitHub source repository.
- Use a transactional SQLite operational ledger with deterministic exports.
- Provide versioned Parquet analytical projections compatible with DuckDB and
  Hugging Face.
- Maintain a rolling Hugging Face dataset archive.
- Produce intentional, immutable, checksum-pinned Zenodo release snapshots.
- Independently verify remote publication before reporting it as successful.

### Engineering and security

- Use Python 3.14 as the primary language and admit Rust only for benchmarked
  hot paths.
- Provide a typed, non-interactive CLI and scheduled jobs without requiring an
  always-on service.
- Use locked, reproducible environments and current stable dependencies.
- Require 100% line and branch coverage for critical integrity, policy,
  credential, versioning, and publication logic.
- Require at least 95% line and branch coverage overall.
- Use deterministic, redacted fixtures and fail-closed handling of credentials,
  signed URLs, personal information, and sensitive payloads.
- Test idempotency, interruption, retry, reconciliation, integrity, and recovery.
- Keep human, credential, publication, rights, security-exception, destructive,
  and external-system gates explicit.

### Planning and traceability

- Give every implementation track a MoSCoW `requirements.md`.
- Give every design-bearing track a `design.md` with Mermaid diagrams.
- Cross-reference Conductor tracks with GitHub parent issues and nested
  subissues where supported.
- Use task-sized commits only after the relevant automated gates and evidence
  are complete.
- Support a solo maintainer without mandatory second-person review,
  CODEOWNERS approval, team assignment, or reviewer-count gates.

## Should

- Preserve material HTTP transaction context in WARC 1.1 records.
- Use an OCFL-compatible object layout and evaluate conformance tooling.
- Export RO-Crate, W3C PROV, DCAT, and Croissant-compatible metadata where the
  source and representation permit it.
- Provide BagIt-compatible bounded transfer and recovery packages.
- Use SHA-256 for interoperability and BLAKE3 as an additional high-throughput
  identity where justified.
- Provide property, state-machine, mutation, contract, and recovery testing for
  risk-bearing behaviour.
- Generate SBOMs, provenance attestations, signed release artefacts, and
  least-privilege workflow evidence.
- Evaluate upstream CKAN tools through reproducible tests before replacing or
  contributing to them.

## Could

- Add a read-only static archive status site generated from the evidence ledger.
- Add an HTTP API when a demonstrated consumer requires one.
- Publish graph projections derived from versioned entity and relationship
  tables.
- Publish reproducible embeddings and Lance/LanceDB vector indexes for semantic
  discovery.
- Use Rust components for retrieval, hashing, packaging, or verification after
  benchmarks demonstrate a material benefit.
- Support additional government catalogues and non-CKAN sources.
- Provide Arrow Flight or another high-performance access layer when scale and
  consumers justify it.

## Won't, for the initial implementation

- Run an always-on backend service.
- Build a custom interactive frontend.
- Treat a graph or vector database as authoritative preservation state.
- Store large archive payloads in the GitHub source repository.
- Mirror source deletion by automatically erasing preserved history.
- Publish a Zenodo DOI without an explicit release decision.
- Modify upstream libraries or submit upstream issues or pull requests without
  first reproducing the need locally and reviewing contribution and AI
  disclosure requirements.
- Claim complete coverage, successful publication, or recoverability from a
  green workflow alone.
