# Typed workbook inspection

`archive-govt-nz health-appropriations-inspect-workbook` replaces the donor's
print-only worksheet listing and sheet-head functions. It inspects one capped,
hash-verified snapshot and emits structured JSON without writing original or
derived files. Unknown sheets, bad packages, hash mismatches and exceeded limits
produce redacted structured failures, not a false completion message.

## Bounds and interpretation

- Maximum original snapshot: 64 MiB, followed by the existing workbook package
  and traversal checks. This is not a process-isolated parser sandbox.
- Previews allow 0–20 rows and 1–50 columns. Zero rows means listing only.
  Default heads contain five rows and twelve columns per worksheet.
- Across selected worksheets: at most 2,000 preview cells and 128 KiB of
  UTF-8 encoded preview values. These are preview limits; the structural
  inventory remains subject to its existing package/traversal bounds.
- Values are decoded displays, explicitly not canonical financial facts.
  Source hashes and cell coordinates link back to unchanged originals.
- Literal formulas remain formula text. Array and data-table formula objects
  retain decoded attributes/text rather than memory-address representations.
  Nothing is evaluated; cached-value freshness remains unverified.
- Temporal displays are stable. Unsupported object types and nonfinite decoded
  numeric previews fail closed. Listing mode does not serialize cell values.
- The inspection schema validates the envelope/preview contract and the nested
  inventory identity. Existing inventory tests govern its richer structural
  fields; this is not a new full workbook-normalization schema.

## Examples

```sh
uv run --locked archive-govt-nz health-appropriations-inspect-workbook \
  --source "$HEALTH_ARCHIVE_ROOT/bronze-cas/sha256/d6/d67c01b0a3f1fbee5cb5121b641bda42f91f3e5bc84e599d22d32aeacbbb3338" \
  --expected-sha256 d67c01b0a3f1fbee5cb5121b641bda42f91f3e5bc84e599d22d32aeacbbb3338 \
  --rows 0
```

For a bounded head, use `--sheet 'Raw Data' --rows 2 --columns 17` instead.
The live original Budget workbook lists eight sheets and returns 34 cells for
that head; its SHA-256 was rechecked unchanged. Inspection neither creates
Silver facts nor updates Gold/HF data or resolves source rights.
