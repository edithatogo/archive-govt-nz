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

## Quality boundaries
- Preserve originals and provenance over rewriting.
- Keep gates fast-first; schedule heavier evidence lanes behind explicit triggers.
- Record failures with bounded evidence before making follow-up modifications.

## Human accountability
- PR narratives should include issue references, scope, expected outcomes, and
  any risk/failure modes observed.
