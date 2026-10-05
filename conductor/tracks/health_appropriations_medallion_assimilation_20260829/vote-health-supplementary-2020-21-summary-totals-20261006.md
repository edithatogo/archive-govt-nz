# Vote Health Supplementary Estimates 2020/21 summary totals

Added a hash-pinned Silver profile for four named rows on PDF page 7 of the
captured 2020/21 Supplementary Estimates. The source object SHA-256 is
fd2afd86cd0f827d5896705bb9eaefe827a645143f3b7573a95d642b455f5bfe; the source
census records the exact Treasury PDF locator. The profile has its own summary
fact schema and output, distinct from the category-total profiles.

The four records retain the three printed Estimates Budget, Supplementary
Estimates Budget and Total Budget columns in the source's $000 units. The
line-wrapped Multi-Year label is parsed across the extracted text, while source
tokens, normalized values, page/field coordinates and the separate summary
versus capital-injection context are retained. The package contains four facts,
12 field-lineage rows and one partial-page disposition. Unselected page-7 rows
and all other PDF pages remain outside this profile.

Two independent source-operation builds and two independent recovery-entry
point builds produced identical manifests and Parquet hashes. The persistent
local Silver package is
silver/vote-health-supplementary-2020-21-summary-totals-20261006-v1; its
manifest SHA-256 is
897d8385ec7251fa830360817970830579c673065882ff5e81d72bb937190c6c. The Bronze
source hash was unchanged. Rights remain not_evaluated; the package is local
validation evidence and asserts no redistribution, currency interpretation,
edition comparison or publication.

The focused tests passed (514 passed, 10 skipped). The repository harness
passed on this implementation tree: 7,522 passed, 10 skipped, 97.74% coverage
against the 80% floor; formatting, lint, typing, 56 schemas/46 representative
documents, differential parity 9/9, configured mutation gates, dependency and
licence audit, secret scan and 113-component SBOM passed. This bounded profile
does not close the Health track or its full clean-room recovery gate.

See the machine evidence
vote-health-supplementary-2020-21-summary-totals-20261006.json for the exact
source, output hashes and bounded validation claims.
