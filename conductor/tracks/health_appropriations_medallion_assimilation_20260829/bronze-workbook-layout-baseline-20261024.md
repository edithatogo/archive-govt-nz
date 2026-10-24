# Bronze workbook structural baselines — 24 October 2026

The read-only `health_bronze_workbook_layout` builder rechecks every captured
object against the pinned 2026-10-03 source census, capture manifest, size and
SHA-256 before it inventories an XLSX. The inventory is structural: workbook
package members and sheet structure are fingerprinted, without including cell
values. It does not normalize the source, establish cross-vintage comparability,
or grant rights or mapping approval.

The pinned cohort contains 75 captured sources, including 12 XLSX workbooks.
All 12 yielded structural baselines, including six with no matching retained
Silver workbook inventory. The report records parser `openpyxl` 3.1.5 and binds
to census SHA-256 `aa6f9d55ed8f416c8ea890add9ecc5363cbe4c0333f7efaa02db9fd6d44df272`
and capture-manifest SHA-256
`017b3a9adbda288c60693ef038e4c0da198d8db99b2bca9cf4bb81adbc6efb5f`.

Rebuild with `tools/health_bronze_workbook_layout.py`, pointing `--cas-root` at
the `sha256` directory inside the retained Bronze CAS. The focused contracts
cover repeat-build identity, omission of cell values, object-fixity checks and
complete capture-to-census reconciliation. The machine receipt SHA-256 is
`29a8501358c358874225df9099f32b19f29649c7cd9e000b2f23be1fe6f8dd0d`.

Three captured CSV sources and one HTML source still lack structural profiles.
The separate source-layout cohort recheck remains constrained by six captured
workbooks with no Silver-derived workbook inventory; this new Bronze baseline
records their structure without implying a Silver parse. Per-adapter drift
integration and source-specific CSV/HTML baselines remain open.
