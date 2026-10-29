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
