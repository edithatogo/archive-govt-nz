# Treasury Archive MVP Planning Review

## Review outcome

Status: approved for track initialization

## Checks

- The track is bounded to Treasury and does not absorb later health scope.
- Complete metadata and eligible-resource capture are explicit.
- Every resource requires an explicit outcome.
- Original objects and derivatives are distinct.
- Resource capture is bounded and fail closed.
- Recovery does not depend on operational or query databases.
- Hosted upload, remote verification, and release remain separate states.
- Hugging Face and Zenodo actions retain explicit credential and publication
  gates.
- Coverage and security standards match the project workflow.
- Solo-maintainer governance does not invent a second reviewer.
- The plan requires one parent GitHub issue and nested phase subissues.
- The dated count of 54 is evidence, not a hard-coded acceptance target.

## Open planning limitations

- Exact dependency versions remain implementation-time decisions resolved and
  locked from current stable releases.
- Source resource sizes, media types, availability, and rights have not yet
  been exhaustively profiled.
- No remote repository or publication state is yet verified.
- Preservation-standard conformance remains an evaluation task.

## Task self-review: Establish GitHub and Conductor traceability

- Repository owner, name, visibility, default branch, and remote were read back.
- The local and hosted head matched before recording task evidence.
- Parent and phase issue bodies reference the track and requirement scope.
- Native GitHub subissue relationships were verified, not inferred from links.
- No second-person review, CODEOWNERS, team, or reviewer-count constraint was
  added.
- No credentials or token values were persisted in repository evidence.
- No publication, Hugging Face, Zenodo, or dataset payload action occurred.
- Connector access lag is recorded as a bounded limitation with an authenticated
  CLI fallback.

## Task self-review: Write failing package and CLI bootstrap tests

- Tests describe public behaviour rather than implementation details.
- CLI tests execute a separate Python process and detect prompts or extra output.
- JSON output has an explicit schema version.
- Exit states are unique and leave conventional usage errors available.
- The observed red failure was the intended absent-package condition.
- No network, credential, publication, or payload access occurs in these tests.

## Task self-review: Implement the Python 3.14 project foundation

- The package installs from a locked Python 3.14 environment and builds as both
  an sdist and a platform-independent wheel.
- The public package version derives from distribution metadata, avoiding a
  duplicated version constant.
- CLI help and JSON version output are non-interactive and stable.
- Exit-state values are explicit and tested as a public automation contract.
- Configuration requires explicit caller input; no credentials or uncontrolled
  environment values are loaded.
- Cyclopts is a material stack decision and is now named in the project
  technology guide.
- No network, catalogue capture, payload, credential, or publication boundary
  is crossed.
- Static analysis, coverage enforcement, and the repository-wide gate are
  intentionally owned by the next sequential Phase 1 task and are not claimed
  by this task.

## Task self-review: Establish the repository-wide assurance harness

- One cross-platform Python command runs the locked stages in a deterministic
  order and stops at the first failure.
- The gate has no shell interpolation and receives only repository-owned command
  tuples.
- Strict type checking remains enabled; the jsonschema typing gap has one
  expression-scoped suppression at the third-party boundary.
- Ruff's full ruleset is enabled. Exceptions are scoped to explicit CLI output,
  controlled subprocess calls, test assertions, standalone tool layout, and
  the repository's licence-file copyright model.
- Coverage failed closed before direct tests were added and now reports 100%
  line and branch coverage for measured production modules.
- Hypothesis and JSON Schema are executed, not merely declared dependencies.
- The CLI schema uses Draft 2020-12, forbids additional properties, and pins
  command, status, and schema-version constants.
- No archive payload, network, credential, hosted CI, or publication action
  occurs in this gate.
- Supply-chain, licence, vulnerability, secret, SBOM, and hosted workflow checks
  remain the next sequential task and are not claimed here.

## Task self-review: Establish supply-chain and repository controls

- Vulnerability lookup fails closed and uses a current OSV response; a network
  timeout is not reported as a clean audit.
- Licence policy rejects unresolved and strong-copyleft terms while preserving
  a complete machine-readable local inventory.
- Secret scanning covers source files and excludes only generated, ignored
  environments, caches, receipts, locks, and track evidence containing hashes.
- No candidate secret was baselined or waived.
- The SBOM is reproducibly generated and validated against CycloneDX 1.6, not
  merely checked for file existence.
- Generated receipts remain outside Git and do not contain credentials.
- Policies describe the real solo-maintainer model and retain explicit rights,
  credential, quarantine, publication, and upstream-contribution gates.
- Rust remains absent. Its guide requires equivalence, safety, property,
  mutation, and benchmark evidence before adoption.
- Local scanner success does not claim hosted CodeQL, GitHub secret scanning,
  attestations, CI, or publication.

## Phase 1 checkpoint self-review

- Every Phase 1 implementation task has an observed red phase, a green local
  result, track evidence, a coherent commit, a pushed remote match, and an issue
  comment.
- A separate isolated environment reproduced package installation, CLI startup,
  tests, and coverage from the lock.
- The source distribution and wheel build without untracked payload content.
- Machine-readable Git revisions use a key-scoped secret-scan exclusion; the
  remainder of each checkpoint receipt remains scanned.
- The GitHub hierarchy and remote ref were read back; Conductor does not infer
  them from local metadata.
- Phase 1 establishes local assurance and supply-chain foundations only.
  Hosted CI, CKAN capability, Treasury completeness, capture, recovery, Hugging
  Face upload, and Zenodo release remain explicitly unverified.
- No critical self-review finding remains open for Phase 1.

## Task self-review: Continuous autonomous Conductor execution

- Routine task, phase, checkpoint, review, documentation, and approved-track
  boundaries no longer request confirmation.
- The policy does not broaden authority: credentials, publication, DOI,
  legal/rights/privacy/security exceptions, destructive actions, and material
  unapproved scope remain decisions.
- Decision requests must be actionable and evidence-backed, with the
  recommendation first and independent work continuing where possible.
- Retry budgets require materially changed hypotheses and cannot become an
  infinite loop.
- Repository evidence, not conversational memory, is the resumption authority.
- Experimental upstream code was not copied, installed, or represented as
  stable. Its useful concepts are implemented through tested local contracts.
- Conditional worktrees avoid imposing experimental isolation on the current
  clean sequential Windows/OneDrive checkout.

## Task self-review: Write failing CKAN envelope and capability tests

- Tests separate CKAN's envelope-level `success` value from HTTP status.
- Retryable and terminal statuses are explicit and bounded.
- Malformed documents cannot become successful results.
- Timeout and unknown transport errors do not expose source exception text.
- Redaction tests preserve safe query/identifier evidence and source
  immutability while removing headers, nested keys, and signed URL values.
- The red failure is the intended absent-module condition.

## Task self-review: Implement the CKAN envelope and redaction kernel

- Complete envelopes are required before HTTP or Action classification.
- Unknown transport exceptions fail terminal and do not enter retry loops.
- Diagnostic exceptions retain stable classes and bounded parsed evidence, not
  private source exception text.
- URL redaction operates on parsed query keys and retains non-sensitive
  parameters.
- Redaction copies mappings/lists and cannot mutate captured originals.
- Raw-byte receipts, async transport, timing, user agent, and retry scheduling
  are explicitly not claimed and remain in the next red/green task pair.

## Task self-review: Write failing bounded CKAN HTTP client tests

- Contracts exercise public transport behavior through HTTPX's in-memory async
  transport rather than implementation-private functions.
- Clock, sleep, and jitter are injected so retry evidence is deterministic and
  does not slow the suite.
- Attempt receipts require stable error classes and prohibit private transport
  exception text.
- Raw source bytes remain distinct from the parsed Action response and receive
  a deterministic SHA-256 receipt.
- Response metadata uses an allowlist contract that excludes cookies.
- Oversized responses fail before Action interpretation.
- The production lock uses current stable releases; prerelease compatibility
  remains an isolated later lane and cannot rewrite the production lock.
- The observed red failure is the intended absent-client-module condition.

## Task self-review: Implement the bounded CKAN HTTP client

- All configured resource controls reject zero, negative, absent, or unsupported
  values before a request.
- Disabling redirects prevents an Action call from silently crossing catalogue
  boundaries; later resource capture owns separately bounded redirect policy.
- Identity content encoding makes the retained body meaningful as the received
  entity bytes and avoids transparent decompression ambiguity.
- `Content-Length` is used only as an early rejection signal. Missing or invalid
  values still traverse the incremental byte counter.
- Buffered mock responses and unbuffered transport streams exercise distinct
  limit branches.
- Retries require both a known-safe class and remaining budget. There is no
  unbounded loop, and deterministic tests prove exhaustion.
- Attempt records contain stable classes, status codes, and times but never
  source exception strings, cookies, or unrestricted headers.
- Capability evidence requires both deployed CKAN version and site identity;
  incomplete status output is terminal protocol failure.
- ckanapi remains locked for upstream-compatible utilities, while the raw
  Action transport is intentionally owned here because evidence receipts and
  safety bounds are archive-critical behavior.
- Critical and overall line and branch coverage are 100%, with no exclusion in
  the client module.

## Task self-review: Write failing Treasury discovery tests

- The Treasury slug is a configured discovery starting point, not accepted as
  sufficient identity evidence; `organization_show` must return a stable ID and
  the expected canonical name.
- Package search is explicitly sorted by stable ID so page ordering is
  reproducible within a live observation.
- Rising counts extend discovery and are retained as evidence. The historical
  count of 54 is not an executable invariant.
- Duplicate and missing stable dataset IDs cannot be silently deduplicated or
  omitted.
- An empty page before the latest reported count prevents a completeness claim.
- Raw page bytes and their transport hashes remain available alongside a
  smaller deterministic scope manifest.
- Errors expose bounded classes rather than affected dataset identifiers or
  raw payload detail.
- The observed red failure is the intended absent-discovery-module condition.

## Task self-review: Implement complete Treasury discovery

- The Action protocol is narrow enough for deterministic fixtures and is
  structurally compatible with the bounded production client.
- The canonical organisation name is verified before being interpolated into
  the CKAN filter; source results cannot redirect the scope to another agency.
- Pagination advances by observed result length and verifies the requested
  ascending stable-ID order.
- Count increases are evidence, not errors. Counts below already observed
  unique datasets are inconsistent and fail closed.
- Duplicate IDs fail before ordering checks so the diagnostic class remains
  precise; distinct descending IDs receive a separate ordering class.
- Search counts reject booleans despite Python's integer subtype relationship.
- Exact raw observations remain separate from compact reports; neither report
  reserializes itself as claimed source bytes.
- The paired reports use one observation time and stable hashes and explicitly
  state that metadata discovery is not resource capture or publication.
- All discovery branches are covered without exclusions.
- Current live scope remains unclaimed until the separately bounded live task
  observes and persists catalogue evidence.

## Task self-review: Add bounded live read-only contract checks

- Live access is an explicit tool invocation and cannot make the deterministic
  test suite dependent on catalogue availability or count stability.
- The live tool inherits all client time, attempt, byte, redirect, user-agent,
  raw-byte, and redaction controls.
- Organisation lookup disables embedded datasets, avoiding redundant source
  volume before the sorted package search.
- The second live observation intentionally uses a smaller page size to verify
  deployed pagination and completeness independently of the one-page result.
- The live count is reported as time-bounded evidence, not a permanent
  executable expectation. A future change from 54 is not itself failure.
- Raw observations are written only after complete scope reconciliation and are
  atomically promoted within an ignored output directory.
- The committed receipt includes hashes and sizes but not the source payloads,
  cookies, unrestricted headers, or transport exception strings.
- Checksum-specific secret-scan exclusion cannot baseline an arbitrary
  credential line; credential-like values outside revision and SHA-256 receipt
  keys still fail.
- The `text-unidecode` decision selects its declared Artistic alternative by
  exact package name. A synthetic unreviewed package with identical aggregated
  classifiers remains denied.
- Metadata observation is not resource capture, rights eligibility, hosted
  scheduling, upload, remote verification, or publication.

## Phase 2 checkpoint self-review

- Every Phase 2 behavior has deterministic contracts, a red implementation
  boundary, green focused evidence, and 100% critical line and branch coverage.
- Live observations were run only after deterministic bounds and receipts were
  established.
- The page-size-25 live run proves deployed pagination rather than relying on a
  single large response.
- The live count matches the dated baseline of 54, but no code treats 54 as a
  success condition.
- Raw-source preservation is exact and hash-verified; derived JSON and Markdown
  reports never masquerade as raw CKAN responses.
- Response receipts allowlist headers and exclude cookies, signed values,
  unrestricted exception text, and credentials.
- Supply-chain failure was not suppressed. The dual-licence metadata was
  investigated, documented, selected package-specifically, tested against a
  synthetic unreviewed package, and re-run through the complete gate.
- Hosted CI and scheduled checks are still unimplemented; local live evidence
  does not claim a hosted run.
- No dataset resource file, quarantine decision, rights decision, credential,
  upload, deposition, DOI, or publication boundary was crossed.
- No critical self-review finding remains open for Phase 2.

## Task self-review: Define versioned archive schemas

- The catalogue covers every record kind named in M-10 without combining
  operational attempts, immutable objects, versions, or publications.
- Stable record relationships do not depend on filesystem paths, ledger row
  IDs, DuckDB, or Parquet.
- Source metadata, source resources, receipts, manifests, and derivatives have
  separate roles, preventing normalized output from replacing an original.
- State enums separate observation, eligibility, capture, validation, upload,
  remote verification, and release.
- Publication constraints prohibit early DOI or remote-verification claims.
- Published schema files cannot be silently loosened; any document change
  creates a new version and retains the original record bytes.
- Migrations produce new records and transformation receipts and cannot erase
  restriction, quarantine, rights, or publication history.
- The design sets exact testable canonicalization rules and explicitly rejects
  non-finite numbers.
- This task is a contract only. The next task must demonstrate the intended red
  boundary before models or JSON Schemas are implemented.

## Task self-review: Write failing schema and invariant tests

- Every planned record kind has a representative record; no kind can be omitted
  while still passing the parameterized catalogue contract.
- Common provenance failures are tested uniformly across all ten schemas.
- The object-role contract prevents an invented hybrid role from obscuring
  whether bytes are original or derived.
- Publication tests distinguish prepared, uploaded, remotely verified, and DOI
  states without claiming that any remote action occurred.
- Canonicalization is compared across reversed insertion order and requires a
  trailing newline.
- Non-standard JSON floating-point values fail rather than producing
  platform-dependent hashes.
- The red failure is the intended absent-record-module condition.

## Task self-review: Implement typed domain models and schemas

- TypedDict definitions give Python callers kind-specific required and optional
  fields; JSON Schema remains the cross-language persisted-record authority.
- Generated files are checked back against the in-code catalogue, preventing
  hand-edited schema drift.
- Defensive schema copies prevent callers from mutating later validations.
- Readers infer kind only from the exact
  `archive-govt-nz.<kind>/v1` identifier and reject missing, foreign, newer, and
  unknown versions.
- Format checking is active, so URL and RFC 3339 fields are executable
  constraints rather than annotations.
- Publication conditionals require complete remote identity, revision, and
  time evidence, and restrict a DOI to a released Zenodo record.
- The schema layer does not grant rights, release quarantine, create an object,
  or perform a publication.
- All record validation and canonicalization branches are covered without
  exclusions.

## Task self-review: Define the fail-closed resource policy

- The policy applies before and during transfer, so a safe preflight cannot
  remove streaming bounds.
- Redirect destinations are independently rechecked for scheme and host policy;
  downgrade and loop behavior cannot become implicit acceptance.
- Filename metadata is separated from object paths, preventing traversal and
  reserved-name issues from becoming storage writes.
- Independent type evidence, archive member limits, expansion ratio, links, and
  encrypted members address common archive and content-confusion hazards.
- Rights ambiguity, privacy, security, quarantine, and withdrawal are explicit
  states, while tombstones preserve prior history.
- Exceptions require bounded authority and expiry and cannot cross destructive,
  credential, quarantine, or DOI gates.
- The documented defaults are implementation inputs, not yet runtime evidence;
  the next task must test every critical branch and generated disposition.

## Task self-review: Write failing resource-policy property tests

- Tests cover both preflight and safety evidence and do not call the network or
  inspect unbounded payloads.
- Unsafe URL evidence includes cleartext, local schemes, and embedded
  credentials; redirects are tested independently for downgrade and loops.
- Rights ambiguity, rate limiting, not-found, size, type, and archive safety
  outcomes are distinct dispositions rather than a generic skipped state.
- Filename tests verify sanitization is metadata-only and cannot imply a storage
  path.
- Canonical decision bytes and explicit outcome closure establish the manifest
  contract needed for later ledger and publication stages.
- The observed red failure is the intended absent policy-module condition.

## Task self-review: Implement resource-policy evaluation

- The evaluator is pure and cannot silently download, write, decompress, or
  publish content; it consumes only bounded preflight evidence.
- URL credentials, cleartext/local schemes, redirect downgrades, cross-host
  redirects, loops, and excessive hops receive terminal bounded reasons.
- Rights ambiguity is restricted, transient rate limiting is retryable, and
  type/archive safety conflicts are quarantined rather than eligible.
- Sanitized filenames are returned only as display metadata and never used as
  object paths.
- Policy overrides validate their own bounds and preserve the policy version.
- Every critical branch is covered and eight targeted mutations were killed by
  the integrated assurance stage in isolated temporary package copies.
- Native third-party mutation tools were not silently treated as passing: their
  Windows/WSL and Python 3.14 limitations were recorded, and the bounded
  repository-owned runner provides the executable evidence available here.

## 2026-08-01 corrective publication review

- Critical finding resolved: the first Zenodo package contained evidence but omitted captured source objects, raw CKAN responses, and derivatives. Role-based release assertions and the corrected package now include all three layers.
- Critical finding resolved: the DuckDB fallback used keyword substring filtering, which allowed PRAGMA and did not reliably contain external reads. It now preloads only the approved Parquet file, disables external access, and accepts exactly one SELECT.
- External finding resolved: all Hugging Face Viewer endpoints recovered and representative 54-row readback passed. The failure was transient service state, not invalid archive data.
- Remaining finding: Zenodo network operations were executed through a bounded credential-safe script path but still need a repository-owned, mocked integration adapter before scheduled publication can be claimed automated.
- Hosted CI finding resolved: tests no longer depend on ignored local build outputs; Linux run `30669731935` passed the full locked gate and Codecov OIDC upload.
- Residual CI warning: pinned third-party actions currently target Node.js 20 and are force-run on Node.js 24 by GitHub. This is not a failed control, but action-version upgrades should be tracked when upstream releases are reviewed and pinned.
