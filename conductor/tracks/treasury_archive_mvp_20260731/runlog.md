# Treasury Archive MVP Run Log

## 2026-07-31 - Planning

- Confirmed track classification: MVP / Bootstrap.
- Confirmed complete live Treasury metadata and eligible-resource capture
  boundary.
- Confirmed gated full Hugging Face and Zenodo vertical slice.
- Confirmed core Parquet, JSONL, manifest, hash, and material WARC outputs.
- Confirmed bounded OCFL, RO-Crate, and BagIt evaluation.
- Confirmed configurable fail-closed resource policy.
- Live read-only probe observed CKAN 2.10.9 and 54 Treasury datasets.
- No dataset resource payloads were downloaded during planning.
- No GitHub repository, issue, Hugging Face dataset, or Zenodo deposition was
  created during planning.

## 2026-07-31 - Task: Establish GitHub and Conductor traceability

- Marked the track in progress and committed the state transition as `5c4582d`.
- Confirmed authenticated GitHub CLI account `edithatogo`.
- Confirmed no repository named `archive-govt-nz` existed under that account.
- Created public repository `edithatogo/archive-govt-nz`.
- Added local remote `github` and pushed `main`.
- Verified the remote and local head were identical at
  `5c4582d9dc1916b05ba0305802293345b35825cf` before the task evidence commit.
- Created parent issue #1 and phase issues #2 through #11.
- Attached all ten phase issues through GitHub's native subissues API.
- Read back the parent, all ten subissues, visibility, default branch, and
  remote head.
- GitHub connector issue creation returned 403 for the new repository; used the
  authenticated CLI fallback with exact-title idempotency checks.

## 2026-07-31 - Task: Write failing package and CLI bootstrap tests

- Added bootstrap tests for package/distribution version agreement.
- Added subprocess tests for non-interactive help and structured version JSON.
- Defined the expected stable process exit-code contract.
- Red command:
  `uvx --python 3.14 --from pytest pytest tests/test_package_bootstrap.py tests/test_cli_bootstrap.py -q`
- Expected red result: two collection errors because `archive_govt_nz` did not
  yet exist.
- Observed a non-fatal transient Windows `uv` cache rename warning after pytest
  installation; it did not change the failure cause.

## 2026-07-31 - Task: Implement the Python 3.14 project foundation

- Added the `archive-govt-nz` distribution and `archive_govt_nz` source
  package with a Python `>=3.14` runtime contract.
- Selected Cyclopts 4.22.3 as the typed CLI framework and resolved the
  production and development environment into `uv.lock`.
- Added stable process outcome codes and deterministic JSON for
  `version --format json`.
- Added an immutable settings value object that resolves only explicit caller
  input; ambient configuration discovery is intentionally deferred.
- Green command:
  `uv run --locked pytest tests/test_package_bootstrap.py tests/test_cli_bootstrap.py -q`
- Final green result: 5 tests passed in 1.84 seconds on CPython 3.14.6,
  including explicit configuration resolution.
- Console-script checks:
  `uv run --locked archive-govt-nz version --format json` and
  `uv run --locked archive-govt-nz --help`; both exited successfully without
  standard-error output.
- Build check: `uv build --no-sources` produced the source distribution and
  platform-independent wheel successfully. Generated `dist/` content remains
  ignored and is not repository evidence.

## 2026-07-31 - Task: Establish the repository-wide assurance harness

- Red command:
  `uv run --locked pytest tests/test_assurance_harness.py -q`
- Expected red result: four failures for absent assurance dependencies, policy,
  gate script, and importable gate orchestration.
- Added locked Ruff 0.16.1, Pyright 1.1.411, pytest-cov 7.1.0, Hypothesis
  6.164.0, and jsonschema 4.26.0.
- Configured Ruff's full ruleset with narrow documented boundary exceptions,
  strict Pyright, strict pytest configuration, branch coverage, and a 95%
  fail-under threshold.
- Added `uv run --locked python tools/check.py` as the single portable,
  non-interactive gate.
- Added fail-fast stage tests. A simulated status 23 stopped the later stage
  and was returned unchanged; successful stages ran in order.
- Intermediate full-gate runs correctly stopped on lint findings, strict
  third-party JSON typing boundaries, and 64% subprocess-only coverage.
- Resolved findings without weakening strict typing or the coverage threshold.
- Final gate command:
  `uv run --locked python tools/check.py`
- Final result: lock consistent; 31 files formatted; Ruff passed; Pyright
  reported 0 errors and 0 warnings; 14 tests passed; overall line and branch
  coverage was 100%; the final recorded test run took 4.93 seconds; one Draft
  2020-12 schema and fixture validated.

## 2026-07-31 - Task: Establish supply-chain and repository controls

- Red command:
  `uv run --locked pytest tests/test_supply_chain_controls.py -q`
- Expected red result: three failures for missing gate stages, governance
  documents, and supply-chain tool.
- Verified current upstream releases before locking: pip-audit 2.10.1,
  pip-licenses 5.5.5, CycloneDX BOM 7.3.x, and detect-secrets 1.5.0.
- Added dependency vulnerability, licence, secret, and SBOM stages to the
  authoritative repository gate.
- The initial PyPI advisory lookup timed out during TLS after 15 seconds. The
  bounded OSV backend completed successfully and found no known vulnerabilities.
- The first secret scan reported two generated cache-tag hashes. Added explicit
  exclusions for ignored `.pytest_cache` and `.ruff_cache` content; the source
  scan then passed with zero candidates.
- Licence inventory passed the denied-term policy.
- Generated a reproducible CycloneDX 1.6 JSON SBOM with 69 components and
  validated it with the library's strict official-schema validator.
- Added Apache-2.0 licence text, security reporting, contribution, authorship,
  AI-use, Rust engineering, and benchmark-evidence policies.
- Final command: `uv run --locked python tools/check.py`.
- Final post-documentation result: all ten stages passed in 85.6 seconds; 17
  tests passed in 5.46 seconds with 100% measured line and branch coverage.

## 2026-07-31 - Phase 1 verification and checkpoint

- Reused the final ten-stage repository-gate result from the completed
  supply-chain task.
- Isolated verification:
  `uv run --isolated --locked python -m archive_govt_nz --help`.
- Isolated test command:
  `uv run --isolated --locked pytest --cov=archive_govt_nz --cov-branch --cov-report=term-missing`.
- The isolated environment installed 69 packages; 17 tests passed in 10.60
  seconds with 100% measured line and branch coverage.
- `uv build --no-sources` rebuilt the `0.1.0` sdist and platform-independent
  wheel successfully.
- Read back the public, unarchived GitHub repository, default `main`, open
  parent #1, and all ten native phase subissues.
- `github/main` exactly matched local
  `45420f3c153b95628fabfd8de83f92a3f5054fba` before checkpoint evidence.
- The post-checkpoint secret scan identified the explicit Git hash in
  `source_revision`. Added a key-scoped line exclusion for only
  `source_revision` and `remote_revision`; the complete source scan then passed
  with zero candidates.
- Phase 1 issue #2 remains open until this checkpoint commit is pushed and read
  back; its close action is an external receipt, not assumed local state.

## 2026-07-31 - Task: Establish continuous autonomous Conductor execution

- Red command:
  `uv run --locked pytest tests/test_conductor_autonomy.py -q`.
- Expected red result: four failures for absent policy, schema, and track
  inheritance.
- Compared bundled Conductor `0.3.0` at `fb6212e8` with live upstream `main`
  `0.3.0` at `99ba10e1`.
- Evaluated open draft PR #86 (Ralph/architect loop) and draft PR #161
  (worktree isolation). Adopted bounded-loop, completion-state, isolation, and
  recovery concepts without vendoring experimental Gemini/shell code.
- Added paired `conductor/autonomy.md` and schema-validated
  `conductor/autonomy-policy.json`.
- Updated the project workflow, requirements, design, product guidance,
  registry, active track specification, requirements, plan, design, index, and
  metadata.
- Added automatic review/fix/document synchronization and approved-track
  handoff without routine confirmation.
- Added three distinct corrective attempts, failure classification,
  branch-local blocking, continued independent work, resumability, and
  conditional branch/worktree isolation.
- Green focused result: four autonomy tests passed; two schemas and documents
  validated.
- Created and read back native parent subissue
  [#12](https://github.com/edithatogo/archive-govt-nz/issues/12).
- Final command: `uv run --locked python tools/check.py`.
- Final result: all ten stages passed in 103.6 seconds; 21 tests passed in 8.03
  seconds with 100% measured line and branch coverage; two schemas validated;
  OSV reported no known vulnerabilities; licence, secret, and 69-component
  CycloneDX SBOM controls passed.

## 2026-07-31 - Task: Write failing CKAN envelope and capability tests

- Added public contracts for CKAN Action success and error envelopes independent
  of HTTP transport status.
- Added retryable 429/5xx, terminal 404, malformed document, timeout, unknown
  transport failure, nested credential, header, and signed-URL cases.
- Required unknown failures to default terminal and diagnostic strings to omit
  private exception details.
- Red command:
  `uv run --locked pytest tests/ckan/test_envelope.py tests/ckan/test_redaction.py -q`.
- Expected red result: two collection errors because
  `archive_govt_nz.ckan` does not exist.

## 2026-07-31 - Task: Implement the CKAN envelope and redaction kernel

- Added typed immutable successful Action responses and bounded exception
  classes for protocol, Action, HTTP-status, timeout, and unknown transport
  outcomes.
- HTTP and CKAN envelope states are validated independently. Unknown failures
  default terminal and exception text is not retained.
- Added recursive copy-on-redact behavior for mappings and lists, normalized
  sensitive field matching, and query-aware URL redaction.
- Corrected the redaction assertion from four to five markers: the fixture
  contains Authorization, Cookie, API key, token, and AWS signature values.
- Green command:
  `uv run --locked pytest tests/ckan/test_envelope.py tests/ckan/test_redaction.py -q`.
- Final focused result: 19 tests passed in 0.92 seconds with 100% line and
  branch coverage for CKAN modules; strict Pyright reported no errors.
- Refined the remaining async HTTP client work into separate red and green tasks
  so raw transport, retry, timing, user-agent, and observation contracts are not
  claimed by this kernel.

## 2026-07-31 - Task: Write failing bounded CKAN HTTP client tests

- Locked AnyIO 4.14.2, ckanapi 4.11, and HTTPX 0.28.1 for the Python 3.14
  runtime; HTTPX 1.0 development releases remain outside the production lock.
- Added deterministic `httpx.MockTransport` contracts for the versioned Action
  path, identifiable user agent, bounded attempts, exponential backoff,
  timeout classification, exact raw bytes, SHA-256, safe response headers,
  response-size rejection, and CKAN capability observations.
- Retry tests inject clock, sleep, and jitter dependencies and make no live
  request or elapsed-time assumption.
- Red command: `uv run --locked pytest tests/ckan/test_client.py -q`.
- Expected red result: collection stops at `ModuleNotFoundError` for the absent
  `archive_govt_nz.ckan.client` implementation.
- Ruff passes for the red contract file. No catalogue access, credential,
  payload capture, or publication action occurred.

## 2026-07-31 - Task: Implement the bounded CKAN HTTP client

- Added an async context-managed HTTPX client with an explicit catalogue URL,
  user agent, timeout, maximum attempts, exponential backoff, jitter, response
  byte limit, disabled redirects, and identity content encoding.
- Streamed unbuffered bodies incrementally and bounded pre-buffered test
  responses independently of trusted `Content-Length` metadata.
- Restricted Action names to stable identifiers so caller input cannot alter
  the versioned `/api/3/action/` path.
- Classified timeouts and network errors as bounded retry candidates. Unknown
  HTTPX failures and terminal statuses fail without retry or private exception
  text.
- Preserved exact received bytes, SHA-256, UTC observation time, safe response
  headers, and per-attempt status/error-class receipts.
- Added typed capability observations requiring string CKAN version and site
  identity fields.
- Green focused result: 18 client tests; 100% of 165 statements and 40
  branches; Ruff and strict Pyright clean.
- Green CKAN result: 37 tests. Full result: 58 tests and 100% of 292 statements
  and 70 branches. Source secret scan passed.
- No live request, Treasury discovery, credential, capture, upload, or release
  occurred.

## 2026-07-31 - Task: Write failing Treasury discovery tests

- Added deterministic contracts that resolve the `the-treasury` slug through
  `organization_show` and retain the returned stable organisation ID.
- Required sorted, organisation-filtered pagination driven by live result
  counts rather than the dated 54-dataset baseline.
- Defined count-drift evidence, exact raw organisation/page observations,
  deterministic newline-terminated scope JSON, and stable page hashes.
- Required duplicate IDs, missing IDs, and premature page exhaustion to fail
  closed without leaking affected identifiers into exception text.
- Red command: `uv run --locked pytest tests/ckan/test_discovery.py -q`.
- Expected red result: collection stops at `ModuleNotFoundError` for the absent
  `archive_govt_nz.ckan.discovery` implementation.
- Ruff passes for the red contract file. All fixtures are in memory and no live
  catalogue operation occurred.

## 2026-07-31 - Task: Implement complete Treasury discovery

- Added a narrow Action-client protocol, stable organisation and dataset
  records, exact raw page observations, reconciled scope records, and bounded
  discovery errors.
- Resolves `the-treasury`, verifies the returned canonical name and stable ID,
  and uses the verified name in sorted `package_search` pagination.
- Drives progress from every live reported count. Rising counts extend the run;
  falling counts below observed results, premature empty pages, duplicate IDs,
  missing IDs, and out-of-order results fail closed.
- Preserves exact organisation and page bytes, SHA-256 values, UTC observation
  times, page starts, page dataset IDs, and all reported counts.
- Generates paired deterministic UTF-8 JSON and Markdown scope artefacts with a
  dated observation, page receipts, and an explicit metadata-only limitation.
- Focused result: 20 discovery tests and 100% of 138 statements and 24 branches.
- Full result: 78 tests and 100% of 430 statements and 94 branches; Ruff,
  strict Pyright, and source secret scan passed.
- These results establish deterministic discovery machinery only. No current
  live Treasury count or completeness claim is made.

## 2026-07-31 - Task: Add bounded live read-only contract checks

- Added an explicit non-interactive live observation tool, separate from the
  deterministic default suite, with 20-second attempts, three-attempt maximum,
  source-identifying user agent, disabled redirects, 8 MiB metadata-response
  bound, page-size control, and compact JSON status output.
- Extended capability observations to retain exact raw bytes, attempts, and
  allowlisted response headers.
- Reduced organisation response volume with `include_datasets=false`; package
  search remains the single authoritative paginated scope.
- Added an atomic evidence writer for exact raw capability, organisation, and
  page responses plus paired JSON and Markdown reports. Its deterministic
  contract passes without network access.
- First live run at page size 100 reconciled 54 unique datasets in one page.
- Independent deployed-pagination run at page size 25 reconciled 25, 25, and 4
  unique datasets. All three live counts were 54.
- Observed CKAN 2.10.9 and Treasury stable organisation ID
  `4d08a178-e03b-4e97-b79d-83d9a7a35744`.
- Exact raw live responses remain ignored under
  `build/live/treasury-20260731T152100+1000-p25`. The paired committed receipt
  records five source hashes and byte counts; the canonical scope report hash
  is `bb72d7fbad84b04aca6f39b39c76cf8e1d835887d86ac88a51b663a475f8414c`.
- The full gate initially stopped on aggregated dual-licence classifiers for
  `text-unidecode` 1.3. Installed metadata declares Artistic License; the gate
  now records that package-specific alternative and still rejects the same
  licence string for every unreviewed package.
- Focused licence, secret, and SBOM gates pass with 79 components. Resource
  downloads and external publication remain unstarted.

## 2026-07-31 - Phase 2 verification and checkpoint

- Re-ran the complete deterministic suite after the live evidence task and
  licence-control correction.
- Full command: `uv run --locked python tools/check.py`.
- All ten stages passed in 103.3 seconds: lock, format, lint, strict types, 80
  tests, schemas, OSV audit, licences, secrets, and validated CycloneDX SBOM.
- Measured production coverage is 100% across 476 statements and 100 branches.
- Reconciled the live page-size-25 scope: 54 unique sorted dataset IDs; three
  reported counts of 54; starts 0, 25, and 50; no duplicate, missing, or
  out-of-order ID.
- Reviewed receipts: exact raw bytes remain local and ignored; committed
  evidence contains bounded hashes, byte counts, times, safe identifiers, and
  explicit limitations.
- Verified local and `github/main` both referenced
  `d04aeccf315ed5cf3f0f715e368bf42f74ab80a1` before the checkpoint commit.
- Phase 2 is complete for capability and metadata scope discovery only.
  Resource policy, capture, hosted scheduling, and publication remain later
  phases and are not implied.

## 2026-07-31 - Task: Define versioned archive schemas

- Defined the Phase 3 schema catalogue for capability, scope, dataset,
  resource, attempt, content-addressed object, archive version,
  transformation, validation, and publication records.
- Added a Mermaid relationship diagram and common identifier, UTC time, digest,
  evidence, state, redaction, and role invariants.
- Kept raw source observations, original resource objects, WARC receipts,
  manifests, and derivatives as explicit distinct roles.
- Defined publication state constraints so upload, remote verification,
  release, and DOI are separate evidence states.
- Defined immutable schema versions, fail-closed readers, explicit
  non-destructive migrations, canonical JSON bytes, and reconstruction without
  SQLite or Parquet.
- The contract is in `schema-design.md`. No schema implementation or stored
  resource record is claimed by this documentation task.

## 2026-07-31 - Task: Write failing schema and invariant tests

- Added representative records for all ten v1 schema kinds and required an
  executable Draft 2020-12 schema for each.
- Applied common missing-ID, undeclared-field, and non-UTC-time rejection
  contracts across every record kind.
- Added object-role separation, early DOI rejection, complete remote
  verification, stable canonical bytes, trailing newline, and non-finite-number
  rejection contracts.
- Red command:
  `uv run --locked pytest tests/records/test_archive_records.py -q`.
- Expected red result: collection stops at `ModuleNotFoundError` for the absent
  `archive_govt_nz.records` implementation.
- Ruff passes for the red contract file. No archive record or resource payload
  was created by the red phase.

## 2026-07-31 - Task: Implement typed domain models and schemas

- Added typed common, capability, scope, dataset, resource, attempt, object,
  version, transformation, validation, and publication record definitions.
- Added a strict runtime schema catalogue and bounded validation errors that do
  not retain record payload detail.
- Generated ten immutable Draft 2020-12 schema files under
  `schemas/archive/v1/` and made the repository schema gate compare every file
  with the typed catalogue.
- Enforced closed properties, non-empty IDs, UTC `Z` times, lower-case SHA-256
  and BLAKE3, URLs, byte bounds, unique identifier arrays, record-specific
  states, explicit object roles, and publication evidence transitions.
- Canonical serialization validates first, rejects NaN/infinity and unsupported
  objects, sorts keys, preserves Unicode, uses compact separators, and appends
  exactly one newline.
- Moved JSON Schema validation into runtime dependencies because archive record
  validation is a library behavior, while retaining its assurance-gate test.
- Focused result: 31 schema/invariant tests; record logic 100% across 189
  statements and 10 branches.
- Full result: 121 tests and 100% across 665 statements and 110 branches; 12
  schemas and two representative documents validated; Ruff, strict Pyright,
  and secret scan passed.

## 2026-07-31 - Task: Define the fail-closed resource policy

- Defined `resource-policy/v1` decision order, network and storage bounds,
  redirect revalidation, decompression and archive-member controls, independent
  type evidence, source-filename handling, rights states, retry classes,
  quarantine behavior, tombstones, and exception requirements.
- Defaults are explicit: HTTPS, three redirects, bounded 10-second connect and
  60-second read timeouts, 15-minute total transfer, 512 MiB compressed and
  1 GiB decompressed bytes, 10,000 archive members, 100:1 expansion ratio,
  three retries, four concurrent resources, and 2 GiB temporary storage.
- The policy prohibits silent omission, credential or cookie retention,
  publication of restricted/quarantined bytes, history deletion, and DOI
  creation through an override.
- The policy contract is in `resource-policy.md`. Evaluation and property
  tests are the next red/green task; no resource payload was downloaded.

## 2026-07-31 - Task: Write failing resource-policy property tests

- Added deterministic contracts for unsafe schemes, embedded credentials,
  redirect downgrade and loops, rights restriction, size limits, rate limiting,
  source absence, independent type conflict, archive member and expansion
  bounds, filename sanitization, explicit dispositions, canonical decisions,
  and bounded configuration overrides.
- Red command:
  `uv run --locked pytest tests/policy/test_resource_policy.py -q`.
- Expected red result: collection stops at `ModuleNotFoundError` for the absent
  `archive_govt_nz.resource_policy` implementation.
- Ruff passes for the red contract file. No resource payload was accessed.

## 2026-07-31 - Task: Implement resource-policy evaluation

- Added a pure typed evaluator with `resource-policy/v1`, seven closed
  dispositions, bounded configuration, and canonical decision receipts.
- Enforced HTTPS, credential-free URLs, same-host redirect revalidation,
  redirect loops and limits, rights states, declared byte limits, retryable
  rate limits, terminal not-found, independent media-type conflict quarantine,
  archive member and expansion-ratio quarantine, and metadata-only filename
  sanitization.
- No network, filesystem payload, decompression, or publication action occurs
  in the evaluator; those boundaries remain owned by later capture/storage
  stages.
- Green focused result: 16 policy tests; evaluator 100% across 127 statements
  and 44 branches.
- Full result: 137 tests and 100% across 792 statements and 154 branches; Ruff,
  strict Pyright, and secret scan passed.
- Mutation testing remains an explicit hardening subtask before the Phase 3
  checkpoint and is not claimed complete by this commit.

## 2026-07-31 - Resource-policy mutation hardening

- Native `mutmut` was assessed and rejected for this Windows environment because
  it requires WSL. `mutatest` was assessed and rejected after a reproducible
  Python 3.14 set-sampling incompatibility.
- Added a repository-owned isolated mutation runner with eight targeted
  critical-policy mutants. Each mutant runs the policy tests against a copied
  package tree; the source worktree is never modified.
- Mutation command: `uv run --locked python tools/mutation_resource_policy.py`.
- Result: 8/8 mutants killed; receipt is generated under ignored `build/`.
- Integrated the mutation runner as the repository assurance gate stage after
  schema validation.

## 2026-07-31 - Immutable object-store vertical slice

- Red phase: six tests specified hashing, atomic promotion, deduplication,
  corruption detection, interruption cleanup, and object-ID traversal defence.
- Added `ContentAddressedStore` with SHA-256 addressing, BLAKE3 receipts,
  durable temporary writes, atomic promotion, fail-closed verification, and
  immutable overwrite protection. Payload roots remain outside Git tracking.
- Green focused result: 6 object-store tests passed. Full assurance result:
  143 tests, strict Pyright, Ruff, schema validation, 8/8 policy mutants
  killed, dependency/licence/secret audits, and an 80-component SBOM passed.
- Object-store coverage is 92% locally; repository total is 99.24%. The
  remaining uncovered branches are defensive filesystem/type failures and are
  retained as explicit future mutation-hardening work.

## 2026-07-31 - Streaming capture foundation

- Added bounded httpx capture with status classification, byte limits, and immutable promotion.
- Focused result: 2 tests passed; redirect, validator, decompression, type, and quarantine controls remain open.

## 2026-07-31 - Capture safety hardening

- Added bounded redirect traversal, relative-location resolution, ETag/Last-Modified validation, timeout propagation, and redirect-loop failure classification.
- Full gate: 147 tests, 97.72% coverage, strict Pyright/Ruff, schemas, mutation, audit, licence, secret, and SBOM checks passed.

## 2026-07-31 - SQLite ledger foundation

- Added WAL-enabled SQLite migrations with foreign keys, observation uniqueness, checkpoints, and deterministic export.
- Focused result: 3 ledger tests passed. Attempt/object/version/publication write APIs remain the next ledger increment.

## 2026-07-31 - Ledger relationship writes

- Added transactional attempt, object, version, and publication inserts with
  foreign-key linkage and stable duplicate/orphan error classes.
- Focused ledger result: 4 tests passed, including relationship enforcement.

## 2026-07-31 - Change-driven versioning foundation

- Added canonical SHA-256 fingerprints over metadata/resource evidence and
  explicit initial, unchanged, changed, and tombstone decisions.
- Focused result: 2 versioning tests passed. Resource disappearance and policy
  transition mutation coverage remain open.

## 2026-07-31 - Phase 4 verification checkpoint

- Added isolated version-transition mutation testing: 3/3 targeted mutants
  killed and integrated it as an assurance stage.
- Full gate passed: 153 tests, 97.60% total coverage, schemas, both mutation
  suites, audits, secrets, and SBOM. Defensive capture/object-store branches
  remain below the critical 100% target and are recorded explicitly.

## 2026-07-31 - Provenance manifest foundation

- Added deterministic, SHA-256-addressed manifest receipts with explicit
  observation/object/version/derivative closure checks.
- Focused result: 2 provenance tests passed; transformation, validation, and
  publication receipt fields remain open for the next manifest increment.

## 2026-07-31 - Core derivative foundation

- Added deterministic normalized JSONL and Zstandard-compressed Parquet
  derivatives with DuckDB row-count reconciliation.
- Unknown CKAN fields are explicitly reported as information loss rather than
  silently presented as preserved data. Focused derivative test passed.

## 2026-07-31 - WARC transaction receipt foundation

- Added bounded WARC 1.1 response receipts with payload digests, safe origin
  URLs, and an allowlist of non-sensitive response headers.
- Focused result: 2 WARC tests passed, including signed-query and
  Authorization-header exclusion. Manifest relationship verification remains
  open.

## 2026-07-31 - Preservation packaging evaluation

- Added paired Markdown and JSON evidence evaluating OCFL, RO-Crate, and BagIt
  against the Treasury vertical-slice constraints.
- Decision recorded as `evaluate-before-adopt`; none is silently promoted to a
  release requirement. The evaluation receipt is generated and tested.

## 2026-07-31 - WARC manifest closure

- Extended provenance manifests with explicit WARC-record-to-object
  relationships and deterministic ordering.
- Added a failing/green closure test for detached WARC evidence; 3 provenance
  tests now pass.

## 2026-07-31 - Paired evidence ledger

- Added generated Markdown and JSON evidence ledgers with separate stage states
  for discovery, eligibility, capture, validation, transformation, upload,
  remote verification, release, unavailability, and restriction.
- Publication states remain explicitly `not-authorized`/`not-released` until
  credentials and remote receipts exist. Generation test passed.

## 2026-07-31 - Phase 6 pre-capture reconciliation

- Fresh read-only CKAN observation returned 54 Treasury datasets at all three
  pages. Dataset IDs match the baseline exactly; no additions or removals.
- Scope hash drifted, so metadata change detection remains required. Paired
  reconciliation evidence is in `evidence/phase-6-pre-capture-reconciliation.*`.
- Payload capture and publication remain gated and unstarted.

## 2026-07-31 - Treasury capture planning inventory

- Enumerated 91 resources across the current 54-dataset Treasury scope and
  generated per-resource fail-closed policy decisions.
- This is metadata-only planning; no payload bytes were downloaded or committed.

## 2026-07-31 - Batch capture budget controls

- Added fail-closed batch admission decisions for total bytes, resource count,
  and concurrency. Budget overruns are explicit and cannot start partial
  unbounded work.
- Three focused budget tests pass.

## 2026-07-31 - Explicit bounded capture runner

- Added a resumable batch-runner seam consuming the 91-resource plan. It
  defaults to no transfer, requires `--enable`, applies byte/count/concurrency
  budgets, and writes per-resource outcome JSON outside Git-tracked payloads.
- Offline no-transfer contract test passes.

## 2026-07-31 - Capture gate sizing evidence

- The 91-resource metadata-only plan currently resolves to 74 terminal and 17
  restricted outcomes, with zero eligible bytes. This is intentionally
  fail-closed because transport/type preflight has not run; no payload transfer
  was started.
- A bounded live preflight is required before any resource can become eligible.

## 2026-07-31 - Authorized Treasury resource preflight

- Ran the authorized HTTPS `HEAD` preflight over all 91 resources with no body
  transfer. Results: 17 HTTPS observations, 12 status-200 candidates, 5 status
  403 unavailable, and 74 non-HTTPS policy-restricted URLs.
- Paired summary evidence is in `evidence/phase-6-preflight-summary.*`.

## 2026-07-31 - Bounded Treasury payload capture

- Captured all 12 HTTP-200 HTTPS resources selected by the authorized preflight.
- Enforced 512 MiB per-resource, 10 GiB batch, and concurrency-4 limits.
- Stored 12 content-addressed objects under the ignored local object store.
- No publication was attempted; 403 and non-HTTPS resources remain explicitly unavailable/restricted.
- Paired evidence is in `evidence/phase-6-capture-summary.*` and the run receipt is `build/live/capture-20260731.json`.

## 2026-07-31 - Hugging Face Viewer diagnosis and bounded blocker

- Tested the dedicated derivative repository with derivative-only layouts, canonical split naming, minimal cards, and both Zstandard and Snappy Parquet.
- Direct download and local PyArrow validation passed for 54 rows and six typed columns.
- All Dataset Viewer endpoints continued to return HTTP 500.
- The failure is recorded in `evidence/phase-8-hf-derivative-viewer-diagnosis.json`; Viewer readiness and Zenodo DOI gates remain unclaimed.
- Nested GitHub follow-up issue #21 was created after the API rate-limit window reset.

## 2026-07-31 - Treasury rights classification

- Read-only reconciliation found `CC-BY-4.0` at dataset level for all 54 Treasury datasets.
- This supports attribution-based publication candidates but does not waive resource-specific rights, privacy, security, withdrawal, or exception review.
- Receipt: `evidence/phase-6-rights-classification.json`.

## 2026-07-31 - CSV Viewer fallback diagnosis

- Created fresh `edithatogo/archive-govt-nz-treasury-csv` with only a minimal card and 54-row CSV.
- Viewer `is-valid`, `splits`, and `rows` endpoints all returned HTTP 500.
- This rules out Parquet compression, mixed repository layout, evidence JSON, and raw-object placement as the sole cause.
- Receipt: `evidence/phase-8-hf-csv-viewer-diagnosis.json`.

## 2026-07-31 - Preservation-only Zenodo publication

- Published Zenodo record `21718048` / DOI `10.5281/zenodo.21718048`.
- Uploaded the checksum-pinned preservation candidate tar; package SHA-256 is recorded in `evidence/phase-9-zenodo-publication.json`.
- The record explicitly documents Hugging Face Viewer HTTP 500 and is not claimed as the analytical Viewer release.

## 2026-08-01 - Viewer recovery and corrective preservation release

- Verified Viewer/search/filter/statistics recovery for the source, Parquet, and CSV repositories; both derivatives expose 54 rows and six columns.
- Closed GitHub issue #21. The earlier HTTP 500 was a transient service-side conversion/cache failure.
- Audit found Zenodo v1 omitted raw CKAN responses, 12 captured objects, and derivatives because the release test asserted a fixed evidence-file count instead of preservation roles.
- Hardened release preparation to include raw responses, every content-addressed captured object, derivatives, rights evidence, and Viewer receipts.
- Removed the timestamped raw-directory default and now require explicit raw, object, derivative, and capture-receipt inputs; package creation fails unless object hashes exactly close against the capture receipt.
- Published corrective version DOI `10.5281/zenodo.21728726` under concept DOI `10.5281/zenodo.21718047`; v1 remains auditable and explicitly superseded.
- Hardened the DuckDB fallback to preload an in-memory table, disable external access, and accept exactly one SELECT statement.

## 2026-07-31 - Recovery reconciliation foundation

- Added restart-safe ledger/object-store reconciliation reporting verified,
  missing, corrupt, and orphan payload states separately.
- Local recovery fixture passed; interruption-at-every-boundary and repeated
  unchanged-run proof remain open.

## 2026-07-31 - CI/CD workflow foundation

- Added immutable-pinned, least-privilege CI, scheduled read-only discovery,
  and manually enabled capture workflows with concurrency controls.
- Capture workflow fails closed until the bounded capture command is explicitly
  released; no scheduled workflow publishes payloads.
- Workflow policy test initially caught missing CI concurrency and now passes
  after the correction.

## 2026-07-31 - Release attestation foundation

- Added deterministic checksums over the paired evidence ledger, preservation
  evaluation, and SBOM.
- Attestation state is explicitly `prepared-not-published`, unsigned, and
  unauthorized until release credentials and approval gates are satisfied.

## 2026-07-31 - Publication contract foundation

- Added a shared credential-safe contract for Hugging Face rolling archives and
  Zenodo immutable releases.
- Default preparation is non-mutating; enabled publication without the target
  token fails closed, and remote side effects are not implemented implicitly.
- Two publication safety tests pass.

## 2026-07-31 - Deterministic Zenodo package foundation

- Added reproducible, gzip-free tar packaging from an explicit file list with
  normalized paths, timestamps, modes, and a package SHA-256.
- Package state is `prepared-not-published`; no DOI or remote side effect is
  created. Focused reproducibility test passed.

## 2026-07-31 - Treasury release candidate preview

- Prepared a checksum-pinned local candidate from seven verified evidence/SBOM
  artefacts. The manifest explicitly records no DOI, no remote upload, and
  incomplete payload capture.
- Candidate preparation test passes; exact Hugging Face revision reconciliation
  remains open because no remote publication has occurred.

## 2026-07-31 - Expanded assurance methods

- Added deterministic simulation primitives with permutation and addition
  metamorphic tests.
- Added explicit publication contract tests covering both Hugging Face and
  Zenodo state invariants.
- Existing Hypothesis property tests, branch coverage, and mutation suites
  remain active; CI now exports Cobertura XML and uploads it to Codecov.

## 2026-07-31 - Dependency lane foundation

- Added a read-only scheduled dependency/pre-release compatibility lane.
- It verifies the production lock, runs tests, and records pre-release mode as
  observational; it cannot rewrite `uv.lock` or publish artifacts.

## 2026-07-31 - Current assurance reconciliation

- The aggregate `tools/check.py` invocation exceeded the shell's 120-second
  timeout after the dependency/tooling expansion; it is not claimed as a
  single-command pass.
- Decomposed authoritative stages passed: 167 tests, strict lint/types,
  schemas, 8/8 resource-policy mutants, 3/3 version mutants, dependency audit,
  licence inventory, secret scan, and an 82-component SBOM.

## 2026-07-31 - Derivative dependency security correction

- The first full gate identified the published Apache Arrow advisory in
  `pyarrow 22.0.0`; release progression stopped at the audit stage.
- Upgraded to fixed `pyarrow 23.0.1`; dependency audit now passes with no known
  vulnerabilities. This correction is required before derivative publication.
