# Health source-context census — 2026-09-07

This metadata-only census covers the entire Phase 1.2 context-series task:
CPI, QES wages, national population, Stats NZ/Treasury GDP, and distinct
core/total Crown expenses. Ten definition/vintage/disposition rows are in
[context-census.json](context-census.json). All remain unqualified for
analytical admission; the register is not a promotion or rights decision.

## Evidence and findings

The register pins 12 existing adapter/receipt files plus the new
[retained-byte observation](context-census.observation.json). Source references
join exact IDs, URLs, original hashes and observation times to the retained
source census. Previous receipt claims remain historical; this slice freshly
verified three Crown original hashes and four retained manifest byte hashes.
It did not revalidate every derivative member or historical rights claim.

| Context | Exact retained definition/selection | Qualification still missing |
| --- | --- | --- |
| CPI | CPIQ.SE9A, all-groups New Zealand, June-2026 vintage | Source-bound index base and fiscal average/rebase policy |
| QES | QEMQ.SASZ9A, Table 8 total-sector ordinary-time hourly earnings, nine quarters | Currency/sex/adjustment, deflator selection and annual weighting |
| Population | DPEQ.SG1CTOT is a prior metadata lead; retained HLFS workbook rejected | Exact national all-age resident export, census base, coverage and annual mean |
| Stats NZ GDP | SNEQ / SG03AB01GE00S900, Table 1 C27:BJ27, March-2026 vintage | Currency, annual aggregation and semantic projection |
| Treasury GDP | Fiscal-2025 Nominal GDP sheet, C3 label, B/C year/value columns | Preserve period transitions and revision vintage in derived joins |
| Core Crown | Fiscal-2025 Spending D27:D58, 1994–2025 | Canonical adapter and accounting/consolidation comparability |
| Total Crown | Fiscal-2025 Spending E30:E58, 1997–2025 | Canonical adapter, restatement footnotes and consolidation comparability |
| Forecast core Crown | BEFU-2026 F26:O26 / HYEFU-2025 F25:O25 | Formula/cache qualification and financial-year basis |

The newly inspected Crown ranges are enumeration evidence, not implemented
adapters. Fiscal blank cells before 1994/1997 are not zeros; Financial Net
Expenditure and percent-GDP blocks cannot substitute for expense levels.
BEFU/HYEFU totals contain formulas. No formulas were evaluated or caches
qualified. Both releases label 2021–2025 Actual and 2026–2030 Forecast.

Population metadata comes from the already recorded
[Stats NZ concept](https://datainfoplus.stats.govt.nz/Item/nz.govt.stats/5c91579c-9077-4553-ae9a-1e04e6bce0e7)
and [RBNZ M12 metadata](https://www.rbnz.govt.nz/statistics/series/economic-indicators/population-and-migration)
observation in source-schema-gaps.md. No new RBNZ or other network request was
made. These prior links do not establish current access or a captured export.

## Validation and review

TDD red: the initial focused test failed on the absent source_context_census
module. Green: 19 tests passed. A second red regression demonstrated that a
forged retained-manifest digest was accepted; the implementation now requires
that digest in a cited, hash-verified receipt. Final focused suite: 22 passed,
100% of 83 statements and 22 branches. Ruff format/check and Pyright passed.
Exact commands and outcomes are in context-census.validation.json.

Conductor review covered the new source, tests and all dedicated receipts
against M-02/M-12 and the source-derived analytical boundary. The review
resolved the initial overly broad Crown selector gaps by inspecting retained
bytes, and added the retained-manifest regression. No outstanding actionable
finding in this bounded slice. The validator checks structural/evidence
consistency; it cannot independently prove prose semantics, rights or source
authenticity. Existing pinned evidence changes require deliberate re-audit.

No shared plan/runlog/metadata, Bronze fixture, dependency or remote was
changed. No new raw data was captured, promoted or published. Full harness,
mutation/programme assurance and archival remain with the parent as delegated.

## Proposed parent status clause

Keep the existing Phase 1.2 task in progress:

> [~] Enumerate the exact official CPI, QES wage, population, GDP and Crown
> expense series needed for approved derived measures; reject discovery leads
> that lack a stable definition or join. [M-02, M-12; AC-03, AC-10]
> Context-family census and retained Crown selector enumeration are recorded
> in context-census.json and context-census.observation.json. Population export,
> CPI base, wage qualification and denominator joins remain explicitly
> unqualified; no analytical admission or source promotion is claimed.

Rationale: the full requested family inventory is now explicit and validated,
but the exact population export and stable analytical joins required by the
existing clause are not established. An [x] would overstate that clause.
Do not split this into additional partial micro-tasks. Parent integration must
run the combined harness and reconcile the shared records.
