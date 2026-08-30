# Raw Budget expenditure adapter

`tools/build_health_budget.py` is a separate Bronze-to-Silver path. It reads
the original workbook, not `health_funding_nz.sqlite`. The donor database
remains an independent parity oracle; existing Silver/Gold and the published
candidate are not replaced or updated by this command.

## Local execution

Resolve the preserved Budget 2025 workbook's CAS path from the donor manifest,
or use an intact donor checkout. Pass its expected digest, original relative
locator, explicit vintage and timezone-aware observation time:

```sh
uv run --locked python tools/build_health_budget.py \
  --source /path/to/preserved/b25-expenditure-data.xlsx \
  --expected-sha256 d67c01b0a3f1fbee5cb5121b641bda42f91f3e5bc84e599d22d32aeacbbb3338 \
  --source-locator data/raw/b25-expenditure-data.xlsx \
  --source-vintage Budget-2025 \
  --observed-at 2026-08-30T00:00:00Z \
  --output-dir /path/to/new/silver-budget
```

The source argument also accepts extensionless CAS objects. The command reads
one bounded snapshot, verifies its SHA-256, inventories the workbook and extracts
only the exact `Raw Data` sheet. Required columns are selected by name, not
position; original extra columns remain in row JSON and field lineage.

The example time is a fixed reproducibility-test context, not an attestation
that capture occurred at midnight. For operational builds, supply the verified
source observation time from the acquisition evidence. The local verification
build retained under `silver/raw-budget-d26e769` uses that fixed test context;
it is a validation derivative, not a replacement acquisition receipt.

Outputs are `budget_facts.parquet`, `field_lineage.parquet`,
`row_dispositions.parquet` and `MANIFEST.json`. Every rectangular input row
after the header has one disposition: normalized, non-Health out of scope,
blank or rejected. Other worksheets have explicit exclusions and retain their
full original bytes and structural inventory; they are not silently declared
normalized. Source coordinates use the original worksheet/cell addresses.

## Fail-closed boundaries

- A passed extraction exits zero; partial or empty results exit two. Invalid
  packages/layouts, context, hashes, output collisions and I/O failures exit
  nonzero. Do not treat output-directory existence as completion.
- Output directories must be new. The completion manifest is written last;
  interrupted/failed writes can leave partial files. Do not reuse that directory
  or ingest it without a valid manifest and matching hashes. There is no claim
  of an atomic directory transaction, automatic cleanup or resumable writes.
- Formula and spreadsheet-error Health rows are rejected. No formulas are
  evaluated and no external workbook content is fetched. Zero/negative amounts
  are retained; amounts must fit decimal128(20,3) exactly, without rounding.
- Year must be integral in 1–9999. It remains a source year label: the adapter
  does not infer whether it denotes a fiscal year beginning or ending then.
  `valid_time_start` is null and the uncertainty is a quality flag.
- This adapter does not infer source redistribution rights. Records and the
  receipt remain `not_evaluated` until separately joined to approved rights
  evidence. Successful parsing cannot promote a publication candidate.
- Preserve the original object and donor snapshot. No existing SQLite, Gold,
  Hugging Face revision or collection member is changed.

## Next raw-source work

The Budget adapter targets 215 of the 312 donor-table rows. The remaining
97 rows require independent historical health/GDP and BEFU/HYEFU expense
adapters, with named semantic ranges, explicit units/vintages, formula-cache
policy, raw-cell lineage and row-by-row reconciliation. The preserved PDF and
expanded official corpus need their own extraction/disposition contracts.
Raw extraction of one workbook does not complete the assimilation track.
