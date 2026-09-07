# P2.12 linked FOI factual cohort — review and delivery

## Outcome

Six previously evidenced links across five source identities are assessed:

| Source | Bounded finding | Remaining uncertainty |
| --- | --- | --- |
| AL 2026 | Register-labelled HTML with one table, 26 table-row elements, six recognized schema labels and six DOCX link occurrences | Rows include headers; no request denominator or attachment contents established |
| AL 2015–2025 | Register-labelled landing page, no table detected | Year-level inventories, linked contents and coverage remain unknown |
| GG | Linked FOI page timed out | Access and actual interface remain unverified |
| JM | Access-to-information information page; 15 PDF link occurrences | Links are not classified as requests/responses or downloaded |
| KY | FOI information page; one PDF link occurrence and publication navigation | No request/response inventory established |
| UM | DOI FOIA information page with FOIA-library and request navigation | Department-wide page, not proof of UM-specific records or country coverage |

Counts apply to structural occurrences in the bounded HTML, including possible
navigation/footer duplicates. They are not unique documents, request totals,
captured objects or inferred nonpersonal schema clearance. AL's recognized labels
are request date, request subject, response date, response, completion method and
fee (retained in normalized Albanian). No cell values, correspondent names,
attachment filenames or arbitrary link text are retained by the new parser.

## Transparent historical acquisition provenance

These observations were acquired **before** guard correction
`8272a2a0b493f90bb647347050b623a7291d2e5e`, at
2026-09-07 03:31:24.854772–03:31:36.679504 UTC. The original transport was from
`f8206f38fada690eff7d79469add77b658917223`; its exact bytes are already preserved
in `candidate-probe-acquisition-20260907.py.txt`. The new `metadata_get` wrapper
only extracted structural metadata in memory; it made no additional requests.
The paired [provenance receipt](linked-foi-provenance-20260907.json) binds the
immutable observation file bytes and canonical content to that history.

Twelve completed trace entries record 886,484 received response-body bytes.
Counters describe retained traces, not TLS/header wire traffic or unrecorded
partial traffic during a timeout. Collection used the earlier configured bounds:
eight workers, ten-second requests, forty-second sources, 1,500-second cohort,
one-million-byte pages, 65,536-byte robots and at most three redirects. The earlier
collector's pacing flaw remains documented by P2.13. **No historical transport
policy compliance is claimed**, even though the factual observations validate
under the corrected terminal/media guard. Bound settings are not certification.

No new network reads occurred during final review/delivery. No 223-source replay
occurred. Fresh reads are unnecessary to establish this dated factual assessment;
future authorized probes use the corrected collector. GG's timeout is not silently
replaced with successful homepage access from the earlier cohort.

## Implementation and validation

`foi_linked_assessment.py` derives exactly four retained FOI leads and two AL
year links, rejecting drift, duplicates and unsafe targets. Stable target IDs
retain parent source, discovery-page hash/date and discovery-receipt identity.
The optional observer reuses the existing corrected HTTP collector; there is no
second transport, discovered-link fan-out, API access or attachment acquisition.
The offline assessor reuses P2.13 terminal validation, validates structural
metadata even on failed/robots responses, and separates transport outcome from
interface finding. Unknown denominators stay null; rights, adapter qualification,
country completeness, schedules and publication are not promoted.

Paired `linked-foi-assessment.json` and `.md` reproduce deterministically. The
machine report carries the canonical observation-content digest and explicitly
states that factual assessment does not certify transport compliance. Raw HTML
bodies were hashed in memory, not retained as originals; structural assertions
cannot independently reconstruct or authenticate original page contents.

Red phase before initial implementation: focused collection failed with missing
`foi_linked_assessment` module, as expected. Final focused suite: **236 passed**;
new module **100% line and branch coverage**. Ruff, format, BasedPyright and
scoped track checks pass. Cases include exact-cohort/provenance drift, malformed
structural counts/labels, private targets, failure metadata leakage, forged GG
success, all three P2.13 guard regressions, historical preservation hashes,
unchanged publication fields and deterministic output. No full harness claimed.

Conductor implementation/review guidance informed acceptance-linked records,
negative-path checks and the explicit historical evidence boundary. Applicable
Python/general guides pass under the repository's Ruff/typing conventions; no
new dependency, platform guide or global registry change is needed.

## Integration and next action

Integrate this separate P2.12 commit after P2.13. Parent owns the full gate;
preserve its accepted P2.5–P2.8 statuses and rechain appended evidence against
the parent's advanced ledger. P2.2/P2.3 and the track remain in progress.

No external input is required to close this bounded factual cohort. Further
access qualification for GG requires a successful bounded public response from
`https://www.gov.gg/information`, not human factual-review approval. A later safe
slice could inspect AL's older year-index navigation or DOI's FOIA-library lead,
with separately retained linked URLs and corrected-policy observations. No
request/correspondence or attachment capture is inferred or authorized here.
The existing institutional licence/nonpersonal-schema and mixed-correspondence
metadata-only boundaries remain unchanged; no rights or publication decisions.
