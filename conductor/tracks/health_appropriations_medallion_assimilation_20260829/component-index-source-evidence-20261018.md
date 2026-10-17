# Retained health component-index source evidence

Refs #207, #208, #209 and #211. This qualifies a fixed source-census cohort;
it does not select a health-spending deflator or admit analytical joins.

| Export | Exact selection | Represented quarters | Numeric | Publisher missing |
| --- | --- | --- | --- | --- |
| LCI025AA / LCI358301.px | Labour Cost 3; Observations LCI025AC; Central Government, Health Care and Social Assistance, All Salary and Wage Rates | 1992Q4–2026Q2 (135) | 69, from 2009Q2 | 66 literal `..` |
| PPI021AA / PPI387801.px | Observations PPI021CC; Inputs, ANZSIC06, NZSIOC level 3, Health Care and Social Assistance | 1994Q2–2026Q2 (129) | 120, from 1996Q3 | 9 literal `..` |

LCI uses the source's June 2009 index reference; PPI uses December 2010.
PPI's footnote about a December 2013 reference applies to the named agricultural
industries, not this health-and-social-assistance selection. The PPI industry
selection is not restricted to Central Government. Both include Social Assistance.

The original TQX files contain publisher-generated selections, not observations.
They request `ShowNonFinalFlags`. Absence of a flag is retained as
`unflagged_unknown`, never upgraded to FINAL. PPI's native decimal strings are
preserved despite its display configuration requesting zero decimals.

Original CSVs came from publisher-generated download-frame URLs. Fresh bounded
unauthenticated captures through existing `capture_url` matched both browser
exports exactly; existing WARC response binding verified the actual captures.
These timestamped download locators identify retained observations and are not
promised as durable endpoints. No browser credentials were transferred.

The six body/response pairs include both CSVs, Infoshare ownership, LCI method
version 66, PPI method version 3, and the previously retained Stats NZ copyright
page. Two separately pinned TQX files bring the preserved cohort to 14 objects.
The copyright default and specific-statement exceptions are observed together
with resource ownership. Rights adjudication and public-release authority remain
separate. General method versions do not qualify every historical break,
reweighting or current-vintage comparability question.

`component_index_evidence.inspect_component_source_evidence(cas_root)` is an
offline, read-only entry point. `cas_root` contains all 14 originals as
`<sha256[:2]>/<sha256>`. It checks exact snapshot pins and WARC response binding
before checking headers, footers, query selections, periods, missing positions
and decimal literals. `encode_evidence` provides deterministic JSON without
local paths or a clock. It does not write Silver/Gold products or infer LCIQ/PPIQ
identifiers, currency, annual alignment, component weights or a cost basket.

The actual-source proof runs in two isolated CAS copies with network access
denied and compares the report bytes while checking the inputs remain unchanged.
Its report SHA256 is
`fccc38505c0983ff60c12371e714f4233e54c84efa7c52b0b04e7d31c62fe8e4`.
The first proof's embedded-JSON link parsing failure is retained separately;
the corrected proof decodes publisher Content and checks the parsed anchor.


The original machine-style PPI method summary triggered an entropy-scanner false
positive when its report entered Git. Three summaries now use readable prose;
no scanner policy or baseline changed. Native3 regenerated this report and
verified every other report value and all 14 input objects are unchanged. The
previous canonical report and failed scan remain retained as historical evidence.
The earlier full harness qualifies its recorded executable head; a new full run
must qualify the corrected producer before PR creation.
