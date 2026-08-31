# Pharmac medicines-budget HTML adapter

Local source-specific normalization, cold mutation and native assurance pass;
hosted delivery remains pending. No source capture, rights promotion or publication is
performed by this adapter.

## Exact retained source and scope

The census resource `pharmac_cpb-010` identifies the retained 548,867-byte HTML
object `eaf5801b819321f8aed7544fb16e6348779267fd3d5f8fb1d59410803acffbea`.
Its recorded observation is `2026-08-29T09:00:17Z`; this is reused provenance,
not a new capture attestation. The page displays last updated 7 August 2026.
The local profile is `Pharmac-CPB-2026-08-07`.

Full table characterization found one header plus fourteen descending years
2013/14–2026/27, not only the six-row preview. The header has four physical
cells, its final cell spanning two columns. Ten data rows use that same shape;
2013/14–2016/17 have five physical cells with an empty final cell. All 64 cells,
including headers and four padding cells, retain dispositions and colspan.
The two 2014/15 change fields contain literal `-`: both remain null with
`source_dash_not_supplied`, never inferred zero.

The source caption ends at 2025/26 although the table contains 2026/27. Both
the original caption and a discrepancy flag survive. Published absolute and
percentage changes are preserved, not recalculated or tested as exact ratios;
their differing published rounding is not repaired.

The page explicitly defines Pharmac's financial year as 1 July–30 June.
Dates therefore derive from the year token and this exact paragraph, with
both inputs represented in date-field lineage. A separate retained paragraph
describes the 1 July 2022 transfer from DHB budget holding to a Pharmac-held
National Pharmaceutical Purchasing Appropriation. The budget series does not
assert homogeneous policy coverage across that boundary. It is not actual
expenditure, a forecast-outcome claim, or a recomputed price-adjusted measure.

## Medallion and interface contract

`normalize_pharmac_budget` consumes an explicitly pinned original with a 1 MiB
cap, strict UTF-8 decoding, one exact table, bounded rows/cells and 512-character
cell payloads. It rejects ambiguous contexts, layout/colspan/rowspan drift,
unclosed structures, active table elements, missing values in the budget amount,
bad decimal syntax, symlinks and existing outputs before writing.

This is a library-only increment. Dry-run is read-only. Explicit writes reserve
a fresh directory and create `pharmaceutical_budget_facts.parquet` (14 facts),
`field_lineage.parquet` (186 entries), `cell_dispositions.parquet` (64 cells),
then a hash-pinning `MANIFEST.json`. Partial writes retain their files without
a completion manifest. Retry requires a new directory.

Table coordinates count physical cells, not visual colspan-expanded columns.
`html:outside-table-p=N` counts completed non-table paragraphs in document order.
Decoded text folds whitespace; the immutable HTML retains exact markup,
whitespace, links and all unselected page areas. Decimal conversion adds only
zero scale padding (maximum three supplied decimals), never numeric rounding.
Nulls remain null in lineage as well as facts. Original values and padding are
also retained in each fact's decoded `raw_values_json`.

Rights remain `not_evaluated`. The existing capture/census licence observation
is not inherited as new derivative publication approval. No Bronze object,
existing Silver/Gold package, candidate, Hugging Face revision or donor changes.

## Local evidence and bounded failures

- Synthetic tests first failed on the absent `pharmac` module (collection
  exit 2), then passed after implementation. Dependency setup initially hit an
  externally broken shared uv-cache link and disappeared old environment;
  recovery used a fresh clone and task-owned cache without changing shared state.
- An initial all-field lineage check caught decimal display scale mismatch;
  exact scale padding now makes emitted decimal and lineage representations
  agree without rounding any value.
- Independent review caught string `None` in missing-value lineage. The new
  regression failed before the correction and passes with schema null.
- Current focused suite: 69 tests, 100% of 145 statements and 48 branches,
  Ruff format/lint and basedpyright passed. One intermediate coverage command
  misspelled the dotted module path, reporting no data despite passing tests;
  the corrected module-scoped command passed the unchanged 100% threshold.
- Cold unfiltered mutation: 93/93 killed, zero survivors/timeouts/errors/pardons,
  zero cache hits, two workers, all 69 tests, 172.27 seconds. Report SHA-256:
  `4dacb57619169b44569225d3a09fa4aeff5db90527b40e0c41a408d79408cf79`.
- Unchanged native `./scripts/validate.sh` passed at `677326a`: 2,459 tests
  in 145.43 seconds, 97.01% overall coverage, eight existing cleanup warnings,
  and all typing, schema, differential, mutation and supply-chain gates.
  Durable native log SHA-256:
  `ea23b74dabb6a092e9d637eaa06d7bebddca959f01c703f2e519ba5cefb321f0`.
  Hosted exact-head checks remain a separate pending gate.

Two exclusive local pilot builds match byte-for-byte across four files totaling
31,646 bytes. Manifest SHA-256 is
`5eea323f1f9360fb7a92b7c2d9f92f1922dfb6f447a8252c8ca8b3ebf64ff248`.
An independent table parser reconciled every physical cell and all 42
numeric/missing inputs against facts and amount lineage. The script digest is
`5b2df7fa2a0702bd430e53f8cdff1de95d2d137ecb6460d8b12da180cf546db8`;
source hash readback remained unchanged. These packages have not been published.
An exclusive archive copy at
`silver/raw-pharmac-cpb-20260831-v1` was verified byte-identical across all four
files after native assurance. Both temporary pilot copies remain retained;
no existing package or original was replaced.

## Prior embedded-notice hosted delivery

Parent verification observed PR #285 merged externally at
`2026-08-31T12:56:03Z`, exact head
`4563009ac6de12c3ea052ba68a65316ff6142ea2`, merge
`5ff01ff908f9d27f4c9349b112e66b94cd244dea`, with all seven checks successful
and CI run `33393458051` completed successfully. No merge call was issued by
this implementation agent. Earlier local native timing failure evidence stays
intact; hosted delivery grants no source eligibility or publication approval.
