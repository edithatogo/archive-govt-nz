# Vote Health Supplementary Estimates 2019/20 category totals

Added an edition-specific Silver profile for the seven printed category totals
on PDF pages 2–6 of the captured 2019/20 Supplementary Estimates. The separate
profile is pinned to the Bronze object SHA-256
`a38e8520b07207670cb139d6814605659d457a626ee070db2bdc91075211e418`; its
manifest also records the exact Treasury PDF locator.

The profile retains the three printed columns—Estimates Budget, Supplementary
Estimates Budget and Total Budget—in the source's `$000` units. It preserves
dash tokens as null, parenthesized amounts as negative values, and page/category
coordinates in lineage. It emits seven facts, 21 field-lineage rows and five
page dispositions. Only these seven totals are normalized; all other PDF pages
and rows remain outside this profile.

The profile was rebuilt twice from Bronze in the integrated recovery runner;
all output hashes matched and the Bronze CAS remained unchanged. The verified
Silver package is persisted outside Git at
`silver/vote-health-supplementary-2019-20-category-totals-20261006-v1`. Rights
remain `not_evaluated`; no currency interpretation, cross-edition join or
publication is asserted.

See the [machine evidence](./vote-health-supplementary-2019-20-category-totals-20261006.json)
for output hashes, validation and bounded recovery status. The profile and
normalizer require the exact captured Treasury locator, object SHA-256 and
vintage. Focused tests passed (513 passed, 10 skipped). The final tree passed
`./scripts/validate.sh`: 7,505 passed, 10 skipped, 97.76% coverage against the
80% floor; formatting, lint, typing, 56 schemas/46 representative documents,
differential parity 9/9, configured mutation gates, secret scan and supply
chain checks passed, including the 113-component SBOM. The integrated recovery
receipt remains `partial_with_blockers`; this bounded source profile does not
close the Health track.
