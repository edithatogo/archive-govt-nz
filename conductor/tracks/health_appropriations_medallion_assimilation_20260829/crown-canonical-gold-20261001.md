# BEFU and HYEFU core Crown expense in canonical Gold

The canonical Gold package now includes separate BEFU-2026 and HYEFU-2025
core Crown expense products. Each retains its 10 source-record facts and 80
source-coordinate lineage rows in distinct Parquet files. Source vintages,
formula-cache context, source amount tokens and year labels remain intact; the
products are not joined, pooled, compared across vintages, or treated as actual
expenditure. Currency/accounting basis, financial-year boundaries, formula
cache freshness and rights remain unresolved.

The clean-room recovery rebuilt both Silver packages from the pinned Bronze
objects, then built canonical Gold twice with matching file digests. Bronze
objects remained unchanged. Receipt:
[`clean-room-recovery-20261001-crown-gold.json`](./clean-room-recovery-20261001-crown-gold.json),
SHA-256 `a3ede43865a3e6656da3b12f4521de3890739ff60bca5f902623177258908036`.
The four product digests are recorded in its `canonical_gold.files` inventory.

Historical Fiscal Time Series promotion remains open and is tracked separately
in the assimilation plan.
