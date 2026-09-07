# Population numeric-export response contract

The official CSV response now passes a bounded, deterministic admission
contract for both population measures across all 142 selectable quarters,
1991Q1–2026Q2. The response contains 284 measure/period cells, including three
published missing tokens. Enumeration and numeric response verification are
complete for this selected profile. Immutable HTTP/original persistence remains
with the separate capture worker.

## Contract and verified profile

`population_export.inspect_export` consumes exact bytes, the existing
PopulationContext, an explicit requested-period tuple, and ExportTransport
(status, media type, expected SHA-256). It performs no networking or writes.

It requires the exact table title and two distinct columns (As at / Mean year
ended), Total population, Total All Ages, unit magnitude Units, DPE054AA,
the August-2026 update footer and 2023-base note. Identity includes source
hash, table, release, period, estimate code, population and age keys.
Source row/column, original value spelling, reference date and measure kind
are retained. No annual averaging, resampling, interpolation or financial-year
join occurs. Current release basis is source context, not a claim that every
historical observation originally used the 2023 census.

The accepted profile explicitly has **status flags not displayed**. Status
remains null; missing `..` becomes null with figure_not_available, never zero.
Flagged or different CSV layouts require separate reviewed profiles. An attempt
to navigate export options returned the site's fatal_error redirect, so no
status-option success is claimed. The unflagged response is still faithfully
verifiable and remains analytically unselected.

Bounds: 65,536 bytes, 200 physical lines, 2,048 characters per line, at most
142 distinct requested quarters. Malformed encoding/CSV, altered transport,
hash mismatch, header/unit/base/vintage drift, duplicate/extra/missing periods,
unrecognized numbers and contradictory required footer markers fail closed.
Unsigned integer tokens are preserved exactly; negative, fractional and
embedded-status spellings are rejected in this bounded profile.

## Official verification

The existing [Infoshare search](https://infoshare.stats.govt.nz/SearchPage.aspx)
workflow resolves DPEQ.SG1CTOT, then selects both estimate types and the
Total/Total All Ages dimensions. CSV export was verified from the resulting
session-specific selection form. There is no asserted static CSV URL.

| Request | Bytes | Result |
| --- | --- | --- |
| 2026Q2, both measures | 1,162 | Two cells; expected metadata and source-column identities |
| 1991Q1–2026Q2, both measures | 4,819 | 284 cells; three missing values; all 142 requested periods |

The second verification used a streaming 65,536-byte response limit and the
production validator. Exact digests, observations and test commands are in
population-export.validation.json. Network/session state and population amounts
are absent from Git; synthetic tests use invented small integer examples.
No HTTP bytes were durably persisted by this slice. A matching response hash
is not a WARC receipt, CAS insertion or redistribution approval.

## Approved temporal contracts and remaining choice

Reinspection of M-06 (requirements.md lines 49–54), M-12 (lines 99–105),
AC-10 (spec.md lines 258–260) and design.md lines 331–342 found requirements
to preserve financial-period meaning, population definition, source vintage
and temporal alignment. None selects annual mean versus endpoint stock.

Only at the analytical stage, the unresolved choice is:
**Should annual health spending per capita use the publisher's Mean year
ended for the matching financial-year endpoint, or its As at population at
that endpoint?** No choice is needed to acquire and preserve both series.
Historical March/June fiscal boundaries and missing means must remain explicit;
neither interpolation nor a silent replacement denominator is approved.

The [Stats NZ release](https://www.stats.govt.nz/information-releases/national-population-estimates-at-30-june-2026/)
distinguishes these stock and period-mean concepts. This is source-method
context, not a repository decision selecting a spending denominator.

## TDD, review and parent handoff

Initial collection failed because the module did not exist. A malformed-CSV
test then exposed an unnormalized csv.Error; it now raises the dedicated
PopulationExportError. Final focused population export/context suites:
47 passed (29 export, 18 context), 100% of the export module's 85 statements
and 14 branches. Ruff, formatting and Pyright pass. Full harness and mutation
lanes were not run.

Self-review confirmed disjoint source/test/receipt files, no shared plan edits,
no transport-worker implementation, no payloads in Git, and explicit separation
of response verification, durable capture, source rights and Gold policy.

Proposed parent clause:

> Population numeric-export response contract verified for both source measures
> over all 142 selectable quarters (284 cells; three missing). Preserve both
> identities and undisplayed-status uncertainty. Durable capture/HTTP provenance
> remains capture-owner work; denominator choice belongs to the subsequent
> analytical stage and does not block source acquisition.
