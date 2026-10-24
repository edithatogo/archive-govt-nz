# Budget revenue common Bronze dispatch

The common hash-bound adapter registry now accepts one explicit Budget revenue
context per registration set. It composes the existing edition-specific parser
for Budget 2025 or Budget 2026 with the CPI, population, QES, GDP, Pharmac and
Vote Health profiles. The selected adapter is still the reviewed
`nz-budget-health-revenue` implementation; the caller-supplied vintage and
layout must agree with the embedded edition or selection remains
`preserved_only`.

Synthetic tests dispatch both reviewed edition layouts through the common
registry and assert the exact source vintage and year are retained. The
registered-adapter repeatability test now obtains Budget 2025 revenue through
the common registry instead of adding it separately. The existing Budget
revenue adapter tests continue to cover direct fact, disposition, lineage and
unsupported-layout behavior.

This connects common dispatch only. It does not expand captured-edition
coverage, normalize additional workbook areas, resolve rights, map revenue
semantics, or create annual/Gold comparisons. Rights remain `not_evaluated` and
publication remains `not_performed`. The parent annual Budget and Vote Health
coverage work remains open.

Focused registry, repeatability, adapter and dispatcher tests: 40 passed.
The required `./scripts/validate.sh` passed: 7,278 passed, 10 skipped, 98.15%
branch-aware coverage against the 80% floor, 53 schemas/43 representative
documents, 9/9 parity checks, configured mutation gates, hygiene, CAS benchmark,
dependency, license, secret and 113-component SBOM checks. Ruff, basedpyright,
and the automatic `phase_7_gates` review passed. Receipt:
`phase_7_gates-review-receipt-20261003-budget-revenue-dispatch.json`, SHA-256
`b81dc0c7b2e386d1f01c3d7ae512ee9f87e3031e862add345390e273293d9387`.

The first test attempt used a non-ISO `observed_at` value and correctly failed
at source-context validation; the fixture was corrected and all focused tests
passed. The first full-harness attempt stopped at formatting on two test-line
wraps; Ruff formatting corrected them and the full harness then passed.
