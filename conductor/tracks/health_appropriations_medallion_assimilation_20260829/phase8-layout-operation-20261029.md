# Phase 8 pinned source-layout operation — 2026-10-29

This closes the bounded M-15 / AC-13 operation slice in Phase 8.1. The CLI
command `health-appropriations-reconcile-source-layout` and MCP tool
`health_appropriations_reconcile_source_layout` call the existing pure
reconciliation contract over explicit, hash-pinned reports.

## Contract and limits

The required inputs are the source census, workbook baseline and recheck, and
PDF baseline and recheck. A text-layout baseline and recheck may be supplied as
a complete optional pair. Inputs must be regular files, each at most 16 MiB,
with an aggregate limit of 48 MiB; all SHA-256 values are checked before
parsing. Symlinks, missing/unpaired pins, oversized inputs, and digest or cohort
mismatches fail with path-free reason codes. MCP arguments and result structures
are typed and closed. The operation creates no files and exposes no source URLs.

The receipt lists captured source IDs, counts, report pins, and reason-coded
unassessed source IDs. It makes no rights, normalization, semantic mapping,
period comparability, or publication determination. PDF evidence remains limited
to structural geometry/resource metadata.

## Retained input pins

| Input | SHA-256 | Bytes |
| --- | --- | ---: |
| Source census | `aa6f9d55ed8f416c8ea890add9ecc5363cbe4c0333f7efaa02db9fd6d44df272` | 98,511 |
| Workbook baseline and recheck | `d876c92097bbd1c209fbaaadfd2f3cabcc03ab742cd7aed11763a98163b4ba6a` | 151,912 each |
| PDF baseline and recheck | `481f1e486e2f96943710cad49a2a8bdf8eb20f815399090577521399d514df9b` | 287,583 each |
| Text baseline and recheck | `a0ce61a182666998330397a3cd064955626cf8f46ca096b946093d2219f6216c` | 13,447 each |

The census and capture-manifest identities are respectively
`aa6f9d55ed8f416c8ea890add9ecc5363cbe4c0333f7efaa02db9fd6d44df272` and
`017b3a9adbda288c60693ef038e4c0da198d8db99b2bca9cf4bb81adbc6efb5f`.

## Result

The operation reconciled 75 captured identities: 69 have a structural layout
baseline (6 workbook, 59 PDF, 4 text); 6 remain unassessed with explicit source
IDs and reasons. The same source reports without the text pair leave ten
unassessed, demonstrating that the optional text evidence is accounted for.

## Validation

- Focused source-layout and operation tests: 40 passed.
- `uv run --locked ruff check` on the four changed Python files: passed.
- `uv run --locked python tools/check.py --stage types`: zero errors, warnings,
  or notes.
- Exact-tree `./scripts/validate.sh`: passed on CPython 3.15.1; 8,742 passed,
  14 capability skips, 96.43% branch coverage (80% configured floor), 95
  schemas / 85 representative documents, differential parity 9/9, mutation and
  hygiene gates passed, dependency and licence audits passed, secrets scan
  passed, and validated SBOM contained 118 components.

This evidence closes only the bounded interface task. Hosted PR delivery and
the remaining Phase 8 command matrix, scheduled capture/normalization, recovery,
and overall Health track gates remain open.
