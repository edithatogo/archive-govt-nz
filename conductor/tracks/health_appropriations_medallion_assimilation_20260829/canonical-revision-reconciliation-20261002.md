# Canonical historical revision candidates — 2026-10-02

The source-separated canonical Gold manifest now includes
`revision_reconciliation_report` and the packaged
`historical_revision_reconciliation.json`. It compares only rows sharing exact
recordset, measure, literal source label, unit, currency, price basis, base
period, denominator, institutional coverage, accounting basis, and period
token across observed source vintages. It emits a candidate only when each
vintage has one row and
the exact Decimal values differ. Duplicate observations are counted as
ambiguous and are not collapsed. Values retain their source vintage and
record IDs; change reasons, comparability, and analytical admission remain
unassessed.

The pinned clean-room rebuild found 106 shared historical series-period
coordinates, 98 unchanged, 8 changed candidates, and no ambiguous coordinates
in this input set. The revision report repeated identically in both Gold builds,
its package digest matched the manifest, and Bronze remained unchanged. See
[clean-room recovery receipt](clean-room-recovery-20261002-revision-report.json),
SHA-256 `eb0acc3d9b1e0047d9ac55f106e1c7b0b3f9eaf962f9c3a1c54d300a0936cace`.

This is historical-product-only evidence. Revisions in Budget, Pharmac, MoH,
Crown, remaining source families, source-health criteria, and cross-source
variance remain unresolved. The report does not explain changes, infer missing
periods, join source families, evaluate rights, or authorize publication.
