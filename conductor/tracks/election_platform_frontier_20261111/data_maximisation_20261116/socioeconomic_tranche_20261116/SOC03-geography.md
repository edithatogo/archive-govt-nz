# SOC03 — geography, boundary versions and statistical populations

Status: pending; may run alongside SOC02 once SOC01 metadata is admitted. Existing geographic/shared-key owner retains core interfaces.

## Design

Use direct source-published target-boundary tables before interpolation. Parliament's official electorate-data index lists 2023 Census data by general and Maori electorates on 2025 boundaries; exact underlying tables still require verification. Census observation year and boundary year are different fields. Historical comparison requires the correct election's geometry, not a name-only join.

General and Maori electorate systems overlap geographically and must remain distinct. Census residents within a Maori electorate do not automatically describe Maori-roll electors. Keep residents, eligible population, registered voters, households, families, dwellings and labour force as different statistical universes.

## Executable tasks

- [ ] Reconcile existing 2020/2025 and historical geometry manifests against exact source IDs; qualify direct electorate tables where available.
- [ ] Add reviewed bridges only for compatible source/target vintages and explicit population/count basis. Validate unmatched areas, overlaps, duplicate codes and conservation with published perturbation caveats.
- [ ] Derive rates from compatible numerator/denominator counts. Do not average source percentages unweighted or spatially average medians to manufacture an electorate median.
- [ ] Where only distributions exist, document any derived median as an estimate with methods/uncertainty; with inadequate source information return unavailable.
- [ ] Keep national CPI and regional survey estimates at their published support. No national-to-electorate broadcasting or allocation of survey samples by area as empirical local estimates.

## Verification

Wrong-boundary, general/Maori, SA2/electorate, universe, weight-sum, many-to-many and missing-geometry negative fixtures. The external prototype rejects non-exact joins and non-count rate aggregation; it does not implement or qualify spatial interpolation.

## Handoff prompt

Qualify SOC03 only on the SOC01 boundary/population definitions. Prefer direct electorate tables. Return verified target geography IDs, exact or explicitly estimated method, source populations, coverage and unresolved areas. Escalate shared interface needs to the existing owner; do not replace retained geometries or infer individual political characteristics.
