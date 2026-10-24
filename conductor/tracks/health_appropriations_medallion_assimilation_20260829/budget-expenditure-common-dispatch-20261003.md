# Budget expenditure common Bronze dispatch

The common hash-bound adapter registry now accepts a caller-supplied Budget
expenditure context and registers the existing named-column workbook adapter.
It can be composed with the separately supplied Budget revenue context and the
reviewed CPI, population, QES, GDP, Pharmac, and Vote Health adapters. Contexts
remain explicit, and dispatch continues to select by media type and reviewed
layout after verifying the source digest.

A synthetic Budget 2025 named-column workbook dispatches through the common
registry and retains the supplied source vintage and fiscal year. The combined
registered-adapter repeatability test now obtains both Budget expenditure and
revenue through the common registry, and verifies repeat-identical selections
and extraction output across all registered fixtures.

This does not add another annual Budget source edition, normalize additional
workbook areas, resolve source rights, or complete longitudinal Budget and
Vote Health coverage. Budget revenue remains one explicit vintage per registry
set. Rights remain `not_evaluated`; publication remains `not_performed`.

Focused registry, repeatability, Budget expenditure/revenue adapter and
common-dispatch tests: 51 passed. The required `./scripts/validate.sh` passed:
7,279 passed, 10 skipped, 98.15% branch-aware coverage against the configured
80% floor; 53 schemas/43 representative documents, 9/9 parity, all configured
mutation gates, hygiene, CAS benchmark, dependency, license, secret, and
113-component SBOM checks. Ruff and basedpyright passed. The automatic
`phase_7_gates` review passed; retained receipt
`phase_7_gates-review-receipt-20261003-budget-expenditure-dispatch.json`, file
SHA-256 `c139cc534414639d54202f5e18f3ecb113571f7d49a01edbb6fec821e746809b`.

Ruff first reported one import-order issue and then one line-wrap issue in the
new registry test file. Both were test-only style corrections. After each was
recorded, Ruff fixed/formatted the file; the final focused suite and full harness
passed.
