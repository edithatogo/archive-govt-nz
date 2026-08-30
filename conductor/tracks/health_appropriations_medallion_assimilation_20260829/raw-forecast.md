# Raw BEFU/HYEFU Health expense summaries

`tools/build_health_forecast.py` extracts literal Health summary values from
verified Bronze workbook bytes. It does not read the donor database as input.
The donor's two ten-row tables remain independent reconciliation oracles.

## Command

With `HEALTH_ARCHIVE_ROOT` pointing to the existing external archive:

```sh
uv run --locked python tools/build_health_forecast.py \
  --source "$HEALTH_ARCHIVE_ROOT/bronze-cas/sha256/db/dbde3256b1cbfb847f9f6caec66e7adffabca0489b218997a431220da584a3d6" \
  --expected-sha256 dbde3256b1cbfb847f9f6caec66e7adffabca0489b218997a431220da584a3d6 \
  --profile befu \
  --source-vintage BEFU-2025 \
  --source-locator data/raw/befu25-data-expense-tables.xlsx \
  --observed-at 2026-08-30T07:32:37.408769+00:00 \
  --output-dir "$HEALTH_ARCHIVE_ROOT/silver/befu-2025-new"
```

The example observation time is the local Bronze-object verification time,
not a claimed new HTTP retrieval. Operational callers must supply their actual
verified source observation context. For HYEFU, use profile `hyefu`, its own
digest/path, and vintage `HYEFU-2024`; never relabel one vintage as another.

## Contracts

- Exact sheet profiles select `Core Crown Expense Tables` (BEFU) or
  `Expense Tables` (HYEFU). Semantic anchors discover the unique literal Health
  label, the nearest preceding same-column `($millions)` label, consecutive
  year columns and corresponding Actual/Forecast labels. Row/column shifts
  are supported; missing, duplicate or ambiguous anchors fail closed.
- Year values and amount types retain their source meaning. An Actual after
  a Forecast in ascending years is rejected as an unrecognized layout. Bare
  year labels do not establish fiscal-year endpoints; those remain null and
  quality-flagged until supported by source evidence.
- Literal amounts become fixed-decimal NZD-million facts. Zero and negative
  values are retained; precision is never silently rounded. Formula, error,
  blank or invalid amount cells are explicit rejections. The distinct detailed
  Health expense formula totals are not substituted from cached values.
- `forecast_facts.parquet` uses the existing Silver schema.
  `field_lineage.parquet` links six fields per fact to the original year,
  amount, amount-type, Health-label and unit cells. Shared context cells retain
  all their uses through lineage rather than choosing one arbitrary fact.
- `cell_dispositions.parquet` accounts for nonempty cells plus selected inputs
  in the chosen sheet. Selected blank amounts therefore remain visible.
  Other populated cells are `preserved_only`, with the explicit reason
  `outside_literal_health_summary`; unselected blank extents are represented
  by workbook inventory. Other worksheets have explicit exclusions.
- New directories and exclusive output-file creation prevent overwriting
  originals or existing derivatives. `MANIFEST.json` is written last with
  output hashes. Failed writes can leave an incomplete directory; consumers
  must verify the complete manifest and hashes, not directory existence.
- The source is one capped, verified snapshot. Originals remain unchanged.
  Rights are not inferred, and no upload, candidate replacement, donor
  retirement or formula evaluation occurs.

The command exits zero for a fully extracted selected summary, two for partial
extraction, and nonzero for unsupported layouts, hash/context errors or I/O
failures. A passed summary extraction is not complete workbook normalization.

## Continuation

Local verified builds are retained separately in the external archive at
`silver/raw-befu-20260830-forecast-v1` and
`silver/raw-hyefu-20260830-forecast-v1`. Their manifest SHA-256 values are
`0997a9153d5da334860cd43cc850ed3c4b5f768e9729927311fbc91d7e9f4634`
and `1e0e9a173d718acd77c11f729d874a6fa96456ca28bf0fab9dca7b544965e0fd`,
respectively. Each has ten facts and 60 lineage rows; together they account
for 4,665 cells. Repeated builds match byte for byte. These derivatives have
not replaced or updated the published candidate.

Historical health/GDP extraction follows, preserving March/June periods,
accounting-basis transitions, annotated years and any differences from the
incomplete donor health oracle. Detailed expense breakdowns, remaining donor
workbook areas, expanded official sources and conformed analytics remain in
the parent track; preservation-only dispositions do not close those tasks.
