# Treasury replacement and lawful redundancy search — 2026-08-11

## Outcome

The unresolved set contains 47 resources represented by 36 unique source URLs.
The bounded search found 23 unique URLs with successful Internet Archive
captures. Nineteen latest snapshots were downloaded into the local evidence
object store and SHA-256 hashed; four snapshot downloads failed; thirteen URLs
had no usable snapshot in the returned timemap or the query was unavailable.

Internet Archive snapshots are retained as **lawful backup candidates**, not as
automatic replacements. Each candidate must still pass content-type, title,
provenance, and resource-identity checks before it can be promoted into the
archive's source-capture state.

## Official replacement candidates

The Treasury's current Chief Executive Expenses information-release page is a
canonical publisher landing page. It identifies the disclosure as official
information, states Crown Copyright CC BY 4.0, and lists the historical files
from 2010 onward. The page is the preferred replacement for catalogue links
that remain blocked or have uncertain rights:

<https://www.treasury.govt.nz/publications/information-release/chief-executive-expenses-information-release>

The page exposes these direct publisher attachments for the affected periods:

- `https://www.treasury.govt.nz/sites/default/files/2025-07/tsy-ceep-nov24-jun25-rennie.xlsx`
- `https://www.treasury.govt.nz/sites/default/files/2025-07/tsy-ceep-nov24-mersi.xlsx`
- `https://www.treasury.govt.nz/sites/default/files/2025-07/tsy-ceep-sep24-nov24-little.xlsx`
- `https://www.treasury.govt.nz/sites/default/files/2025-07/tsy-ceep-jul24-sep24-mcliesh.xlsx`
- `https://www.treasury.govt.nz/sites/default/files/2024-07/tsy-ceep-jul23-jun24.xlsx`
- `https://www.treasury.govt.nz/sites/default/files/2023-07/Treasury%20Chief%20Executive%20Expenses%201%20July%202022%20-%2030%20June%202023.xlsx`
- `https://www.treasury.govt.nz/sites/default/files/2022-08/tsy-ceep-jul21-jun22.xlsx`
- `https://www.treasury.govt.nz/sites/default/files/2021-08/tsy-ceep-jul20-jun21.xlsx`
- `https://www.treasury.govt.nz/sites/default/files/2020-07/tsy-ceep-sep19-jun20.xlsx`
- `https://www.treasury.govt.nz/sites/default/files/2019-07/tsy-ceexp-jan-june19.xlsx`
- `https://www.treasury.govt.nz/sites/default/files/2019-03/tsy-ceexp-jul-dec-18.xlsx`
- `https://www.treasury.govt.nz/sites/default/files/2018-07/tsy-ceexp-jul17-jun18.xlsx`
- `https://www.treasury.govt.nz/sites/default/files/2018-06/tsy-ceexp-jul16-jun17.xlsx`
- `https://www.treasury.govt.nz/sites/default/files/2018-06/tsy-ceexp-jul-15-jun16.xls`

The 2016 Budget and HYEFU pages are also current official publication pages
and expose replacement publication records for the old `/budget/...` paths:

- <https://www.treasury.govt.nz/publications/efu/budget-economic-and-fiscal-update-2016>
- <https://www.treasury.govt.nz/publications/efu/half-year-economic-and-fiscal-update-2016>
- <https://www.treasury.govt.nz/publications/fiscal-strategy-report/fiscal-strategy-report-2016>

The HTTPS `hyefu16-charts-data.xlsx` and the two Productivity Commission URL
mapping files returned HTTP 200 in the bounded preflight. They remain
rights/provenance candidates until downloaded and reconciled to the CKAN
resource hashes.

## Prohibited source

Anna's Archive was not queried or used. I cannot assist with retrieval from a
known illicit distribution source. The lawful redundancy lanes are official
publisher files, the Internet Archive, Common Crawl, and other authorised
public-sector mirrors.

## Receipts

- Discovery metadata: `evidence/replacement-discovery-20260811.json`
- Download and hash receipt: `evidence/internet-archive-backup-20260811.json`
- Objects: `build/live/authorized-20260811/internet-archive-backups/`

