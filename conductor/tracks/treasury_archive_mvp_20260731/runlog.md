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
