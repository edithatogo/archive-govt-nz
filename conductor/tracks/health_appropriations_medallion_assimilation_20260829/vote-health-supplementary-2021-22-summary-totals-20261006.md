# Vote Health Supplementary Estimates 2021/22 summary totals

Added a hash-pinned Silver profile for four named rows on PDF page 7 of the
captured 2021/22 Supplementary Estimates. The source object SHA-256 is
`f567098d4f98fd9ea34df90ca330b295346a8f567b924f8b11694a494d3ce502`; the source
census records the exact Treasury PDF locator. The profile has its own summary
fact schema and output, distinct from the category-total profiles.

The four records retain the three printed Estimates Budget, Supplementary
Estimates Budget and Total Budget columns in the source's `$000` units. The
line-wrapped Multi-Year label is parsed across extracted text, while source
tokens, normalized values, page/field coordinates and separate summary versus
capital-injection context are retained. The package contains four facts, 12
field-lineage rows and one partial-page disposition. Unselected page-7 rows and
all other PDF pages remain outside this profile.

Two independent recovery-entry-point builds produced identical output
manifests and Parquet hashes. The persistent local Silver package is
`silver/vote-health-supplementary-2021-22-summary-totals-20261006-v1`; its
manifest SHA-256 is
`5f34467c812ce43f5fa20b369c5314f4ab7a5ceeec1c697a060483bed528d466`. The Bronze
source hash remained unchanged. Rights remain `not_evaluated`; this local
package asserts no redistribution, currency interpretation, edition comparison
or publication. Full track recovery remains partial with blockers.

Focused tests passed: 515 passed, 10 skipped. The full repository harness passed: 7,519 tests passed, 10 skipped, 97.72%
coverage against the 80% floor; formatting, lint, typing, 56 schemas / 46
representative documents, 9/9 differential parity, configured mutation gates,
dependency and licence audit, secret scan and 113-component SBOM all passed.
Hosted checks for the follow-on PR remain pending.
