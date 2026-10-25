# AGENTS.md

This repository is a solo-maintainer codebase.

## Operator intent
- Primary actor: `edithatogo`.
- Merge policy: the solo maintainer may self-review and self-merge when required
  automated checks are green.
- Confidential handling: never commit secrets, signed URLs, API keys, private
  tokens, personal data, or restricted source artefacts.

## Required command contract
- Run the repository validation harness before opening a pull request:
  - `./scripts/validate.sh` (Linux/macOS)
  - `./scripts/validate.ps1` (Windows PowerShell)
- The harness runs `tools/check.py`, which enforces lock, format, lint,
  typing, tests, schemas, mutation gates, and supply-chain checks.

## Python runtime qualification
- All active Python use in this repository must use CPython 3.15.1 through an
  explicitly selected repo-local interpreter. Verify the interpreter version
  and dependency/runtime behavior in that environment.
- Older version literals may remain only in immutable historical evidence or
  synthetic tests that deliberately exercise version handling.
- Preserve a working latest-version environment and any in-flight operation;
  do not downgrade or rebuild it without a task need.

## Quality boundaries
- Preserve originals and provenance over rewriting.
- Keep gates fast-first; schedule heavier evidence lanes behind explicit triggers.
- Record failures with bounded evidence before making follow-up modifications.

## Project-owned code licensing
- Project-owned code uses Apache-2.0; keep the complete root `LICENSE` and the
  package's `Apache-2.0` declaration aligned.
- Preserve upstream and third-party licences, copyright notices, attribution,
  and applicable inherited terms. Do not relabel third-party code.
- This licence does not grant redistribution rights over external documents,
  datasets, private evidence, or operational history.

## Human accountability
- PR narratives should include issue references, scope, expected outcomes, and
  any risk/failure modes observed.
