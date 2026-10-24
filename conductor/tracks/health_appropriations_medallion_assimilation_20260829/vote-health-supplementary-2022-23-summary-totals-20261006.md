# Vote Health Supplementary Estimates 2022/23 summary totals

Added a hash-pinned Silver profile for four named rows on PDF page 5 of the
captured 2022/23 Supplementary Estimates. The source object SHA-256 is
`98cd7a110628349648926007ba37d6ca9f5ad4525e1d9fdf34a94560e3078741`; the source
census records the exact Treasury PDF locator. The profile has its own summary
fact schema and output, distinct from the category-total profiles.

The four records retain the three printed Estimates Budget, Supplementary
Estimates Budget and Total Budget columns in the source's `$000` units. The
line-wrapped Multi-Year label, parenthesized negative values, source tokens,
normalized values, page/field coordinates and separate capital-injection
context are retained. The package contains four facts, 12 field-lineage rows
and one partial-page disposition. Unselected page-5 rows and all other PDF
pages remain outside this profile.

Two independent recovery-entry-point builds produced identical output
manifests and Parquet hashes. The persistent local Silver package is
`silver/vote-health-supplementary-2022-23-summary-totals-20261006-v1`; its
manifest SHA-256 is
`f2fc52e56ee995791b3e9a94e8f19d6ad7a0629f7895567c316eb4ec93328daa`. The Bronze
source hash remained unchanged. Rights remain `not_evaluated`; this local
package asserts no redistribution, currency interpretation, edition comparison
or publication. Full track recovery remains partial with blockers.

Focused tests passed: 516 passed, 10 skipped. The integrated clean-room recovery
receipt includes this lane and remains `partial_with_blockers`; all Bronze
objects were unchanged, and this lane rebuilt identically twice. The full
repository harness passed: 7,526 passed, 10 skipped, 97.70% coverage against
the 80% floor; formatting, lint, typing, schema, parity, mutation, dependency,
licence, secret-scan and SBOM gates passed. Hosted checks for the follow-on PR
remain pending.
