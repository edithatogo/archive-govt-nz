# SOC02 — source-native ingestion and normalisation

Status: production pending; independently runnable synthetic prototype outside the repo. Depends on SOC01 source/rights admission. Reuse existing archive acquisition and Arrow/Polars/Pydantic machinery; do not create another crawler or preservation store.

## Contract and source preference

Prefer existing original bytes; next prefer source-native electorate tables and public CSV exports. ADE adapters must resolve actual dataflow version, DSD dimensions and codelists from the current release rather than guess field/status meanings. Infoshare is a migration source, not an assumed permanent endpoint. No credential or signed URL is persisted.

A normalised observation binds source hash, reviewed profile hash, reference period/date, publication/capture time, geographic code/system/boundary, metric/unit/multiplier, population universe, measurement type, confidentiality, status and original record locator. Counts, rates, medians, means and indices have distinct aggregation semantics. Keep suppression, missing, unavailable, estimated, provisional and observed states; never fill missing with zero.

## Executable tasks

- [ ] Adopt reviewed profile/conformance logic from the external `normalise_csv(raw, manifest)` reference into the existing native modules only after the owner assigns exact paths and accepted interface version.
- [ ] Qualify one real original source CSV and metadata against independently read source cells and official totals, allowing documented perturbation discrepancies rather than rewriting published values.
- [ ] Require explicit mapping/filtering of every dimension; do not collapse age, sex, ethnicity, household type or year through an incomplete pivot.
- [ ] Preserve confidential cells as null; verify unit multipliers and percentages; reject malformed numbers, missing hash/rights, duplicate keys and empty filtered extracts.
- [ ] Produce typed long-form Silver with original hashes/locators and source-status audit, then expand one already-admitted cohort at a time.

## Verification and completion

Focused native tests and independently checked real source fixtures; CPython3.15.1 prescribed harness and exact-head review/CI. External tests are not these gates. No native adapter or real Stats NZ observation has been admitted by this planning tranche.

## Handoff prompt

Implement one SOC02 source-profile adapter in an explicitly reserved namespace using the SOC01 original bytes and existing contracts. Retain DSD/version, dimension filters, statistical population, suppression and unit provenance. Qualify independently and hand back source/transform/output hashes with uncovered records. No live acquisition or HF write is implied.
