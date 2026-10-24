# Budget 2007–2019 legacy workbook definition census

This bounded census reconciles 32 already-preserved BIFF8 resources: 26 annual expenditure/revenue workbooks and six separately identified departmental forecast-statement variants. It verifies complete Explanation-sheet observations and complete raw header rows against pinned native outputs, source CAS objects and the existing WARC capture crosswalk. It does not recapture sources or change their originals.

The machine receipt records source identity, locator edition, declared June-year periods and qualifiers, layout, definition coordinates and text digests, amount-scale observations, rights status and explicit gaps. Complete decoded observations remain in the pinned evidence outside Git. Earlier discovery, capture and qualification checkpoints remain unchanged; this addendum records later observations separately.

## Findings and dispositions

| Evidence | Result | Disposition |
| --- | --- | --- |
| Explanation coverage | Every cell in all 32 retained sheet extents observed twice | Metadata census qualified; formula origin and numeric meaning not admitted |
| Raw headers | All 32 complete header rows observed twice | Layout observations retained without inferring field meanings |
| Period descriptions | All 32 describe June-year actual, estimated-actual and prospective periods | Preserve declared years and qualifiers; no start dates or analytical alignment inferred |
| Amount scale | 23 sources explicitly state thousands of dollars | Retain source-native scale; ISO currency and derived measures remain unqualified |
| Unit gaps | Six annual 2007–2009 expenditure/revenue workbooks and three departmental variants from 2008–2010 | Complete Explanation sheets and amount headers supply no scale; keep pending for further source evidence |
| Edition conflict | Budget 2014 revenue locator, Explanation B10 says Budget 2015 while its period sentence describes 2010–2015 | Preserve both observations; no silent correction or approved edition binding |
| Rights | No rights keyword candidate in inspected Explanation sheets | Rights remain not evaluated; no whole-workbook or publisher-policy absence claim |
| BIFF numeric values | Existing reader exposes decoded stored or cached values | No numeric promotion until a separate record/formula evidence contract is qualified |

The nine pending headers use the literal label `Amount`; the `Unit` column in some older layouts does not establish an amount scale. Source/CAS/WARC fixity, read-only repeats, cell coverage, native process termination and the independent validation lease were checked. Runtime code, schemas, dependencies, tests, coverage floor, time limits and publication state are unchanged.

The 2010 revenue raw header reuses the complete 11-column row from the original qualified all-sheet preview. Later Explanation-only observations are not relabelled as header evidence. Original and newer native controls use different exit/process field names; the new projection checks each original schema and retains its digest rather than modifying historical receipts.

## Next eligible work

Qualify a separate bounded BIFF8 stored-number evidence contract for the 2019 pair, whose source periods and amount scale are explicit. Keep OOXML literal-token requirements intact; retain encoded bytes, record type, workbook/stream/cell identity and offsets. A future profile must distinguish constants from formula caches, reject unsupported numeric states and retain the nine unit gaps and 2014 revenue edition conflict. This recommendation is preparatory and grants no numeric or rights admission.

The wider annual Budget, BEFU/HYEFU, Vote Health, Pharmac and contextual-series census, downstream phases and final recovery/review gates remain open. Refs #207, #209 and #211. Original repository validation and exact-head hosted assurance remain delivery gates for this addendum.
