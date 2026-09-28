# Context Gold verifier — 2026-09-29

## Delivered

Added a read-only verifier for contextual Gold packages. It requires an
independently supplied SHA-256 pin for the exact manifest bytes; checks the
closed three-file inventory (`context_observations.parquet`,
`context_coverage.parquet`, and `context_quality.parquet`); and verifies each
declared file size and digest. CLI and read-only MCP return the same compact
receipt. Tampering, extra files, duplicate manifest keys, and an invalid pin
fail closed without writing a failure file.

## Boundary

Verification proves manifest-declared output fixity and package closure only.
It does not recompute source facts, establish whole-source completeness,
evaluate rights, select a denominator, or claim publication.

## Validation

- Focused Context Gold builder/verifier tests: 15 passed.
- Ruff and basedpyright: passed.
- Full local `./scripts/validate.sh` and hosted exact-head checks are pending.
