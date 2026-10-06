# Vote Health Supplementary Estimates 2023/24 summary totals

Added a hash-pinned Silver profile for four named rows on PDF page 5 of the
captured 2023/24 Supplementary Estimates. The source object SHA-256 is
`7c35d7c49827e5f4a478203007fb388f3f403698765472ab5e44167ed61c2b72`; the source
census records the exact Treasury PDF locator. The profile has its own summary
fact schema and output, distinct from the category-total profiles.

The four records retain the three printed Estimates Budget, Supplementary
Estimates Budget and Total Budget columns in the source's `$000` units. The
line-wrapped Multi-Year label, parenthesized negative values, dash tokens,
source tokens, normalized values, page/field coordinates and separate
capital-injection context are retained. The package contains four facts, 12
field-lineage rows and one partial-page disposition. Unselected page-5 rows and
all other PDF pages remain outside this profile.

Two independent recovery-entry-point builds produced identical output
manifests and Parquet hashes. The persistent local Silver package is
`silver/vote-health-supplementary-2023-24-summary-totals-20261006-v1`; its
manifest SHA-256 is
`c8b1f4bd2ee5fb11972f14dff81ee6226ccba85357943ad52890d921f4e29c3d`. The Bronze
source hash remained unchanged. Rights remain `not_evaluated`; this local
package asserts no redistribution, currency interpretation, edition comparison
or publication. Full track recovery remains partial with blockers.

Focused tests passed: 517 passed, 10 skipped. The integrated recovery receipt
remains `partial_with_blockers`. `./scripts/validate.sh` passed: 7,533 passed,
10 skipped, 97.68% coverage against the 80% floor; format, lint, strict typing,
schemas, parity, mutation, dependency audit, licences, secret scan and SBOM
checks passed.
