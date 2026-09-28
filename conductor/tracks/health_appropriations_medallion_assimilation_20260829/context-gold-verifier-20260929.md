# Context Gold verifier — 2026-09-29

## Delivered

Added a read-only verifier for contextual Gold packages. It requires an
independently supplied SHA-256 pin for the exact manifest bytes; checks the
closed inventory of four core outputs plus up to four per-series plots; and
verifies every declared file size and digest. It also checks that rendered
plots correspond one-to-one with the plot report and its declared digest/size.
CLI and read-only MCP return the same compact receipt. Tampering, extra files,
duplicate manifest keys, and an invalid pin fail closed without writing a
failure file.

## Boundary

Verification proves manifest-declared output fixity and package closure only.
It does not recompute source facts, establish whole-source completeness,
evaluate rights, select a denominator, or claim publication.

## Validation

- Focused Context Gold plotting, builder and verifier tests: 37 passed.
- Ruff and basedpyright: passed.
- `./scripts/validate.sh`: passed locally on this change; 7,096 passed, 9
  skipped, 98.09% branch coverage; 52 schemas/42 representative documents;
  parity 9/9; all mutation, benchmark, vulnerability, licence, secret, and
  SBOM checks passed. Hosted exact-head assurance is pending.
