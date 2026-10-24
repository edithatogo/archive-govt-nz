# Vote Health Estimates overview source census: 2017/18

This addendum reconciles the already-captured Budget 2017 Vote Health Estimates
PDF with its official capture record. It reuses the Bronze object and WARC and
does not perform another request or capture.

| Census field | Evidence |
| --- | --- |
| Publisher/source | New Zealand Treasury, *The Estimates of Appropriations 2017/18*, Health Sector, Vote Health, Budget 2017, Volume 6 |
| Edition and period | Estimates for fiscal year 2017/18; the selected overview states Vote Health funding “in 2017/18” |
| Official locator | `https://www.treasury.govt.nz/sites/default/files/2017-05/est17-v6-health-v2.pdf` |
| Captured object | `treasury-vote-health-pdf-4cad52281f0c61e6`; SHA-256 `3fc0cc6a193c232e9278389f42dbd9003cff03228ac3c83cbfe58452f5711604`; 980,866 bytes; 95 pages |
| Capture record | `official-capture-2026-10-03-health-complete.json`; source observation `2026-08-29T09:00:17Z`; HTTP 200 |
| WARC evidence | SHA-256 `e19b746dd545f78fc1a8d5458c8ce15c9468d21d6d2cfc430af95660ca6c203d`; payload digest matches the PDF. |
| Rights evidence | Treasury copyright and licensing page `https://www.treasury.govt.nz/copyright-and-licensing`; receipt records publisher-declared CC-BY-4.0 and eligible source acquisition. Rights for normalized facts and downstream publication remain unevaluated. |
| Layout evidence | `source-pdf-layout-baseline-20261002.json`; structural baseline plus direct page-2/page-3 text inspection for this exact hash. Page 2 contains “Overview of the Vote”; page 3 begins “Details of Appropriations and Capital Injections.” |
| Selected scope | PDF page 2: 25 source-reported monetary statements in whole `$ million`, for the 2017/18 estimate. Page 3 is a layout confirmation only; the other 94 pages remain outside the profile. |
| Definitions/limits | Values and percentages remain as reported in the edition. They are not annual actuals or an approved time series. No currency code, price base, deflator or join is inferred; source category names are not reconciled to other editions. |
| Gaps | No semantic review of the other 94 pages, no cross-edition reconciliation, no currency/base admission, no rights decision for derived records, and no publication authorization. Supplementary Estimates are not included. |

Machine reconciliation: `vote-health-estimates-overview-2017-18-census.json`.
The profile reuses this capture and the existing Bronze object; it does not
duplicate acquisition evidence.
