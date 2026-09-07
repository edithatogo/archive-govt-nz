# Donor PDF identity discrepancy: retained-byte proof

Observed read-only on 2026-09-07. This receipt preserves the identity finding;
it does not implement a PDF extractor, validate table layout, qualify numerical
facts or correct shared source registers. Parent owns layout follow-up.

## Immutable source

- Donor commit: `4668e6c3b1b492086941d4c1ef96e299250a8301`.
- Donor path: `data/raw/historical_appropriations/appropriation-main-estimates-2024-25.pdf`.
- SHA-256: `620ff6a34e7be955ce70316af8f6fa4a9ca95689fa5036e076b50c13431d1fa8`.
- Byte count: **1,339,480**.
- Retained CAS path:
  `/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations/bronze-cas/sha256/62/620ff6a34e7be955ce70316af8f6fa4a9ca95689fa5036e076b50c13431d1fa8`.
- Existing donor manifest: external `manifests/donor-4668e6c.json` under the
  same health archive. Source hash rechecked after the preceding text audit;
  exact bytes are unchanged. No downloaded replacement or payload committed.

## Independent identity observations

Poppler `pdfinfo` 26.09.0 reports 471 pages, PDF 1.4, no encryption, and title:

> PDF File – Supplementary Estimates of Appropriations Year Ending 30 Jun 03 - The Treasury

Metadata Author is `New Zealand Treasury`. Creation and modification dates are
4 June 2003; these are embedded metadata, not trusted acquisition timestamps.

`pdftotext -layout` on PDF page **1** independently yields the cover headings:

- `B.7`
- `15 May 2003`
- `The Supplementary Estimates of Appropriations`
- `for the Government of New Zealand`
- `for the year ending 30 June 2003`
- ISBN `0-478-11844-9`.

The cover content and metadata agree on **2003 Supplementary Estimates**.
Neither supports the donor filename's **2024-25 Main Estimates** identity.
The donor path remains provenance; it must not assign period or estimate type.
No claim is made about why the donor filename is wrong or which online URL
originally supplied these bytes.

## Exact bounded Health ranges

PDF ordinals below are **one-based physical pages**, not printed labels.
Text-based boundary observations, pending visual/layout verification:

| Physical PDF pages | Printed B.7 pages | Observed scope |
| --- | --- | --- |
| 251 | 233 | VOTE Health section title |
| 252 | 234 | Health minister/department context |
| 253–266 | 235–248 | Part B1: Details of Appropriations, including continuations |
| 267–268 | 249–250 | Part F/F1: Crown Revenue and Receipts, including continuation |
| 269 | 251 | VOTE Housing begins; outside Health slice |

On physical page 253 the header states **2002/03**, with grouped columns
**Main Estimates / Supplementary Estimates / Cumulative Vote**. Each has
**Annual / Other** columns labelled **$000**. Text includes parenthesized
negative adjustments, dashes, wrapped labels and descriptions continuing across
pages. A future parser must not confuse the grouped columns, drop signs, treat
dashes as zero without a source rule, or derive a 2024/25 observation.

The earlier regex structural inventory also counted 471 page markers. Poppler
now corroborates a 471-page document; neither result establishes 471 extracted
pages or a table/cell fact count. **One donor PDF structural unit; zero qualified
PDF numerical facts.** This receipt is an identity/range correction, not a
completed extraction or Gold/rights decision.

## Reproduction and remaining gate

Read-only commands against the exact CAS path:

```text
shasum -a 256 <CAS-path>
pdfinfo <CAS-path>
pdftotext -f 1 -l 1 -layout <CAS-path> -
pdftotext -f 251 -l 269 -layout <CAS-path> -
```

The preceding audit used the same text renderer on the complete document,
splitting form-feed page boundaries to locate this bounded range. No extracted
text payload was stored in Git. The PDF skill's text/layout distinction informed
the audit: no screenshot or table-layout verification is claimed. Layout,
column/row continuation, source notes and numerical admission remain the
parent's follow-up. Conductor review preserves this as an explicit source
identity gate rather than silently relabelling the retained object.
