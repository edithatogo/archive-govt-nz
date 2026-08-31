# Spec - Repository Commit And Release Baseline

## Status
done

## Goal
get the current local implementation into a clean Git baseline before any live data operation is treated as repeatable.

## Acceptance Criteria
- Git history contains a commit for the rate-limit work.
- `uv.lock` is committed.
- Tests and lint pass from the clean checkout.

## Evidence to Record
- Commit SHA.
- Test command output summary.
- Lint command output summary.

## Evidence Recorded

- Commit SHA: `158ffdb4787e43fd038a8c690859d2c98e62c680`.
- Test command output summary: `12 passed in 0.28s` (pytest -q -p no:cacheprovider).
- Lint command output summary: `All checks passed!` (ruff check src/nz_legislation_corpus tests).
- `uv.lock` committed alongside the rate-limit hardening and bootstrap guardrails.
