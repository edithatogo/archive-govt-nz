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
