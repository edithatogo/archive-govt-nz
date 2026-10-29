# Health deflator revision discovery — 2026-10-29

Owner: chat `01a09968-c894-77c3-be45-0c2db277bfc2`; standard Git checkout
`/Users/doughnut/.codex/worktrees/health-census-next/archive-govt-nz`, branch
`codex/health-census-next`. Scope is this source-discovery evidence; no native
object mutation. Next: identify and qualify the exact component series.

This is a source-discovery observation, not a captured original, numeric series,
rights qualification, analytical policy, or approval of a Vote Health join.

Stats NZ's [December 2021 quarterly national accounts methodology](https://datainfoplus.stats.govt.nz/item/nz.govt.stats/2dcb8c32-ed2c-46e0-b205-8bd945520ef7)
identifies a correction to a composite deflator for the healthcare sales
component of central government final consumption expenditure. An input index
had ceased to be available; an equivalent index was included from the March
2019 quarter. The publisher states that the correction affected constant-price
series and did not affect current-price series. This is a healthcare-sales
component observation, separate from compensation of employees and from the
whole Vote Health appropriation.

The [2018 quarterly GDP sources and methods, fifth edition](https://www.stats.govt.nz/assets/Uploads/Methods/Quarterly-gross-domestic-product-Sources-and-methods-fifth-edition/quarterly-gross-domestic-product-sources-and-methods-fifth-edition.pdf)
also describes a historical central-government health production indicator
based on district health board salaries and wages deflated by an LCI sub-index.
Its annual method separately deflates balanced intermediate consumption using
annualised PPI. This supports distinguishing wage and input components; the
manual does not identify the selected LCI sub-index as `LCI025AC`, establish
the current method, or support applying it to all Vote Health appropriations.

The later [component-index source evidence](./component-index-source-evidence-20261018.md)
supersedes the earlier discovery-only coverage description: it identifies
retained, hash-bound source CSVs and selection files for LCI025AA/LCI025AC and
PPI021AA/PPI021CC. LCI has 69 numeric quarters and 66 publisher-missing values;
PPI has 120 numeric quarters and nine publisher-missing values. The PPI
selection includes social assistance and is not restricted to central
government. Neither retained selection identifies the healthcare-sales
composite deflator or proves equivalence to the historical LCI sub-index.
The next eligible step is source-separated Silver normalization from the
retained objects, subject to the existing admission contracts; no recapture is
needed. Rights and analytical policies remain separate and unresolved.

The existing register's [September 2022 methodology](https://datainfoplus.stats.govt.nz/item/nz.govt.stats/81c86948-c813-486a-b46b-0c614f03291a/4)
describes a separate improvement to the health compensation-of-employees
deflator and deferred alignment of health compensation volumes with production
measurement. Neither notice identifies an exportable numeric index, its full
weights, current methodology, a rights decision, or an appropriation join.

Disposition: **pending** exact series identity and export, current methodology,
coverage, base, weights, revision policy and resource-specific rights evidence.
Keep these components and vintages separate; do not apply either as a general
health-spending deflator. Observation used rendered official page text; no source
bytes were collected or hash-pinned, and prior evidence remains unchanged.
