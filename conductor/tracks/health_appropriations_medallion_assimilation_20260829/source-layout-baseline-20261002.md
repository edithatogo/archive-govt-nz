# Captured-source Silver layout baselines

This report fingerprints structural worksheet/workbook inventories already
recorded by Silver extraction manifests, after checking each linked source
object against the pinned capture manifest and Bronze CAS. It does not inspect
or publish source values, approve normalization, or claim complete discovery.

The pinned capture covers 74 source objects. Six have matching Silver workbook
inventories across ten retained manifests and seven transformation profiles;
68 captured sources remain without a workbook layout baseline. Nine older
Silver manifests do not match this capture snapshot and are listed as outside
scope rather than mixed into the comparison.

The only cross-vintage profile comparison currently available is
`treasury-health-expense-summary/v1` for BEFU-2026 and HYEFU-2025. Their layout
fingerprints differ. This is an observed structural variation; the report does
not infer whether it reflects expected edition changes, semantic drift, or a
normalization requirement. The other six profiles have only one observed
vintage and therefore remain non-comparable.

The remaining 68 sources need source-specific structural baselines or an
explicit reason why a layout baseline does not apply. Calendar completeness,
rights, layout semantics, and source-to-source comparability remain open.

Machine evidence: `source-layout-baseline-20261002.json`, SHA-256
`8fc529607e6a70933b5b649bd4653e7177dd780199771f14b560cdc3a5abe0e7`.

The report is reproducible with `tools/health_source_layout_baseline.py` when
the pinned source census, capture manifest, Silver tree, and Bronze CAS are
available. The focused test verifies captured-byte fixity, repeat stability,
cross-vintage variation, out-of-scope exclusion, and fail-closed malformed
capture evidence.
