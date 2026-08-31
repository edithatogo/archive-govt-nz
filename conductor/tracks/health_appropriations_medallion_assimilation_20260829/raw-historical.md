# Historical Health spending and nominal GDP

`tools/build_health_historical.py` reads the pinned Treasury fiscal workbook
from Bronze and emits separate historical Silver facts, field lineage, cell
dispositions and a completion manifest. It does not use donor SQLite as input.

## Source-faithful contracts

- The supported currency profile validates `$ millions`, `Health` and
  `Nominal GDP` anchors and the known year/amount columns. It scans consecutive
  year rows beginning at row 5. Unknown headers, internal year gaps, duplicate
  years, ambiguous notes and unsupported period labels fail closed.
- Literal OOXML numeric tokens are converted exactly to decimal128(38,17).
  Original numeric spelling and number format are retained. No display-format
  or binary-float rounding is used. Unsupported precision, blank amounts,
  errors, formulas and nonnumeric amounts have explicit rejection reasons.
- March and June source labels establish year-end context. The old-GAAP label
  inherits the preceding June context with separate lineage. Annual starts
  remain null; basis transitions do not establish comparability.
- Annotated years retain their markers and linked footnote text. Every year-end
  has lineage to both the year and period label. Amount tokens and number
  formats also have source-cell lineage.
- The `% GDP` area is not read as currency. Nonempty unselected cells and
  selected blanks receive dispositions; other worksheets are explicitly
  excluded from this narrow selection, not discarded or declared normalized.
- A capped hash-verified snapshot passes the existing package and traversal
  checks. The additional lexical XML reader rejects DTDs and ambiguous sheet,
  relationship, cell and value records. It does not evaluate formulas or fetch
  external relationships. This is not a process-isolation claim for openpyxl.
- Outputs require a new directory and exclusive files. The manifest is written
  last; incomplete directories are not complete or automatically resumable.
  Rights remain `not_evaluated`, and no publication or original replacement occurs.

## Reproduction

Supply the actual observation context and a new output directory:

```sh
uv run --locked python tools/build_health_historical.py \
  --source "$HEALTH_ARCHIVE_ROOT/bronze-cas/sha256/76/769f2e7dd6000878cd29c2d913ad6979f28c5391c971292e6abf6148e83eb32d" \
  --expected-sha256 769f2e7dd6000878cd29c2d913ad6979f28c5391c971292e6abf6148e83eb32d \
  --source-locator data/raw/fiscaltimeseries1972-2024.xlsx \
  --source-vintage fiscal-2024 \
  --observed-at "$HEALTH_SOURCE_OBSERVED_AT" \
  --output-dir "$HEALTH_ARCHIVE_ROOT/silver/historical-new"
```

Exit zero means all selected amounts normalized; exit two means explicit
partial extraction. Unsupported structure or I/O/integrity failure exits nonzero.
Neither status implies full-workbook or full-track completion.

## Verified local artifacts

The external archive retains `silver/raw-historical-20260830-v1`: 106 facts
(53 Health and 53 GDP), 1,143 lineage rows, 1,503 cell dispositions and zero
rejected amounts. Manifest SHA-256:
`2f39ad4dbeb7cb872118ddc634985b5e21b18f2ef2421ca3c0a1e9bf90411288`.
Two library builds and a CLI build match byte for byte, with unchanged originals.
Observation context records local source verification, not a new HTTP capture.

`historical_reconciliation.compare_historical` compares the complete source/donor
year union. It rejects duplicate keys, missing/mismatched amount lineage and
invalid numeric/temporal inputs. Each row preserves source/donor values,
coordinates, exact delta and a reason; resolution is `retain_both_observations`.
The JSON Schema validates those states. It neither edits the donor nor grants
approval to rewrite an existing compatibility export or publication.

The separately retained `silver/historical-reconciliation-20260830-v1` has
76 exact matches, 29 source-only annotated years and one numeric difference.
Its manifest SHA-256 is
`4847b9b50a08a1f8d2b42627fd496bb0dafe5a661b0d934db41db2d1dbca234e`.
Repeated comparison builds match byte for byte. The 1976 Health source token
is `605.70000000000005`, while the donor scalar text is `605.7`; both survive.
Donor comparison values use decimal conversion of SQLite Python scalar text,
not an assertion of SQLite binary-number lexical identity.

## Next integration boundary

Budget, forecasts and history together produce 341 source-derived facts versus
the donor's 312 rows: 29 recovered years and one explicitly retained precision
difference. The next workflow must combine these adapters through versioned
manifests, regenerate compatibility and analytical products with explicit repair
policy, and expose the operations through the archive interfaces. Remaining
workbook areas, official expansion and contextual measures are still pending.
