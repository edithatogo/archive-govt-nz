# Context-source Bronze adapter integration

This increment connects the existing source-faithful CPI, annual population,
QES and GDP extractors to the common hash-bound Bronze dispatcher. Each adapter
requires its exact reviewed header/workbook layout and caller-provided locator,
vintage and observation time. The composed registration set is deterministic.
Unknown layouts remain preserved-only; exact source fixity is checked before
extraction. The adapters retain input records, source-cell lineage and
reason-coded exclusions. Population remains context-only and is explicitly not
selected as an expenditure denominator; CPI is not asserted to be a health
input-cost deflator; QES currency and adjustment are not inferred; GDP remains
quarterly and current-price with currency unverified.

The annual population normalizer now has a two-build acceptance test requiring
identical manifest bytes and Parquet bytes for identical input and context.

The four context adapters also emit stable dimension assertions and source-row links
for literal series, period, unit, geography and measure-context labels. Every
mapping target remains unresolved, with no evidence or crosswalk asserted.
`schema_drift.py` provides deterministic Arrow-schema and canonical layout
fingerprints plus added/removed/changed drift reporting. The caller supplies
the layout contract; fingerprints detect change but do not authorize
normalization.

Validation for this integrated increment is in `context-adapters.validation.json`.
The exact Pharmac CPB HTML profile also has a common-dispatch adapter; it does
not cover arbitrary HTML or other Pharmac pages. The broader Phase 3 checkpoint
still needs other source-operation profiles, Vote Health PDF layouts, SQLite
adapters, evidence-backed crosswalks, captured per-adapter layout baselines, and
repeat-build checks across all profiles. Rights assessment, source acquisition,
analytical admission, publication and operational acceptance are unchanged.
