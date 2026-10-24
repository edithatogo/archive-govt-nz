# Budget census and Bronze preservation reconciliation — 2026-10-23

## Result

The preservation crosswalk for the 40 registered annual Budget expenditure
and revenue roles (2007–2026) is complete at the file-candidate level. Every
edition/kind role has a publisher-linked archived candidate. This resolves the
missing-byte question for that bounded cohort; it does not approve equivalence
between a historical registered URL and a separately identified candidate,
complete the wider Budget/forecast census, or qualify rights or native meaning.

The independently retained records reconcile as follows:

- The 40-record annual register contains 20 expenditure and 20 revenue roles.
- Its first preservation attempt reused six exact existing captures and
  selected the other 34 URLs. Eighteen registered URLs returned and were
  captured; 16 returned HTTP 404. Those 404 observations remain in the record.
- The official locator work identified 16 publisher-linked correction
  candidates (10 expenditure and 6 revenue). The complete role inventory has
  40 candidate rows and covers all 40 registered edition/kind roles.
- The aggregate archive contains 46 resources: 20 expenditure workbooks, 20
  revenue workbooks, and 6 departmental-statement workbooks. On 2026-10-23,
  all 46 CAS bodies independently matched their SHA-256 names, and all 46
  recorded WARC digests matched retained `response.warc` files.
- The 19-resource additional locator cohort contains 13 captured workbook
  candidates and 6 official publication pages that returned HTTP 403. Together
  with the 4 pages in the first locator cohort, all 10 distinct publication
  page requests returned HTTP 403. Cached page observations support discovery
  of candidate links only; no native page capture or rights conclusion is
  inferred.
- The union inventory records 72 distinct URLs, with 46 captured resources.
  The 40 annual Budget role slots are covered by candidates, while the six
  inaccessible publication pages and other non-captured locator observations
  remain separately represented. The union count is not a whole-corpus
  completeness claim.

## Remaining decisions and qualifications

Keep the original registered identifiers, corrected candidate identifiers,
and their evidence-linked role relationships distinct. The locator receipts
explicitly do not authorize numerical, edition-version, or URL-alias
equivalence. Do not rewrite the 16 HTTP 404 observations.

Rights eligibility remains unevaluated for the locator cohort. Period, unit,
legacy-layout, and definition qualification must use the relevant native
source-specific evidence and existing vintage profiles. Capturing bytes does
not establish those properties. Separately completed 2007–2026 vintage work
remains governed by its own receipts and does not broaden this preservation
crosswalk.

The ten 403 publication pages are an access gap in page preservation, not a
missing workbook body for any of the 40 registered edition/kind roles. Retain
the cached discovery evidence and 403 outcomes; do not infer current
unavailability or retry without a concrete authorized access route.

This reconciliation covers the registered 2007–2026 annual Budget pair and
the captured locator candidates. It does not close the broader Phase 1 census
for BEFU/HYEFU, Vote Health, Pharmac, or contextual series, nor any downstream
track phase.

## Evidence

- `annual-budget-census-20261019-v1.json`: immutable 40-role register.
- `budget-preservation-qualification-20261019-v1.json`: 6 reused captures,
  18 new captures, and 16 registered-URL 404s.
- `budget-locator-qualification-20261019-v2.json`: 46 body/WARC bindings,
  40 candidate roles, 16 correction candidates, and six 403 page observations.
- `budget-locator-delivery-20261020-v1.json`: protected PR #727 delivery and
  historical all-46 fixity result; that receipt's status does not claim rights,
  native meaning, or broader track completion.
- Current local fixity replay: all 46 CAS objects and all 46 WARC digests
  matched; zero mismatches.

