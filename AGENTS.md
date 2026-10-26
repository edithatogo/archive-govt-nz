# AGENTS.md

This repository is a solo-maintainer codebase.

## Operator intent
- Primary actor: `edithatogo`.
- Merge policy: the solo maintainer may self-review and self-merge when required
  automated checks are green.
- Confidential handling: never commit secrets, signed URLs, API keys, private
  tokens, personal data, or restricted source artefacts.

## Required command contract
- During implementation, run only the affected pytest file/node with
  `./scripts/test-focused.sh <path-or-node>` and the affected non-test gates.
  Keep pytest's last-failed cache enabled; after a failure, use
  `./scripts/test-focused.sh --failed` only when its cache names the failures.
- Run the complete repository validation harness once for a reviewable PR
  candidate:
  - `./scripts/validate.sh` (Linux/macOS)
  - `./scripts/validate.ps1` (Windows PowerShell)
- If a single harness stage fails, preserve its output and rerun only that
  named stage with `./scripts/validate-stage.sh <stage>`. After a fix, rerun
  the failed stage and every directly affected gate. Do not restart the full
  harness for an unrelated storage/reporting failure when the tree and gate
  inputs are unchanged. Repeat the complete harness when source, tests,
  dependencies, configuration, runtime, or generated evidence affecting
  multiple gates changes. Hosted CI remains the full PR assurance gate.
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
