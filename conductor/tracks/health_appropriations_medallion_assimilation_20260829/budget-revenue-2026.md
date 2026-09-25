# Budget 2026 revenue Silver checkpoint

This is a source-specific expansion of the existing Budget 2025 Health revenue
adapter. It does not complete annual Budget revenue coverage or Phase 5.2.

## Source and capture evidence

- Capture manifest: external
  \`manifests/official-capture-2026-08-29-complete.json\`.
- Source ID \`budget_2026-001\`; official locator:
  https://budget.govt.nz/budget/excel/data/b26-revenue-data.xlsx.
- Capture manifest records 104,536 bytes, SHA-256
  \`8243f6a3f9575af5ee048133f2695f3c4764ff7d86e7a74849fdafcf478cbfdb\`,
  status \`captured\`, and resource rights \`eligible\` under CC-BY-4.0.
- The original remains at the content-addressed external Bronze path. The
  normalizer re-read and verified those exact bytes. Extraction and canonical
  package rights remain \`not_evaluated\`; the capture rights receipt is not
  converted into a new derivative rights decision.

## Silver extraction

The edition-specific profile preserves Budget 2026's own year definitions:
2022–2025 \`Actuals\`, 2026 \`Estimated Actual\`, and 2027 \`Main Estimates\`.
It validates the exact B3 edition statement and the workbook's shared unit,
period, amount-type, and App ID definitions. It does not reuse the Budget 2025
year map.

The retained Silver package is outside Git at
\`silver/raw-budget-2026-revenue-20260925-v1\`. Its manifest SHA-256 is
\`ff0a5494737378b4741663f1d190bf24971e3d6ee7a17da93fe7b3cdbd5ffdb2\`.
It accounts for all 995 Raw Data rows: 70 normalized Health rows, 925
non-Health rows explicitly out of scope, zero blanks, and zero rejected rows.
The 70 facts comprise 56 Non-Tax Revenue and 14 Capital Receipts observations;
all retain \`$000\`, unknown currency, exact amount token, year, amount type,
source row, and field lineage. No tax revenue rows occur in this workbook.

## Canonical projection and readback

The verified local projection is outside Git at
\`silver/canonical-budget-2026-revenue-20260925-v1\`. Its
\`LOCAL_REVENUE.json\` SHA-256 is
\`134b792ab4e9528b6c312d7794ad8548b49bba9119dcf0116e01720589434c18\`.
Independent \`read_verified_canonical_tables\` readback verified 70
\`revenue_fact\` rows and 630 \`field_lineage\` rows against both the extraction
manifest and Bronze original.

The read-only canonical consumer returned 70 observations across all six
source years with \`aggregation: none\`, \`netting: prohibited\`,
\`currency_state: unknown\`, \`rights_state: not_evaluated\`, and
\`publication: not_performed\`.

A second clean temporary extraction and canonical export reproduced the raw
manifest, all three Parquet files, and every canonical package byte exactly.
The Bronze object's SHA-256 remained unchanged at the pinned digest.

This checkpoint closes one captured 2026 revenue workbook through local Silver
and canonical readback. It does not cover other Budget editions, Vote Health
Estimates, BEFU/HYEFU, rights approval, Gold reconciliation, or publication.
