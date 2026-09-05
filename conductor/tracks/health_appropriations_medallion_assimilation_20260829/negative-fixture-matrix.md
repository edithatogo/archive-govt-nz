# Phase 3.1 negative-fixture checkpoint

This closes the planned negative-fixture coverage task for the existing bounded
profiles, not source coverage, donor parity, canonical promotion or Phase 3.
All new inputs are synthetic; main's pending fixture files remain untouched.

| Negative contract | Executable evidence |
| --- | --- |
| Binary-as-text decoding | `test_health_recordset_normalization.py::test_json_invalid_and_binary_inputs_are_redacted` rejects workbook/PDF/SQLite magic and invalid UTF-8 through explicit JSON-byte admission |
| Unknown layouts | `test_budget.py::test_unknown_headers_fail_before_output`, `test_forecast.py::test_layout_drift_fails_before_output`, `test_historical.py::test_unknown_layout_fails_without_outputs` |
| Ambiguous units | Forecast layout tests reject changed unit labels; `test_moh_indicators.py::test_exact_profile_retains_published_unknowns` keeps unestablished units null |
| Duplicate members and IDs | Normalization nested-member rejection and duplicate-ID tests; Ministry duplicate-header/period fixtures |
| Incompatible periods | Normalization reversed-date/unknown-offset/UTC-overflow tests and forecast layout/context tests |
| Missing lineage | All-eight-set required-field negatives plus Budget/classification/historical projection source-consistency and table-contract tests |
| Formula/cache ambiguity | Budget/forecast/historical formula rejection, `test_formula_cache.py` stored-value/error/empty characterization; caches are never evaluated or treated as fresh |
| Unjustified classification mapping | `test_budget_classification.py::test_unreviewed_labels_rejected` and `test_unmapped_occurrences_are_not_pooled`; labels stay unmapped rather than acquiring an authoritative scheme |
| Arrow/Parquet semantic drift | `test_arrow_parquet_readback_revalidates_rows` rejects required nulls, wrong version constants, missing fields and schema metadata drift after typed conversion |
| Exact money and source context | All-eight-set replay, precision-boundary/property tests, two-vintage ordering, nullable units, unchanged restricted/not-evaluated rights labels |

Schema-level validation does not verify that supplied lineage pointers resolve
to source objects. Source-profile tests establish their bounded joins; other
source families still need equivalent qualification. No rights label or mapping
evidence in a fixture is an accountable decision.

The combined focused command and immutable code/test hashes are recorded in
`normalization-admission-validation.json`. Full combined repository checks stay
with the parent by explicit user instruction; no concurrent full harness ran
for this checkpoint.
