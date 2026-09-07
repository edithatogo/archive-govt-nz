# Donor PDF: bounded structural/text/layout qualification

Date: 2026-09-07. Independent evidence-only worktree based on G
`df7bbd4debdce6986c7331afe30e11d86f294d35`. No production, dependency, shared
plan, source-register, publication or rights changes. **Zero qualified numerical
facts.** This qualifies the next extraction prerequisite, not an extractor.

## Source and parser evidence

Exact retained original, never copied or rewritten:
`/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas/sha256/62/620ff6a34e7be955ce70316af8f6fa4a9ca95689fa5036e076b50c13431d1fa8`.

SHA-256 before/after:
`620ff6a34e7be955ce70316af8f6fa4a9ca95689fa5036e076b50c13431d1fa8`;
byte count **1,339,480**. Donor manifest remains
`/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/manifests/donor-4668e6c.json`.
The donor filename `appropriation-main-estimates-2024-25.pdf` conflicts with
the 2003 Supplementary Estimates cover; see `donor-pdf-identity-proof.md`.
No identity or period is derived from that filename.

Available installed Poppler tools `pdfinfo`, `pdftotext`, `pdftoppm` are all
**26.09.0**. `pdfinfo` reports **471 parsed pages**, PDF 1.4, unencrypted,
untagged, no form and no JavaScript. This uses a PDF parser's document/page-tree
view, not the repository's lexical `/Type /Page` marker regex. The previous
471-marker count is corroborated, not re-labelled as a separate parser test.
No second independent parser was used; pypdf/pikepdf/fitz were unavailable in
the repository environment and none was installed. This is not a comprehensive
PDF conformance or security certification.

`pdfinfo -f 253 -l 268 -box` successfully resolved all **16 physical pages**.
Each has MediaBox/CropBox `[0,0,842,595]` points, landscape A4, rotation 0;
BleedBox/TrimBox/ArtBox reported the same bounds. Printed labels are B.7
235-250 respectively. Physical page ordinals are one-based; rendered filename
253 means physical page 253, not printed page 253 or a zero-based index.

## Visual and text inspection actually performed

Rendered every physical page 253-268 using `pdftoppm -scale-to 1300 -png` and
inspected all 16 images. Table borders, grouped headings, row labels and signs
were legible at this scale; no visible clipping prevented this layout audit.
This is not a cell-by-cell numerical transcription or acceptance assertion.
Text was extracted separately per page with `pdftotext -layout`. The companion
JSON receipt records each text byte count/SHA-256 and each inspected render
SHA-256, plus the exact header carry-forward map. Render/text products are
local temporary derivatives, not committed source payloads.

| Physical / printed pages | Observed rows/structure | Header treatment |
| --- | --- | --- |
| 253 / 235 | D1-D3; Departmental Output Classes, Mode B Gross | Full B1 header |
| 254 / 236 | D4-D6; Mode B Gross continuation | Full B1 header |
| 255 / 237 | D7-D10 and departmental gross subtotal | No column header; carry from 254 |
| 256 / 238 | D11, departmental net subtotal, then O1 | Full B1 header; Mode B Net then Non-Departmental Output Classes |
| 257 / 239 | O2-O6 | No column header; carry from 256 |
| 258 / 240 | O7-O9 | Full B1 header |
| 259 / 241 | O10-O14 | No column header; carry from 258 |
| 260 / 242 | O15-O17 | Full B1 header |
| 261 / 243 | O18-O22 | No column header; carry from 260 |
| 262 / 244 | O23-O24 | Full B1 header |
| 263 / 245 | O25, O26, O28-O30 and non-departmental subtotal | No column header; carry from 262; do not invent O27 |
| 264 / 246 | Other Crown expenses, subtotal, departmental capital contribution and subtotal | Full B1 header; multiple section transitions |
| 265 / 247 | Capital Contributions to Other Persons or Organisations | No column header; carry from 264 but adopt this page's new section label |
| 266 / 248 | Health Sector Projects, capital subsection subtotal, Total Appropriations | Full B1 header |
| 267 / 249 | Part F/F1 Current Revenue / Non-Tax Revenue, ACC rows | New F1 three-column header; reset B1 state |
| 268 / 250 | Current Revenue continuation, subtotals, Capital Receipts, overall total | Full F1 header; section transitions |

### B1: physical 253-266

The table's 2002/03 period heads three groups, each with two separate columns:

| Group | First column | Second column |
| --- | --- | --- |
| Main Estimates | Annual, $000 | Other, $000 |
| Supplementary Estimates | Annual, $000 | Other, $000 |
| Cumulative Vote | Annual, $000 | Other, $000 |

The six numeric columns lie between the left appropriation label and a wide
right-hand explanation column. Values in prose (often $million amounts for
other years) are not table amounts. D11 on page 256 visibly has non-dash Other
values in all three groups: a six-column profile cannot discard Other as an
empty default. Gross/net classifications are explicit source headings and
cannot be merged by arithmetic or inferred equivalence.

Examples checked visually for token semantics, not numerical fact admission:
D1 page 253 has a parenthesized Supplementary Annual value; D11 page 256 has
positive Other values; page 265 contains both dash-led new appropriations and
parenthesized reductions. A dash also appears where a cumulative amount has
been extinguished. Preserve the dash token as distinct from a numeric zero,
missing extraction and absent cell; its eventual numeric interpretation needs
a source-backed policy. Bold styling alone is not a sign or row-type rule.

### F1: physical 267-268

The 2002/03 header has **three** numeric columns, all $000:
Main Estimates / Supplementary Estimates / Total Budgeted.
There is **no Annual/Other subdivision**. These are Crown revenue/receipts,
not expenditure; they must not be netted against B1. Parenthesized values occur
in Main, Supplementary and Total columns (e.g. Net Surplus from DHBs on 268).
Keep Current Revenue, Non-Tax Revenue, Capital Receipts and their subtotal/total
rows separately identified; identical printed totals are not duplicate errors.

## Concrete requirements before extraction acceptance

1. Pin source SHA and observed 2003 identity. Limit this profile to physical
   253-268 and require expected boxes, period, section and column anchors.
   Reject drift; no global regex-based extraction from the donor filename.
2. Use two explicit layouts: B1 six columns and F1 three. Validate coordinate
   bands against rendered headings/rulings before implementing extraction;
   this receipt does not supply unmeasured bounding-box coordinates.
3. Attach lineage to physical page, printed label, row/section, numeric cell
   bounds and originating header page/bounds. Implement only the six observed
   B1 carry-forward edges in the JSON receipt; no carry from B1 into F1.
4. Preserve section state and wrapped labels across continuation pages. These
   images establish table continuation, not a general rule that arbitrary
   row fragments can be joined. Any split-row join needs matched geometry and
   explicit evidence. Never manufacture missing sequential codes such as O27.
5. Preserve raw number lexemes, thousands separators, parentheses and dash
   tokens. Negative parsing must be tested in every estimate group. No silent
   dash-to-zero coercion, sign repair, number inference or totals arithmetic.
6. Separate detail, section headings, subtotal and total rows before counting
   observations. Do not count repeated D11/subtotal amounts as a single row or
   add components and totals together. Do not net capital/revenue/spending.
7. Preserve explanations/notes as linked text, not additional amounts. Text
   fidelity needs attention: rendered `Maori` with macron appears as `MƗori`
   in Poppler text on 253/254/264. Retain original text/render lineage and
   flag decoding differences; no silent spelling/Unicode repair.
8. Acceptance must compare extracted cells and dispositions against the
   render, account for every selected row/cell including failures and nonnumeric
   tokens, and prove source unchanged. No complete-row or amount count is
   asserted here. Formula-cache inference is irrelevant to this PDF slice.

## Reproduction and disposition

Read-only commands (replace `<source>` with the exact CAS path above):

```text
pdfinfo -v
pdftotext -v
pdftoppm -v
shasum -a 256 <source>
pdfinfo -f 253 -l 268 -box <source>
pdftoppm -f 253 -l 268 -scale-to 1300 -png <source> <temporary>/page
pdftotext -f <physical-page> -l <physical-page> -layout <source> -
shasum -a 256 <source>
```

All commands completed successfully. JSON receipt validation checked the
contiguous 16-page range, printed mapping, header-source map, digest syntax,
zero fact count and unchanged source hash. No test suite/full harness was run
for these two evidence files. Render hashes are environment/tool-version-bound
observations, not a promise of cross-version image determinism.

Proposed parent disposition: **Parsed 471-page count and selected 253-268
structural/text/layout qualification complete; bounded extraction profile
requirements documented. PDF numerical extraction/admission remains pending,
with zero qualified facts.** The PDF skill led to actual visual inspection of
every selected page and separation of text availability from table acceptance.
