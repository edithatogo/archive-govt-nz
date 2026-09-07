# Population context: definition enumeration completed

The selected national resident-population definitions are now enumerated.
This supersedes the earlier population *definition/base* gap in context-census;
it does not claim that a numerical CSV/XLS response has been verified.

## Exact official selections

| Field | Observed metadata |
| --- | --- |
| Table | DPE054AA — Estimated Resident Population by Age and Sex (1991+) (Qrtly-Mar/Jun/Sep/Dec) |
| Definition | New Zealand usually resident population, all ages and sexes; includes temporarily absent residents and net census undercount, excludes overseas visitors |
| Population / age keys | C = Total; DPE054FF = Total All Ages |
| Estimate keys | 1 = As at; 2 = Mean year ended |
| Frequency / reference | Quarterly reference dates; selected 2026Q2 / 30 June 2026 |
| Unit | Persons; no thousands multiplier |
| Vintage / basis | Release 18 August 2026, 10:45am; current basis 30 June 2023 |
| Selectable time coverage | 1991Q1–2026Q2 (142 options); not a numerical completeness assertion |
| Legacy identifier search | Exact DPEQ.SG1CTOT resolves; DPEQ.SG*CTOT returns DPEQ.SG1CTOT and DPEQ.SG2CTOT |

The [release](https://www.stats.govt.nz/information-releases/national-population-estimates-at-30-june-2026/)
establishes current base/vintage and distinguishes stocks from published means.
[DataInfo+](https://datainfoplus.stats.govt.nz/Item/nz.govt.stats/4c9f3523-5386-4ce0-a8bd-993bb905f119)
supplies the resident-population concept and unit meaning. Quarter-end stocks
and rolling year means are distinct; “quarterly” does not make the latter a
quarterly mean. The current release is provisional and revises prior quarters.

The authoritative machine selection here is the publisher table plus explicit
dimension codes. Legacy identifier membership was verified, but this slice
does not infer a one-to-one label mapping from the spelling/order of SG1/SG2.

## Endpoint verification

- [Infoshare Search](https://infoshare.stats.govt.nz/SearchPage.aspx):
  identifier search and variable metadata verified through read-only search
  form operations.
- [Export direct](https://infoshare.stats.govt.nz/ExportDirect.aspx):
  stable reachable form; [official instructions](https://infoshare.stats.govt.nz/Help/export-direct.asp)
  document search-file inputs and CSV descriptions/status flags. No numeric
  export response requested.
- [Query upload](https://infoshare.stats.govt.nz/QueryUpload.aspx):
  stable navigation target observed; this upload route was not exercised.
- SelectVariables.aspx: generated session-specific pxID, not a stable URL.
  Its Table Query (.tqx) operation returned HTTP 200, text/plain, 798 bytes.
  The response contained selection metadata only. SHA-256 and exact selected
  codes are in population-context.json.

The query requested both estimate types, Total, Total All Ages and 2026Q2.
An earlier query selected 1991Q1 because option value 0 differs from visual
ordering; a corrected label-to-option lookup produced verified 2026Q2 metadata.
No numeric data, cookies, session tokens or query payload were committed.

## Subsequent analytical work, separate from enumeration

M-12 requires exact denominator/base/vintage. Design lines 331–342 require
explicit temporal alignment and prohibit silent vintage splicing, but do not
choose an annual spending denominator. The precise remaining analytical choice
is **published Mean year ended at the spending-year endpoint versus As at that
endpoint**. Use the actual spending period: historical March/June transitions
cannot be joined merely on the year label. No interpolation or selection was
implemented. Choosing a method belongs to the subsequent Gold contract, not
this source-enumeration checkpoint.

A capture worker can separately verify numeric export, statuses, fixity and
resource rights. The endpoint is an observed export *workflow*, not a
verified static CSV URL or frozen numerical release.

## Validation and parent clause

TDD began with the missing-module import failure. Final focused suite: 18
passed, 100% of 53 statements and four branches. Format, Ruff and Pyright pass.
The first coverage run exposed an untested identifier-rejection branch
(94.74%); its regression now passes. No full harness or mutation run was made.

Self-review: profile consistency rejects population/age swaps, estimate-label
swaps, date/base/vintage drift, session URLs as stable entry points, and
HTML/HTTP-status-only export claims. This is an offline receipt validator,
not independent authentication of a live server response.

Proposed parent clause:

> Population source-definition enumeration completed: exact national/all-age
> DPE054AA selectors, quarterly reference periods, 2023 base, August-2026
> vintage, and metadata-only query export verified. Numeric export/capture
> qualification and the annual-spending denominator policy remain separate
> downstream tasks. Do not describe the entire context census as blocked.

Only new population-context source/tests/receipts were added. Previous census
records and shared plan/runlog/metadata remain untouched. Commit this slice
after its census parent; the module reuses the existing strict receipt base.
