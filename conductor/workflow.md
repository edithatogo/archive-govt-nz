# Project Workflow

## Bounded delivery — 29 October 2026

Complete the user's selected outcome and stop when its acceptance criteria are
met. The [delivery scope and roadmap](../docs/roadmap.md) is the current boundary.
Do not automatically create another track, expand a corpus, or start the next
roadmap item. Continue all necessary in-scope work without routine permission
questions. This policy supersedes the earlier mandatory per-task documentation
and open-ended track progression requirements.

## Start and implement

1. Inspect the actual checkout, existing edits, active writers and native jobs.
   Use one writer per checkout and native object; isolate overlapping source
   work with the app's managed worktree tools. Preserve private runtime state.
2. State the outcome, owned paths and acceptance check in an existing issue,
   track run log or the registry's current coordination entry. Routine fixes
   need no new track, parent/subissue hierarchy or eight-file document pack.
3. Prefer installed CLI/API commands, locked dependencies and existing helpers.
   Use `uv sync --locked` and verify `.venv/bin/python --version` is 3.15.1.
   Browser work needs a concrete missing CLI capability or visual/auth step.
4. Implement the smallest coherent change. Add meaningful regression tests for
   changed behaviour and important failure cases. Documentation and reversible
   configuration edits do not need artificial red tests.
5. Use `./scripts/test-focused.sh <path-or-node>` while editing. Use `--failed`
   only for cached failures; an empty selection proves nothing. Reuse unchanged
   results. Never replace another operation's environment or disable hooks.

Substantial architecture or storage/publication changes still need a concise
design and acceptance criteria. Existing tracks and historical requirements
remain available; creating duplicate records is optional, not an acceptance gate.

## Validate and deliver

- Run `./scripts/validate.sh` once for a reviewable PR candidate. Its 13-stage
  PR profile retains the complete suite, branch coverage, typing, schemas,
  donor parity, secret scanning, dependency audit, licences and SBOM generation.
- Run `./scripts/validate.sh --profile release` at coherent integration/release
  milestones. It includes all 32 existing stages, including targeted mutation
  runners and CAS benchmarking. Linux CI runs this profile; macOS and Windows
  run the PR profile, including the same full test suite and coverage policy.
- Run affected mutation stages directly for integrity/policy changes. Keep
  gremlins and Scalene opt-in via `--include-heavy`. No test or integrity check
  is deleted, and no partial selection is presented as full-suite evidence.
- If a gate fails, preserve the bounded failure, fix the cause, and rerun that
  stage plus checks affected by the fix (`./scripts/validate-stage.sh <stage>`).
  Do not rerun successful unrelated stages after a reporting/network failure.
- Keep the configured 80% branch-aware overall coverage floor and existing
  critical-path contracts. Do not introduce new blanket 100% targets.
- Review the diff once for correctness, security, preservation and scope. Stage
  named owned paths only; reconcile unexpected deletions before committing.
- Deliver one coherent commit/PR with scope, existing issue references where
  relevant, checks, observed limitations and deferred work. The solo maintainer
  may self-review and self-merge after required checks pass. No additional
  reviewer, separate review ceremony or completion confirmation is required.

A concise completion receipt belongs in the existing coordination/run log or PR.
Record local implementation, native verification and operational acceptance
accurately. Stop when the selected delivery is complete; future improvements
stay on the roadmap until selected.

## Boundaries that remain necessary

Preserve originals, provenance, third-party terms, private data and credentials.
Keep failed/partial/held captures explicit. Code validation does not authorise
source acquisition, publication, emails, workflow activation, rights decisions,
new credentials or destructive operations. Reuse exact existing authority when
it applies; do not ask again for an already-authorised action.

Ask only when a real missing decision prevents the selected outcome. Explain
the exact blocker concisely and continue independent in-scope work. After up to
three materially different recovery attempts, retain an external blocker rather
than retrying unchanged operations or generating more governance work.

## Finite completion and evidence reuse — 2026-10-31

User-approved delivery method for the remaining Health Appropriations and Global
FOI tracks. Existing Must requirements and acceptance criteria remain binding.
This section governs execution cadence when older task or phase wording would
otherwise cause duplicate work; it does not waive required checks.

1. Reconcile open items once against the newest applicable receipts and owned
   changes. In the existing plan/run log, classify each as already evidenced,
   unfinished, blocked by a named dependency, or optional. Close an item only
   when its full acceptance scope is evidenced; retain historical receipts.
2. Freeze a finite completion checklist mapped to existing requirement/task IDs.
   Put optional expansion in a deferred subsection of the existing plan. Do not
   defer a Must, shrink the approved source universe, or reinterpret a partial
   result as acceptance merely to finish sooner.
3. Deliver coherent batches, each with an owner, paths/native scope, concrete
   outcome, definition of done and affected verification commands. Use one
   writing chat per worktree and one owner per native object. Batch related
   changes before PR validation; avoid a PR and broad run for every small edit.
4. Reuse applicable evidence. Record the receipt, command, result, code/input
   hashes, runtime/dependency versions and scope in the existing evidence log.
   Reuse requires unchanged relevant code, tests, configuration, dependencies
   and input bytes. Changed shared dependencies or integration invalidate the
   affected results; time-sensitive native claims require bounded fresh reads.
   Missing provenance or a failed/incomplete run is not passing evidence.
5. Stop at the checklist boundary. Add work only for an observed failure or an
   outstanding approved requirement. New frameworks, speculative hardening,
   broader collections and extra review cycles belong outside this completion
   batch unless required. Reconcile only changed inputs on resume.

| Change/checkpoint | Required verification |
| --- | --- |
| Status or documentation only | Changed links, references, consistency and applicable document checks; no artificial red test. |
| Behavior change | Exact affected tests plus meaningful failure cases; expand to dependent consumers when the contract changes. |
| Fix after a failing test | Failure-only rerun, then affected tests; retain the first failure. |
| Native workflow change | Exact-target readback and bounded runtime proof under existing authority; preserve the mutation journal. |
| PR-ready coherent batch | Repository validation harness before opening the PR, and required hosted checks on the applicable head. |
| Phase/track checkpoint | Applicable full integration, recovery, coverage, security and release gates, satisfied by matching receipts where inputs are unchanged. |
| No relevant input change | Reuse the passing receipt; a phase boundary, new chat or status request alone does not require another run. |

Use the explicitly selected repo-local Python 3.15 runtime and keep pytest's
cacheprovider enabled per worktree/environment. For failure-only reruns use
`--lf --last-failed-no-failures=none`; an empty selection proves nothing.
Do not add selection flags globally, treat partial coverage as full coverage,
weaken gates, suppress findings, or add retries for speed. Default retries are
zero; never retry native mutations or sends through a test runner.

Local implementation, native save/readback, runtime success, publication and
natural scheduled recurrence are separate claims. Missing hosted proof calls
for the missing proof, not another implementation cycle or unrelated full suite.
One final review per coherent batch is sufficient unless changed inputs or an
observed finding justify revisiting it. Reuse its conclusions at later phase
boundaries when its scope still matches.

