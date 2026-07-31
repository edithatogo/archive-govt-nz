# Treasury Archive MVP Implementation Plan

## Track controls

- Track type: MVP / Bootstrap
- Execution mode: continuous autonomous across tasks, phases, checkpoints,
  reviews, and approved subsequent tracks
- Decision protocol: ask only at defined decision gates; provide options,
  recommendation, rationale, evidence, and continuing safe work
- GitHub model: one parent issue with one nested subissue per phase
- Coverage: 100% line and branch for critical logic; at least 95% overall
- Commit policy: one coherent commit after each completed task and its evidence
- External gates: repository creation, issues, credentials, Hugging Face
  publication, Zenodo deposition and DOI, rights exceptions, quarantine
  release, and destructive actions

## Phase 1: Repository and assurance foundation

- [x] Task: Establish GitHub and Conductor traceability [M-19]
  - [x] Create or confirm `edithatogo/archive-govt-nz`
  - [x] Configure and verify the local `github` remote
  - [x] Create the parent issue referencing this track
  - [x] Create and read back nested phase subissues
  - [x] Record repository and issue identifiers in track evidence

- [x] Task: Write failing package and CLI bootstrap tests [M-01]
  - [x] Test package import and version metadata
  - [x] Test non-interactive CLI help and structured JSON output
  - [x] Test documented exit-state semantics
  - [x] Run and record the expected red phase

- [x] Task: Implement the Python 3.14 project foundation [M-01]
  - [x] Create `pyproject.toml`, dependency groups, and `uv.lock`
  - [x] Create the typed package and CLI entrypoint
  - [x] Add deterministic configuration loading
  - [x] Make bootstrap tests green

- [x] Task: Establish the repository-wide assurance harness [M-01, M-18]
  - [x] Configure Ruff, strict typing, pytest, and branch coverage
  - [x] Configure Hypothesis and JSON Schema validation
  - [x] Add one non-interactive repository gate command
  - [x] Test the gate against representative violations
  - [x] Run and record the green gate

- [x] Task: Establish supply-chain and repository controls [M-15, S-03]
  - [x] Configure dependency, licence, vulnerability, and secret scans
  - [x] Add SBOM generation and validation
  - [x] Add security, contribution, authorship, and AI guidance
  - [x] Add a project-specific Rust guide before any Rust code
  - [x] Enforce benchmark evidence before Rust adoption

- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md)
  - [x] Run the full repository gate
  - [x] Verify setup from a clean environment
  - [x] Reconcile Conductor and GitHub state
  - [x] Record phase evidence and checkpoint

## Phase 1A: Autonomous execution governance

- [x] Task: Establish continuous autonomous Conductor execution [M-19]
  - [x] Define uninterrupted task, phase, and track progression
  - [x] Define the minimal decision-gate taxonomy
  - [x] Require options, recommendation, rationale, and evidence for decisions
  - [x] Add bounded retry, recovery, resumability, and isolation controls
  - [x] Add paired human-readable and machine-readable policy artefacts
  - [x] Validate policy and current-track inheritance
  - [x] Reconcile the GitHub issue hierarchy

## Phase 2: CKAN capability and Treasury scope discovery

- [x] Task: Write failing CKAN envelope and capability tests [M-02]
  - [x] Test CKAN success and error envelopes independently of HTTP status
  - [x] Test non-200, malformed, timeout, retryable, and terminal outcomes
  - [x] Test sensitive-value redaction
  - [x] Run and record the expected red phase

- [x] Task: Implement the CKAN envelope and redaction kernel [M-02, S-02]
  - [x] Validate success and error envelopes independently of HTTP status
  - [x] Classify retryable, terminal, timeout, and unknown failures
  - [x] Redact sensitive headers, nested values, and signed query parameters
  - [x] Preserve source documents without mutation
  - [x] Make focused capability contracts green

- [x] Task: Write failing bounded CKAN HTTP client tests [M-02, S-02]
  - [x] Test the versioned Action API path and identifiable user agent
  - [x] Test time bounds, retry limits, backoff, and jitter
  - [x] Test raw response and bounded transport receipts
  - [x] Test capability observation records
  - [x] Run and record the expected red phase

- [x] Task: Implement the bounded CKAN HTTP client [M-02, S-02]
  - [x] Use async streamed HTTP with explicit resource bounds
  - [x] Apply retry policy only to classified safe failures
  - [x] Preserve raw responses and redacted transport metadata
  - [x] Record catalogue and CKAN capability observations
  - [x] Make bounded client tests green

- [x] Task: Write failing Treasury discovery tests [M-03]
  - [x] Test organisation name and stable-ID resolution
  - [x] Test pagination, count drift, duplicates, and missing identifiers
  - [x] Test deterministic raw-page and scope manifests
  - [x] Test changed counts without hard-coding 54
  - [x] Run and record the expected red phase

- [x] Task: Implement complete Treasury discovery [M-03, M-04]
  - [x] Resolve and verify `the-treasury`
  - [x] Enumerate and reconcile all organisation-filtered datasets
  - [x] Preserve raw discovery responses
  - [x] Produce dated scope and coverage manifests
  - [x] Produce paired Markdown and JSON discovery reports
  - [x] Make discovery tests green

- [x] Task: Add bounded live read-only contract checks [M-02, M-03]
  - [x] Separate deterministic fixtures from live tests
  - [x] Probe deployed CKAN and representative Treasury metadata
  - [x] Record observation times and response hashes
  - [x] Prevent live count drift from causing false failures
  - [x] Document source-friendly operation

- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md)
  - [x] Run deterministic and bounded live checks
  - [x] Verify complete live scope reconciliation
  - [x] Review response redaction and provenance
  - [x] Record phase evidence and checkpoint

## Phase 3: Schemas, policy, and content-addressed storage

- [x] Task: Define versioned archive schemas [M-10]
  - [x] Define capability, scope, dataset, resource, attempt, object, version,
        transformation, validation, and publication schemas
  - [x] Define compatibility and migration rules

- [x] Task: Write failing schema and invariant tests [M-10]
  - [x] Test valid minimal and complete records
  - [x] Test missing identifiers, invalid times, and invalid transitions
  - [x] Test original and derivative role separation
  - [x] Test deterministic canonical serialization
  - [x] Run and record the expected red phase

- [x] Task: Implement typed domain models and schemas [M-10]
  - [x] Map typed models to JSON Schema
  - [x] Enforce identifiers, UTC times, states, and limitations
  - [x] Generate and validate deterministic schemas
  - [x] Make schema tests green

- [x] Task: Define the fail-closed resource policy [M-05]
  - [x] Version scheme, redirect, time, byte, storage, and concurrency rules
  - [x] Define decompression, archive-member, type, and filename rules
  - [x] Define rights, access, quarantine, retry, and exception states
  - [x] Document operator override and audit requirements

- [x] Task: Write failing resource-policy property tests [M-05, M-18]
  - [x] Generate unsafe schemes, redirects, names, types, sizes, and archives
  - [x] Test restricted, oversized, quarantine, and retry transitions
  - [x] Test that every resource receives an explicit outcome
  - [x] Run and record the expected red phase

- [x] Task: Implement resource-policy evaluation [M-05]
  - [x] Implement preflight and independent type evidence
  - [x] Sanitize source filenames as metadata only
  - [x] Produce versioned decisions
  - [x] Make property tests green
  - [x] Mutation-test critical branches

- [x] Task: Write failing object-store tests [M-07]
  - [x] Test SHA-256, BLAKE3, atomic promotion, and deduplication verification
  - [x] Test corrupt objects, interruption, cleanup, and path traversal
  - [x] Run and record the expected red phase

- [x] Task: Implement immutable content-addressed storage [M-07]
  - [x] Stream hashes while writing and promote only verified objects
  - [x] Prevent mutable overwrite
  - [ ] Record roles and source relationships (ledger task)
  - [x] Keep payload roots outside GitHub
  - [x] Make object-store tests green
  - [ ] Mutation-test integrity decisions (covered by object-integrity gate)

- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
  - [ ] Run schema, property, mutation, and object-integrity gates
  - [ ] Verify critical coverage is 100% line and branch
  - [ ] Review defaults and exception controls
  - [ ] Record phase evidence and checkpoint

## Phase 4: Streaming capture, ledger, and versioning

- [x] Task: Write failing streaming-capture tests [M-06]
  - [x] Test bounded response bytes and immutable promotion
  - [x] Test declared over-limit streams and retryable/terminal classification
  - [ ] Test redirects, validators, ranges, quarantine, and redaction
  - [x] Run and record the expected red phase

- [~] Task: Implement bounded streaming capture [M-06, S-02]
  - [x] Apply byte policy before and during transfer
  - [x] Stream through bounded chunks to atomic temporary objects
  - [ ] Enforce time, redirect, decompression, storage, and concurrency bounds
  - [ ] Record transport and attempt receipts
  - [x] Promote only verified objects
  - [x] Make streaming tests green

- [x] Task: Write failing SQLite ledger tests [M-08]
  - [x] Test constraints, transactions, checkpoints, and resumability
  - [x] Test restart, deterministic export, and migrations
  - [x] Run and record the expected red phase

- [~] Task: Implement the operational ledger [M-08]
  - [x] Create migrations, foreign keys, and WAL configuration
  - [~] Persist observations, attempts, objects, versions, and publications
  - [x] Add deterministic observation export and integrity constraints
  - [x] Make ledger tests green

- [x] Task: Write failing change-driven versioning tests [M-09]
  - [x] Test first, unchanged, and resource-changed states
  - [x] Test tombstone preservation
  - [ ] Test resource disappearance and policy changes
  - [x] Run and record the expected red phase

- [~] Task: Implement change detection and version relationships [M-09]
  - [x] Separate observation from source modification time
  - [x] Canonicalize comparison inputs
  - [x] Version only material change and record unchanged evidence
  - [x] Create tombstones without deleting history
  - [x] Make versioning tests green
  - [x] Mutation-test critical state transitions

- [~] Task: Prove idempotency and recovery [M-14]
  - [ ] Interrupt every persistent boundary
  - [ ] Resume without duplicate objects or versions
  - [x] Reconcile ledger and object store
  - [x] Detect orphaned and missing/corrupt objects
  - [ ] Verify repeated unchanged runs

- [x] Task: Phase Verification & Checkpoint (Refer to workflow.md)
  - [x] Run capture, ledger, versioning, and mutation gates
  - [ ] Verify critical coverage thresholds (defensive capture/object branches remain open)
  - [x] Review bounds and source-friendly behaviour
  - [x] Record phase evidence and checkpoint

## Phase 5: Provenance, derivatives, and preservation evaluation

- [x] Task: Write failing provenance and manifest tests [M-10]
  - [x] Test manifest closure and required provenance fields
  - [x] Test missing relationships and deterministic serialization
  - [x] Test original and derivative separation
  - [x] Run and record the expected red phase

- [~] Task: Implement versioned manifests and receipts [M-10, M-13]
  - [x] Produce closed observation, object, version, and derivative manifests
  - [ ] Produce transformation, validation, and publication receipts
  - [ ] Link software, environment, parameters, rights, and limitations
  - [x] Validate deterministic serialization and relationships
  - [x] Make manifest tests green

- [x] Task: Write failing derivative transformation tests [M-11]
  - [x] Test normalized dataset entities and resource counts
  - [x] Test nested and unknown CKAN fields
  - [x] Test deterministic Parquet and JSONL semantics
  - [x] Test reconciliation with DuckDB
  - [x] Run and record the expected red phase

- [~] Task: Implement core interoperable derivatives [M-11]
  - [ ] Preserve raw CKAN JSON (capture boundary)
  - [x] Generate normalized JSONL and typed Parquet
  - [x] Record transformation versions and information loss
  - [x] Reconcile derivatives with DuckDB
  - [x] Make derivative tests green

- [~] Task: Implement material WARC receipts [M-12]
  - [x] Define material HTTP context
  - [x] Write failing WARC round-trip and redaction tests
  - [x] Generate bounded WARC 1.1 records
  - [x] Verify sensitive-value absence
  - [x] Verify object relationships in release manifests

- [x] Task: Evaluate preservation packaging standards [S-01]
  - [x] Create bounded evaluation scope for Treasury-derived fixtures
  - [x] Evaluate OCFL, RO-Crate, and BagIt
  - [x] Record tooling, security, benefits, gaps, and maintenance
  - [ ] Produce adoption decisions without unsupported conformance claims

- [x] Task: Generate the paired evidence ledger [M-13]
  - [x] Produce machine-readable stage records and Markdown summaries
  - [ ] Reconcile raw, ledger, manifest, and derivative counts
  - [x] Test that every discovered resource has an outcome (fixture scope)

- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
  - [ ] Run schema, provenance, derivative, WARC, and reconciliation gates
  - [ ] Verify bounded reconstruction
  - [ ] Review preservation claims
  - [ ] Record phase evidence and checkpoint

## Phase 6: Complete Treasury capture and recovery proof

- [x] Task: Perform pre-capture live reconciliation [M-03, M-05]
  - [x] Re-run CKAN capability and complete Treasury discovery
  - [x] Compare current scope with the dated 54-dataset baseline
  - [x] Review storage estimates, policy, and rate controls
  - [ ] Obtain explicit capture/publication authority at the release gate
  - [ ] Produce a no-download operator preview

- [~] Task: Execute complete eligible Treasury capture [M-04, M-06]
  - [x] Enumerate every resource under the approved policy
  - [x] Enforce total-byte, resource-count, and concurrency budgets before transfer
  - [ ] Attempt every resource under the approved policy
  - [ ] Preserve every raw dataset response
  - [ ] Record captured, unavailable, restricted, oversized, quarantined,
        retryable, and terminal outcomes
  - [x] Keep suspicious content outside publication roots
  - [ ] Produce bounded progress and checkpoint evidence

- [ ] Task: Reconcile complete capture coverage [M-13, M-14]
  - [ ] Compare discovery, attempts, objects, versions, and derivatives
  - [ ] Verify no dataset or resource disappeared silently
  - [ ] Resolve safe retries within policy
  - [ ] Record unresolved limitations
  - [ ] Generate final local coverage reports

- [ ] Task: Prove unchanged rerun behaviour [M-09, M-14]
  - [ ] Repeat discovery and eligible capture
  - [ ] Verify no duplicate objects or material versions
  - [ ] Verify unchanged evidence and avoided transfers

- [ ] Task: Execute recovery reconstruction [M-14]
  - [ ] Select a bounded representative release manifest
  - [ ] Reconstruct without SQLite or DuckDB
  - [ ] Verify object and derivative hashes
  - [ ] Verify manifest closure and provenance
  - [ ] Record commands, time, and limitations

- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
  - [ ] Run the complete local quality and archive gate
  - [ ] Verify coverage thresholds
  - [ ] Review quarantine, rights, and unresolved states
  - [ ] Record local completion without external-publication claims
  - [ ] Record phase evidence and checkpoint

## Phase 7: Hardened CI/CD and scheduled archival

- [x] Task: Write failing workflow-policy tests [M-15]
  - [x] Test permissions, immutable Action pins, and publication gates
  - [x] Test credential-free pull-request CI and payload exclusions
  - [x] Test logs and artefacts for sensitive values
  - [x] Run and record the expected red phase

- [~] Task: Implement pull-request and main CI [M-15, S-03]
  - [x] Run quality, coverage, schema, dependency, licence, and security gates
  - [x] Generate SBOM and bounded evidence artefacts
  - [x] Make workflow-policy tests green

- [x] Task: Implement safe scheduled discovery [M-15]
  - [x] Use least-privilege read-only defaults
  - [x] Reconcile capability and Treasury scope
  - [x] Produce drift evidence without payload commits or publication
  - [x] Test concurrency controls

- [~] Task: Implement scheduled capture controls [M-15]
  - [x] Require explicit enablement
  - [ ] Enforce storage, duration, concurrency, and source-rate budgets
  - [ ] Support resumable checkpoints and bounded failures
  - [x] Exclude quarantined and restricted objects

- [x] Task: Implement dependency and pre-release lanes [S-04]
  - [x] Configure focused dependency/update observation lane
  - [x] Test stable and isolated pre-release compatibility
  - [x] Prevent pre-release lanes from rewriting production locks

- [~] Task: Add release attestations [S-03]
  - [x] Generate checksums, SBOMs, and provenance attestations
  - [ ] Sign where supported and verify before publication

- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
  - [ ] Run local workflow policy checks
  - [ ] Verify hosted CI separately after push
  - [ ] Record run identifiers and evidence
  - [ ] Record phase checkpoint

## Phase 8: Rolling Hugging Face publication

- [x] Task: Define and test the Hugging Face contract [M-16]
  - [x] Define namespace, layout, dataset card, rights, and state model
  - [x] Write failing publication-state and idempotency tests
  - [x] Run and record the expected red phase

- [~] Task: Implement credential-safe publishing [M-16]
  - [x] Require environment-scoped `HF_TOKEN`
  - [x] Prevent token output or persistence
  - [x] Implement dry-run preparation
  - [x] Exclude restricted and quarantined objects
  - [x] Make publication tests green

- [ ] Task: Prepare the rolling Treasury dataset [M-16]
  - [ ] Generate the card, permitted originals, derivatives, and evidence
  - [ ] Verify the upload manifest and storage estimate
  - [ ] Obtain credential and publication approval

- [ ] Task: Publish and remotely verify Hugging Face [M-16]
  - [ ] Create or target the approved dataset repository
  - [ ] Upload the exact reviewed manifest
  - [ ] Read back revision, paths, and integrity evidence
  - [ ] Verify representative records, sizes, Parquet, and Viewer state
  - [ ] Record upload and remote verification separately

- [ ] Task: Reconcile rolling update behaviour [M-16]
  - [ ] Verify unchanged idempotency
  - [ ] Verify a bounded changed version and history
  - [ ] Verify tombstones do not erase prior history

- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
  - [ ] Run publication and remote-readback gates
  - [ ] Reconcile local and Hugging Face manifests
  - [ ] Record repository, revision, Viewer, and checkpoint evidence

## Phase 9: Immutable Zenodo release

- [x] Task: Define and test the Zenodo contract [M-17]
  - [x] Define versioning, contents, checksums, metadata, and state model
  - [x] Write failing release-state and metadata tests
  - [x] Run and record the expected red phase

- [~] Task: Implement deterministic release packaging [M-17]
  - [ ] Select an exact verified Treasury manifest
  - [x] Package explicitly listed artefacts without hidden mutable state
  - [x] Include checksum-pinned package metadata
  - [x] Validate reproducibility
  - [x] Make packaging tests green

- [ ] Task: Implement credential-safe Zenodo integration [M-17]
  - [ ] Require environment-scoped token and prevent leakage
  - [ ] Implement dry-run, draft creation, and upload reconciliation
  - [ ] Require explicit DOI confirmation
  - [ ] Make integration tests green against mocks or sandbox

- [~] Task: Prepare the first Treasury release candidate [M-17]
  - [ ] Reconcile the exact Hugging Face revision
  - [x] Generate metadata and related identifiers
  - [x] Verify rights exclusions and checksums for available evidence
  - [x] Present a local immutable preview without publication

- [ ] Task: Publish and remotely verify Zenodo [M-17]
  - [ ] Create or update the reviewed draft
  - [ ] Upload the exact checksum-pinned release
  - [ ] Obtain explicit DOI publication approval
  - [ ] Publish and read back DOI, metadata, files, sizes, and checksums
  - [ ] Record published and remotely verified states separately

- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
  - [ ] Reconcile local, Hugging Face, and Zenodo manifests
  - [ ] Verify immutable release recovery
  - [ ] Record deposition, DOI, remote evidence, and checkpoint

## Phase 10: MVP closeout and next-scope handoff

- [ ] Task: Run complete acceptance verification [M-01 through M-19]
  - [ ] Run every deterministic quality gate
  - [ ] Run bounded live CKAN verification
  - [ ] Reconcile complete current Treasury scope and outcomes
  - [ ] Verify local recovery and remote publication states
  - [ ] Confirm no Must requirement lacks evidence

- [ ] Task: Complete security and provenance self-review [M-18]
  - [ ] Review secrets, logs, fixtures, resource policy, quarantine, and rights
  - [ ] Review dependency and workflow findings
  - [ ] Review completeness and publication claims
  - [ ] Resolve or explicitly block every critical finding

- [ ] Task: Publish final evidence ledger [M-13, M-19]
  - [ ] Generate final Markdown and JSON reports
  - [ ] Reconcile counts and remote identifiers
  - [ ] Record limitations, commands, and revisions
  - [ ] Cross-reference issues, pull requests, commits, and Conductor

- [ ] Task: Define the next bounded tracks
  - [ ] Propose Ministry of Health and broader health discovery tracks
  - [ ] Propose adopted preservation-standard follow-up tracks
  - [ ] Propose graph or vector evaluation only if justified
  - [ ] Keep later work outside this MVP's claims

- [ ] Task: Phase Verification & Checkpoint (Refer to workflow.md)
  - [ ] Run final clean-environment reproduction
  - [ ] Reconcile all track artefacts and registries
  - [ ] Confirm hosted and publication evidence is current
  - [ ] Record final checkpoint and review
