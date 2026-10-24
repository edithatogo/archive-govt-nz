# Vote Health Estimates overview source census: 2016/17

This addendum reconciles the already-captured Budget 2016 Vote Health Estimates
PDF with the existing official capture manifest. It reuses the pinned Bronze
object and WARC; it does not perform another request or capture.

| Census field | Evidence |
| --- | --- |
| Publisher/source | New Zealand Treasury, *The Estimates of Appropriations 2016/17*, Health Sector, Vote Health, Budget 2016, Volume 6 |
| Edition and period | Estimates for fiscal year 2016/17; the selected overview states Vote Health funding “in 2016/17” |
| Official locator | `https://www.treasury.govt.nz/sites/default/files/2016-05/est16-v6-health.pdf` |
| Captured object | `treasury-vote-health-pdf-6941bba9f5f094ca`; SHA-256 `c997ffecb631e4dfd0ffd8a1e620585b6b963df11f94164adb2ac02cfa391b2e`; 1,024,038 bytes; 102 pages |
| Capture record | `official-capture-2026-10-03-health-complete.json`; source observation `2026-08-29T09:00:17Z`; HTTP 200 |
| WARC evidence | SHA-256 `5ec442ec495efd804b6db6761ace86c8bb605c7c6ead0cdb6b9d892c7bcb102d`; payload digest matches the PDF. WARC date is absent, so no new remote-capture time is claimed. |
| Rights evidence | Treasury copyright and licensing page `https://www.treasury.govt.nz/copyright-and-licensing`; the capture receipt records publisher-declared CC-BY-4.0 and eligible source acquisition. Rights for normalized facts or downstream publication remain unevaluated. |
| Layout evidence | `source-pdf-layout-baseline-20261003.json`, layout SHA-256 `7d8eedecead8e7b8f1c394eb0637e2927dd2252427017351edd3aca276439ae3`; 102-page structural baseline. Text semantics and the remaining pages are not reviewed by that baseline. |
| Selected scope | Printed pages 6–7 (PDF pages 2–3), “Overview of the Vote”: 24 monetary statements in `$ million`, for the 2016/17 estimate. The 100 other PDF pages remain unreviewed by this overview profile. |
| Definitions/limits | The overview reports nominal source amounts and source-stated shares of the Vote. It does not establish an ISO currency field, price base, annual actuals, or a time series. Percentages remain source qualifiers; values are not reclassified or summed into new measures. |
| Gaps | No complete semantic review of the other 100 pages, no cross-edition reconciliation, no currency/base admission, no rights decision for derived records, and no publication authorization. |

Machine reconciliation: `vote-health-estimates-overview-2016-17-census.json`.
The 2016/17 source profile uses this census and the existing source/layout
preflight; it does not duplicate acquisition evidence.
