# Project Workflow

## Guiding principles

1. **Conductor is the planning authority.** All implementation work belongs to
   a registered track and a sequential task in its `plan.md`.
2. **Requirements precede implementation.** Every track contains a
   `requirements.md` using MoSCoW priorities. A Must requirement cannot be
   silently deferred or weakened.
3. **Design is explicit.** Design-bearing tracks contain `design.md` with
   Mermaid diagrams for relevant components, data flows, trust boundaries,
   states, and failure paths.
4. **The stack is deliberate.** Amend `tech-stack.md` and record the rationale
   before adopting a material new technology.
5. **Evidence precedes claims.** Distinguish discovery, capture, validation,
   transformation, upload, remote verification, and release.
6. **Test-driven development is the default.** Establish a failing test or
   executable check before changing behaviour.
7. **Originals are immutable.** Transformations create separately identified
   derivatives and complete receipts.
8. **Automation is strict; governance is honest.** This is a solo-maintainer
   repository. Strong automated checks replace fictional second-person review
   requirements.
9. **External gates remain explicit.** Credentials, publication, DOI creation,
   rights decisions, security exceptions, destructive actions, and other
   external changes require specific authority.
10. **Commands are non-interactive and CI-aware.** Prefer deterministic,
    scriptable commands with bounded execution and structured outputs.

## Track contract

Each implementation track contains, at minimum:

- `index.md`: track entrypoint and artefact map;
- `requirements.md`: MoSCoW requirements and acceptance criteria;
- `design.md`: required when the track changes architecture, data flow,
  schemas, trust boundaries, storage, or publication;
- `plan.md`: sequential phases and tasks;
- `metadata.json`: stable track identity and status;
- `runlog.md`: dated commands, outcomes, and bounded deviations;
- `evidence.md`: validation and external-state receipts;
- `review.md`: self-review findings and resolution state.

The track maps to a parent GitHub issue. Plan phases or substantial tasks map to
nested subissues where GitHub supports them. Issues, pull requests, and
Conductor artefacts link to one another using stable identifiers.

Use `Fixes #N` only when the change genuinely completes the issue.

## Task lifecycle

### 1. Select and bound the task

1. Choose the next unblocked task in `plan.md`.
2. Confirm its requirement and acceptance-criterion references.
3. Inspect the working tree and preserve unrelated user changes.
4. Mark the task `[~]` before implementation.
5. Record any external, credential, publication, rights, or human gate.

Do not broaden a task merely because adjacent work is desirable. Create or
amend a planned task when scope changes materially.

### 2. Establish the red phase

Before implementation:

1. Add or update the smallest appropriate executable test.
2. Include success, failure, and boundary behaviour.
3. For archive state, include partial, unchanged, retryable, withdrawn,
   restricted, and corrupt cases where relevant.
4. Run the focused test and confirm it fails for the expected reason.
5. Record the command and bounded outcome in `runlog.md`.

Tests that cannot begin red because they characterize existing behaviour must
say so explicitly and preserve the observed contract.

### 3. Implement the green phase

1. Implement only enough to satisfy the task requirements.
2. Preserve stable public and machine-readable contracts.
3. Run the focused test until it passes.
4. Run relevant static, schema, security, and integration checks.
5. Do not suppress a failing check without a documented, time-bounded
   exception.

### 4. Refactor and harden

With focused tests passing:

- remove duplication and accidental complexity;
- make failure states explicit;
- validate typing and schema boundaries;
- verify deterministic and idempotent behaviour;
- check secret and personal-information redaction;
- test interruption and resumption when the task changes persistent state;
- rerun all affected checks.

### 5. Verify coverage

Coverage is risk-tiered:

- **Critical logic:** 100% line and branch coverage.
- **Overall production code:** at least 95% line and branch coverage.

Critical logic includes:

- hashing and content identity;
- manifest and provenance construction;
- change detection and version selection;
- retention, withdrawal, tombstone, and restriction policy;
- credential and sensitive-value handling;
- publication state and remote verification;
- recovery and integrity decisions.

Coverage exclusions must be narrow, justified in source, and recorded in the
track. Coverage alone is not adequate evidence: property, mutation, contract,
recovery, and negative-path tests are required where risk warrants them.

### 6. Record evidence

Before completion, update track-local evidence with:

- task and requirement identifiers;
- files changed;
- exact commands executed;
- test, coverage, lint, type, schema, and security outcomes;
- observed source or remote state;
- known limitations and deferred Should/Could requirements;
- whether any evidence is local-only, uploaded, or remotely verified;
- issue and pull-request cross-references when available.

Do not store task summaries solely in commit messages or Git notes.

### 7. Self-review

Review the task diff for:

- requirement satisfaction;
- correctness and failure semantics;
- archive and provenance integrity;
- security and privacy;
- supply-chain risk;
- performance and resource bounds;
- platform compatibility;
- documentation and schema drift;
- unsupported completeness or publication claims.

Record actionable findings and their resolution in `review.md`.

No second-person approval, CODEOWNERS approval, team assignment, or mandatory
reviewer count is required. Human review may still be requested voluntarily for
specialist legal, rights, security, or research questions.

### 8. Complete and commit

When all relevant gates pass:

1. Mark the task `[x]`.
2. Ensure `requirements.md`, `design.md`, `plan.md`, `runlog.md`, `evidence.md`,
   `review.md`, and `metadata.json` agree.
3. Stage only the coherent task changes.
4. Inspect the staged diff.
5. Create one conventional commit for the completed task.
6. Record the commit and GitHub links in the next track bookkeeping update or
   remote issue summary without rewriting history solely to embed the current
   commit's own identifier.

Commit only after the task is green. Do not combine unrelated completed tasks
in one commit.

## Correction workflow

### In-flight refinement

Resolve small gaps inside the active `[~]` task and rerun its gates.

### Review correction

Add explicit correction tasks to `plan.md` when self-review, CI, or external
evidence identifies a material gap after task completion.

### Logical reversion

Use the Conductor revert workflow when an implementation is fundamentally
wrong. Prefer a traceable revert commit over destructive history rewriting.

### Hosted-state drift

Local success does not repair or prove hosted state. Record upload,
verification, release, and publication drift separately and create a bounded
reconciliation task.

## Phase completion

When the last task in a phase completes:

1. Determine the phase diff from the previous checkpoint.
2. Confirm every changed production module has appropriate tests.
3. Run the full phase validation command.
4. Run recovery or reconstruction checks when archive state changed.
5. Generate paired human-readable and machine-readable evidence.
6. Present bounded manual verification steps only when human observation adds
   material evidence.
7. Record the checkpoint commit in `plan.md` and `evidence.md`.

A phase is not complete while a Must requirement lacks evidence or an
unresolved critical self-review finding remains.

## Quality gates

Before marking a task complete, verify all applicable gates:

- [ ] MoSCoW requirements and acceptance criteria are satisfied.
- [ ] Design and Mermaid diagrams reflect the implemented architecture.
- [ ] Focused tests passed after an observed red phase.
- [ ] Full affected test suite passes.
- [ ] Critical logic has 100% line and branch coverage.
- [ ] Overall production code has at least 95% line and branch coverage.
- [ ] Property and state-machine tests cover invariant-heavy logic.
- [ ] Mutation tests exercise policy- and integrity-critical logic.
- [ ] Formatting, linting, and strict typing pass.
- [ ] Schemas and generated artefacts validate.
- [ ] Originals and derivatives remain distinguishable and traceable.
- [ ] Idempotency, interruption, retry, and recovery behaviour are tested.
- [ ] Secrets and sensitive values are absent from source, logs, fixtures, and
  evidence.
- [ ] Dependency, licence, workflow, and vulnerability checks pass.
- [ ] Documentation and evidence ledgers are updated.
- [ ] GitHub and Conductor cross-references are current.
- [ ] Local, hosted, and published states are reported separately.
- [ ] No human, credential, publication, rights, or external-system gate was
  bypassed.

## Development commands

These commands become authoritative after the initial implementation track
creates the package and tool configuration.

### Setup

```powershell
uv sync --locked --all-groups
```

### Focused Python development

```powershell
uv run pytest tests/path/to/test_module.py -q
uv run ruff format --check .
uv run ruff check .
uv run pyright
```

### Full Python gate

```powershell
uv run pytest --cov --cov-branch --cov-report=term-missing
```

### Rust gate, when Rust exists

```powershell
cargo fmt --all --check
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo nextest run --workspace --all-features
```

### Repository gate

The initial implementation track must create a single non-interactive repository
check command that runs all applicable formatting, linting, typing, tests,
coverage, schema, security, and generated-artefact checks.

Announce the exact command before running a phase or release gate.

## Test requirements

### Unit and property tests

- Every production module has focused tests.
- Tests cover successful and failed outcomes.
- Hypothesis or an equivalent framework tests invariants and state transitions.
- Time, randomness, network behaviour, and filesystem ordering are controlled.

### HTTP and CKAN contract tests

- Use redacted deterministic fixtures.
- Exercise CKAN success envelopes and error envelopes independently of HTTP
  status.
- Exercise pagination, redirects, conditional requests, range requests,
  timeouts, rate limits, partial responses, and malformed metadata.
- Keep live read-only smoke tests separate from deterministic CI.

### Archive integration tests

- Verify original bytes and metadata are unchanged.
- Verify content hashes and object paths.
- Verify change-driven snapshot selection.
- Verify tombstones and restricted-state behaviour.
- Verify transformations have complete receipts.
- Verify crash recovery and idempotent replay.
- Verify manifests reconstruct a bounded release.

### Publication tests

- Treat local packaging, upload completion, remote existence, remote integrity,
  Dataset Viewer readiness, and DOI publication as separate states.
- Do not require production credentials in pull-request CI.
- Use explicit opt-in environments for credentialed workflows.
- Verify external publications after upload before reporting success.

## Commit guidelines

Use Conventional Commits:

```text
<type>(<scope>): <description>

[optional body]

[optional issue and Conductor references]
```

Common types are `feat`, `fix`, `docs`, `refactor`, `test`, `perf`, `build`,
`ci`, `chore`, `security`, and `conductor`.

Each completed Conductor task should produce a small coherent commit after its
checks and track evidence are current.

## GitHub workflow

- Use a parent issue for each Conductor track.
- Use nested subissues for phases or substantial tasks where supported.
- Put the Conductor track path and requirement identifiers in issue bodies.
- Put issue links in track metadata and evidence.
- Use focused branches and pull requests for implementation.
- Permit the solo maintainer to author, review, and merge.
- Require automated checks appropriate to risk.
- Do not interpret an open or green pull request as proof of merge, deployment,
  archive capture, or publication.

## Definition of done

A task is done only when:

1. its Must requirements and acceptance criteria are satisfied;
2. implementation and documentation are complete;
3. relevant quality and security gates pass;
4. track-local run logs, evidence, and self-review are current;
5. status claims are bounded by verified evidence;
6. external gates are either completed with receipts or explicitly unresolved;
7. the task is committed as a coherent change.

## Incident procedures

### Suspected data loss or corruption

1. Stop write and publication workflows.
2. Preserve logs, manifests, and affected object identifiers.
3. Verify immutable objects and independent hashes.
4. Reconstruct from the latest verified manifest.
5. Record the incident and recovery evidence.
6. Add regression and recovery tests before resuming.

### Suspected credential or security exposure

1. Stop affected workflows.
2. Do not reproduce secrets in issues, logs, or chat.
3. Revoke or rotate affected credentials through the authorised system.
4. Preserve bounded audit evidence.
5. Patch and test the root cause.
6. assess notification obligations with appropriate human review.

### Incorrect public release

1. Stop subsequent publication.
2. Record the exact GitHub, Hugging Face, and Zenodo states.
3. Avoid destructive removal until rights and preservation implications are
   assessed.
4. Use tombstones, restrictions, corrections, or superseding releases as
   appropriate.
5. Verify the corrected remote state.

## Continuous improvement

- Review the workflow after each track.
- Convert recurring manual checks into deterministic automation.
- Keep dependencies current through tested, reviewable updates.
- Evaluate pre-releases in isolated compatibility lanes.
- Record architectural decisions and rejected alternatives.
- Prefer simpler durable standards over novelty without a recovery advantage.
