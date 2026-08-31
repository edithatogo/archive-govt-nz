# Preserved fiscal 1972–2025 successor pilot

The existing source-faithful historical adapter supports the inspected 2025
workbook without a production change. This is a bounded local pilot, not full
workbook normalization, a published replacement or approval to splice editions.

## Exact source and context

- Official captured source: `fiscal_time_series-007`, 116,265 bytes, SHA-256
  `de59f9028a81a697ee66eea04861edfd8e2c3a7e472b3b8798d976951964f70f`.
- Locator: https://budget.govt.nz/budget/excel/fiscal-time-series/fiscaltimeseries1972-2025-year-end25.xlsx
- Source vintage: `Fiscal-Time-Series-1972-2025`; local observation context
  `2026-08-31T12:26:32Z`, not a claim about the original HTTP capture time.
- Eight visible sheets; inventory reports no macros or external links in this
  edition. The older fiscal source's metadata concern remains separate.
- Exact labels: Spending A3 `$ millions`, H4 `Health`; Nominal GDP A3
  `$ millions`, C3 `Nominal GDP`. Both selected year ranges are 1972–2025.
- Health retains accounting/period transitions at 1990, 1994, 1997 and 2005;
  GDP retains its March-to-June transition at 1990. All 29 annotated historical
  Health year labels remain represented. No cross-transition growth is inferred.

## Reproducibility and revision evidence

Two independent temporary builds and one exclusive retained build match all
four files byte-for-byte. The retained package is
`silver/raw-historical-2025-20260831-v1` under the external health archive;
manifest SHA-256
`aee4578f1ee83f8c1ede63e36e840c6cd2140df8c6f463e71ec93da9e4e7d75a`.
It contains 108 facts, 1,164 field-lineage rows, 1,531 cell dispositions and
zero selected rejections: four files, 220,812 bytes including the manifest.

An independent literal OOXML readback resolves all 1,164 lineage coordinates,
checks 216 amount/token references and all 108 year labels against the actual
source cells. Original SHA-256 is unchanged. A preliminary diagnostic used a
nonexistent fact coordinate field; it was corrected to use the actual lineage
table before the independent checks. No failed check was treated as a pass.

Compared with the retained 2024 historical facts, shared-year Health amounts
are unchanged. GDP amounts for 2017–2024 are revised, and both measures gain
2025. The 2024 package remains intact: no overwrite, silent backfill, Gold
rebuild or revised GDP-share publication occurred. This revision evidence is
why source vintage must remain part of every analytical join.

Rights remain `not_evaluated` on these derivatives. The four-package additive
inventory scope does not automatically include this new fifth source package.
Publication, additional measures and complete annual-edition coverage remain
separate work.

The existing historical, numeric and reconciliation suites pass all 65 focused
tests; Conductor validates 70 tracks. No production code was modified for this
pilot. Broader delivery assurance remains separately recorded by the containing
source-pilot PR.
