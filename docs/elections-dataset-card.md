---
license: other
tags:
  - new-zealand
  - election
  - "2026"
  - "2023"
  - "2020"
  - "2017"
  - "2014"
  - "2011"
  - "2008"
  - "2005"
  - "2002"
  - "1999"
  - "1996"
  - preliminary-results
  - boundaries
  - enrolment
  - voting-statistics
  - government-data
  - archive-govt-nz
---

# New Zealand General Elections — Complete Dataset (1996–2026)

**⚠️ 2026 IS PRELIMINARY — Official results due 27 November 2026**

**✏️ Verified captures 9–11 Nov 2026**: this revision also ships the 10-11 November 2026
verified capture batches (CKAN records; Wikipedia opinion polls 1993–2026; Internet Archive
raw-byte per-place official CSVs 2017/2020/2023; NZES 1993 figshare files) — see Data
Components §§6–8.

This dataset captures **all New Zealand General Elections from 1996 to 2026**, including:
- **2026 Preliminary Results** (held 7 Nov 2026, captured 9 Nov 2026) — ~399,000 special votes not yet counted
- **Official Results 1996–2023** — Complete historical record
- **Electoral Boundaries** for every election cycle (2007–2026 Representation Commission reviews)
- **Enrolment Statistics** by electorate and age group (2026)
- **Advance Voting Statistics** with cross-election comparison (2020/2023/2026)

## Contents by Election

| Year | Status | Date | Electorates | Voting-Place CSV | Boundaries |
|------|--------|------|-------------|------------------|------------|
| **2026** | **PRELIMINARY** | 7 Nov 2026 | 71 | ✅ 71 XLSX (full) | ✅ 2025 review |
| **2023** | OFFICIAL | 14 Oct 2023 | 72 | ✅ 72 + 72 per-place CSVs (Wayback `id_`) | ✅ 2020 review |
| **2020** | OFFICIAL | 17 Oct 2020 | 72 | ✅ 72 + 72 per-place CSVs (Wayback `id_`) | ✅ 2020 review |
| **2017** | OFFICIAL | 23 Sep 2017 | 71 | ✅ 71 + 71 per-place CSVs (Wayback `id_`) | ✅ 2014 review |
| **2014** | OFFICIAL | 20 Sep 2014 | 64 | ❌ CSV summary only | ✅ 2014 review |
| **2011** | OFFICIAL | 26 Nov 2011 | 64 | ❌ CSV summary only | ✅ 2007 review |
| **2008** | OFFICIAL | 8 Nov 2008 | 64 | ❌ CSV summary only | ✅ 2007 review |
| **2005** | OFFICIAL | 17 Sep 2005 | 62 | ❌ CSV summary only | (2007 review) |
| **2002** | OFFICIAL | 27 Jul 2002 | 62 | ❌ CSV summary only | (2007 review) |
| **1999** | OFFICIAL | 27 Nov 1999 | 67 | ❌ PDF only | — |
| **1996** | OFFICIAL | 12 Oct 1996 | 65 | ❌ PDF only | — |

## Data Components

### 1. Electoral Commission Results (1996–2026)
- **2026 Preliminary**: 71 electorate XLSX files (Party + Candidate sheets), 71 PDFs, 76 HTML pages — **~10.1 MB**
- **2023/2020/2017 per-place CSVs**: 144/144/142 files captured verbatim via Internet Archive `id_` raw-byte snapshots (see §8). Note: only the previously-ingested subsets appear in the Derivatives tables below; the Wayback captures are included as raw bytes under `objects/` with per-file receipts and were NOT yet merged into the parquet derivatives.
- **2023/2020**: Voting-place CSV for ~55% (2023) and ~3% (2020) of electorates
- **2017–1996**: HTML statistics pages, PDF reports, summary CSVs

| Election | Party Vote Rows | Candidate Vote Rows | Electorates with CSV |
|----------|----------------|---------------------|---------------------|
| 2026 (prelim) | 152,626 | 62,930 | 71 (100%) |
| 2023 | 48,895 | 33,660 | ~40/72 (55%) |
| 2020 | 2,424 | 2,122 | ~2/72 (3%) |

### 2. Stats NZ Electoral Boundaries (datafinder + ArcGIS FeatureServer)
Authoritative boundaries from Representation Commission reviews, captured as GeoParquet/GeoJSON (EPSG:4326) + Parquet. The 2007–2025 sets came from the ArcGIS FeatureServer pipeline; the 2002 sets and an independent re-capture of all six 2007–2025 sets came from datafinder (§9a).

| Layer | Elections Used | Features | Year |
|-------|----------------|----------|------|
| `general-electorates-2025` | 2026 | 64 | 2025 review |
| `maori-electorates-2025` | 2026 | 7 | 2025 review |
| `general-electorates-2020` | 2020, 2023 | 65 | 2020 review |
| `maori-electorates-2020` | 2020, 2023 | 7 | 2020 review |
| `general-electorates-2014` | 2014, 2017 | 64 | 2014 review |
| `maori-electorates-2014` | 2014, 2017 | 7 | 2014 review |
| `general-electorates-2007` | 2008, 2011 | 63 | 2007 review |
| `maori-electorates-2007` | 2008, 2011 | 7 | 2007 review |
| `general-electoral-district-2002` | 2002, 2005 | 62 | 2002 review (captured 2026-11-11 from datafinder; see §9a) |
| `maori-electoral-district-2002` | 2002, 2005 | 7 | 2002 review (captured 2026-11-11 from datafinder; see §9a) |
| `constituency-2026` | Regional councils | 64 | 2026 |
| `maori-constituency-2026` | Regional councils | 22 | 2026 |

**Licence:** CC BY 4.0 Stats NZ

### 3. Enrolment & Voting Statistics (2026)
- **Enrolment by electorate × age**: 65 electorates × 11 age groups = 715 rows
- **National enrolment by age**: 11 age groups
- **Advance votes by date**: 15 days (23 Oct – 6 Nov) with 2020/2023/2026 comparison

### 4. Candidate & Party Lists (2026)
- Party lists PDF (2.3 MB): all registered parties with list rankings
- Per-electorate candidate rosters (71 HTML pages)

### 5. Election Funding: Donations, Loans & Expenses (1996–2025)

Primary-source returns published by the Electoral Commission, captured directly from
`elections.nz` through a headed Chrome DevTools Protocol session (the site sits behind an
Incapsula bot challenge that defeats plain HTTP clients).

| Collection | Coverage | Format |
|------------|----------|--------|
| Party annual returns of donations & loans | 1996–2025 | PDF (one per party per year) |
| Party donations & loans summary tables | 1996–2016 | XLSX / XLS |
| Candidate expense/donation/loan returns | 2011, 2014, 2017, 2020, 2023 | PDF (one per candidate) |
| Candidate returns summary tables | 2017, 2020, 2023 | XLSX / CSV |
| Party election-expense returns | 2008, 2011, 2014, 2017, 2020, 2023 | PDF |
| Registered promoter expense returns | 2020, 2023 | PDF |

Each file is stored as a raw byte object under `objects/<sha2>/<sha4>/<sha256>.bin` with a
sidecar `<sha256>.bin.json` recording the source URL, resource name, format, byte size and
SHA-256. Per-batch provenance lives in `evidence/capture-<capture_id>.json`.

**Licence:** Crown Copyright / CC BY 4.0 — Electoral Commission (Te Kaitiaki Take Kōwhiri).
Returns are published by the Commission under the Electoral Act 1993; individual returns
contain candidate- and party-supplied financial declarations.

### 6. CKAN & figshare Research Batch (10 November 2026)

Captured directly from `data.govt.nz` (CKAN API, unauthenticated public endpoints) and
figshare via OAI-PMH, then CAS-verified against their `sha256`/`byte_count` receipts.
See `evidence/ckan-election-batch-20261110-{classification,capture}.json` (28/28 eligible,
0 broken, 18,876,807 bytes).

| Publisher | Dataset | Files | Licence |
|-----------|---------|-------|---------|
| Department of Internal Affairs | [Local Authority Election Statistics](https://data.govt.nz/dataset/8a06249a-2bdc-4b10-97d0-6bdc962dc4b8) (elections 2004–2022) | 12 (XLSX/CSV) | CC BY 4.0 |
| Department of Internal Affairs | [Women's Franchise Petitions 1892 and 1893](https://data.govt.nz/dataset/4bc7fc3c-6a37-4463-a505-b71d1c7fb7bd) | 2 XLS | CC BY 3.0 NZ |
| Parliamentary Service | [Members of Parliament](https://data.govt.nz/dataset/f0f878d5-e2da-477d-85a0-4d2006f8b558) | 3 CSV | CC BY 4.0 |
| Electoral Commission | [Enrolment and Voting Statistics, 8 Nov 2008](https://data.govt.nz/dataset/8f1256cf-6ff6-4629-a6f5-b47f69587b3e) | 3 (CSV/TXT/XLS) | CC BY 3.0 NZ |
| Electoral Commission | [Enrolment and Voting Statistics, 26 Nov 2011](https://data.govt.nz/dataset/27337b33-40d3-4cad-8467-321caa960b1e) | 3 (CSV/TXT/XLS) | CC BY 3.0 NZ |
| Electoral Commission | [Enrolment and Voting Statistics, 20 Sep 2014](https://data.govt.nz/dataset/0140ddde-f908-4ac8-b818-79ec88519e4f) | 3 (XLS/TXT/CSV) | CC BY 3.0 NZ |
| figshare (NZES — NZ Election Study Archive) | [NZES 1993 study](https://api.figshare.com/articles/oai:figshare.com:2002590) | 2 (SAS `.sav`; questionnaire PDF) | See figshare record |

Notable: the two figshare files were restored byte-identical via a fresh pre-signed
`ndownloader.figshare.com` redirect at capture time (the signed URL is never persisted
anywhere); the original 1892/1893 petition XLS hit a transient 429 and was re-downloaded
byte-identical (see `repair_log` in the 11-10 capture receipt).

### 7. Opinion Polls 1993–2026 (Wikipedia)

Raw wikitext (`action=raw`) and rendered article HTML (`action=render`) for the
"Opinion polling for the `<year>` New Zealand general election" pages for the twelve
general-election years (1993, 1996, 1999, 2002, 2005, 2008, 2011, 2014, 2017, 2020,
2023, 2026). Licence: **CC BY-SA 4.0** (Wikipedia contributors / Wikimedia Foundation).
24 files in total (12 raw wikitext + 12 HTML). Per-year columns and pollster coverage
vary because the pages are volunteer-compiled; bulk normalisation into one analysis-ready
table is NOT performed and is proposed as a follow-up track.

**Pre-1993 gap:** no compiled polling tables exist on Wikipedia for any election before
1993 (1990 general election confirmed missing). Historical pre-election polling
sentiment for those elections is **outside the scope** of this revision.

**Non-election-year 404s (intentional):** the compiled-Wikipedia-polling page only exists
for years in which a general election was held. The capture attempted all years 1993–2026;
the 22 non-election years returned HTTP 404 for both raw wikitext and rendered HTML —
recorded as terminal-status misses in `evidence/polls-capture-20261111-capture.json`
(44 broken URLs, all `en.wikipedia.org` 404s), not as data loss.

### 8. Official Voting-Place Results — per Polling Place (Internet Archive)

Captured from `web.archive.org` **raw-byte** (`id_`) endpoints of the archived
`electionresults.govt.nz/electionresults_<year>/statistics/csv/*` CSVs — exactly the
delivered DOCTYPE/Encoding bytes of the snapshot, not a re-render.
Licence: **CC BY 3.0 NZ** (Electoral Commission) via the archived per-election site.

| Election | Candidate votes by voting place | Party votes by voting place | Wayback snapshot range |
|----------|----------------------------------|-----------------------------|------------------------|
| 2017 | 71 CSV | 71 CSV | 2018-01-27 (id_) |
| 2020 | 72 CSV | 72 CSV | 2025-02 (id_) |
| 2023 | 72 CSV | 72 CSV | 2025-02 (id_) |

2011 referendum per-place records — the only per-place official referendum files
archived (confirmed via availability API): `referendum_ppresults.csv` /
`.txt` / `.xls` (timestamps 20260128234615 / 20260129085258 / 20260129085453).

**Known gaps (documented, not archived):** 2008 general, 2011 general, 2014, and all
cycles before 2017 — no per-place official-result CSVs in this form exist on either the
live site or the Internet Archive at capture time (CDX for 2002/2008 returned data but no
per-place files; 1996/1999/2005 CDX and 2011/2014 CDX returned the Internet Archive's
Temporarily Offline interstitial at capture time). Enrolment-and-voting-statistics CSV/TXT/XLS
from 2008/2011/2014 (aggregate-level, not per-place) ARE included via §§6.

### 9. Stats NZ Boundary Geodata — attributes and geometry re-captured from datafinder

The legacy Stats NZ OData API (`https://api.stats.govt.nz/opendata/v1`) still serves an
**expired TLS certificate** (`api.stats.govt.nz`, issuer DigiCert, notAfter 29 Oct 2026,
checked again 11 Nov 2026) and returned **HTTP 502** from Azure Application Gateway even
when certificate verification was bypassed. It is no longer the capture target.

A Stats NZ API subscription key **has now been provisioned** (`STATS_NZ_API_KEY`, sent as
`Ocp-Apim-Subscription-Key`, stored only in the gitignored repo-local `.env`; the value is
never committed). It authenticates successfully against the separate **Aotearoa Data
Explorer SDMX API** (`https://api.data.stats.govt.nz/rest/`): unauthenticated data requests
return HTTP 401, keyed requests return HTTP 200; the public catalogue lists 913 dataflows
including 335 `CEN23` tables. That is statistical SDMX data, not the boundary service.

Stats NZ now names **`https://datafinder.stats.govt.nz/`** (Koordinates) as its primary
geospatial service. Its catalogue is public and CC BY 4.0, and on 11 Nov 2026 the following
were captured **byte-for-byte into CAS and sha256-verified** (20 objects, 632,312 bytes) —
`evidence/datafinder-attachments-20261111-capture.json`:

| Layer | ID | Captured |
|-------|----|----------|
| General Electorates 2025 | 122741 | attribute CSV (4,556 B) + PDF (124,308 B) + metadata |
| Māori Electorates 2025 | 122742 | attribute CSV (644 B) + PDF (128,479 B) + metadata |
| General Electorates 2020 | 104580 | attribute CSV (4,912 B) + PDF (124,797 B) + metadata |
| Māori Electorates 2020 | 104579 | attribute CSV (687 B) + PDF (126,185 B) + metadata |
| General Electoral District 2014 | 104062 | metadata only (attachments list empty) |
| General Electoral District 2007 | 104065 | metadata only (attachments list empty) |

The CSVs carry electoral population, land area, and area per electorate — useful for the
census/electorate derivatives — but **no geometry**.

### 9a. Boundary geometry (captured 11 Nov 2026)

**Boundary geometry is now captured.** The WFS gateway exposes no `FeatureType` entries and
`STATS_NZ_API_KEY` is **not** a Koordinates token (the spatial-query service rejects it with
`HTTP 403 invalid-api-key`), so geometry comes from the datafinder **export API**, which
needs a free Koordinates API token (`exports:read`, `exports:write`) held in the gitignored
`.env` as `KOORDINATES_API_KEY`. Eight layers were exported as GeoParquet (EPSG:4326) with
the publisher's own ISO 19115 metadata, stored verbatim in CAS and sha256-verified
(8 objects, 25,094,596 bytes) — `evidence/datafinder-geometry-20261111-capture.json`,
reproducible with `scripts/capture_datafinder_exports.py`.

| Layer | ID | Features | Role |
|-------|----|----------|------|
| General Electoral District 2002 | 99645 | 62 | **new coverage** |
| Māori Electoral District 2002 | 104064 | 7 | **new coverage** |
| General Electorates 2025 | 122741 | 64 | verification |
| Māori Electorates 2025 | 122742 | 7 | verification |
| General Electorates 2020 | 104580 | 65 | verification |
| Māori Electorates 2020 | 104579 | 7 | verification |
| General Electoral District 2014 | 104062 | 64 | verification |
| General Electoral District 2007 | 104065 | 63 | verification |

The 2002 pair closes a real gap: returns in this dataset run back to 1996 but boundaries
previously stopped at 2007, so the 2002 and 2005 elections had no matching geometry.

**Independent-source verification.** Decoding WKB from the archive's own
`data/general-electorates-2025.parquet` (ArcGIS FeatureServer pipeline) and from this
datafinder export gives identical feature ids and names, **577,688 vertices in both**, a
maximum relative area difference of `3.7e-08`, and a maximum bounding-box difference of
`2.8e-08°`. The two independent Stats NZ services encode the same boundaries to
floating-point precision, so the existing geometry is confirmed rather than replaced.
Feature counts also match for all six verification layers (64/7/65/7/64/63).

Remaining follow-up: capture the 2011 boundary set if a layer is published, and re-run
both capture scripts when the 2026 official count is released.

## Derivatives (Parquet — Ready for Analysis)

| File | Rows | Description |
|------|------|-------------|
| `preliminary_party_votes.parquet` | 152,626 | 2026 party votes by electorate, voting place, party |
| `preliminary_candidate_votes.parquet` | 62,930 | 2026 candidate votes by electorate, voting place, candidate |
| `preliminary_overall_party_votes.parquet` | 17 | 2026 preliminary nationwide party totals |
| `historical_2023_party_votes.parquet` | 48,895 | 2023 party votes (partial) |
| `historical_2023_candidate_votes.parquet` | 33,660 | 2023 candidate votes (partial) |
| `historical_2020_party_votes.parquet` | 2,424 | 2020 party votes (minimal) |
| `historical_2020_candidate_votes.parquet` | 2,122 | 2020 candidate votes (minimal) |
| `general-electorates-2025.parquet` | 64 | 2026 general electorate boundaries |
| `maori-electorates-2025.parquet` | 7 | 2026 Māori electorate boundaries |
| `general-electorates-2020.parquet` | 65 | 2020/2023 general boundaries |
| `maori-electorates-2020.parquet` | 7 | 2020/2023 Māori boundaries |
| `general-electorates-2014.parquet` | 64 | 2014/2017 general boundaries |
| `maori-electorates-2014.parquet` | 7 | 2014/2017 Māori boundaries |
| `general-electorates-2007.parquet` | 63 | 2008/2011 general boundaries |
| `maori-electorates-2007.parquet` | 7 | 2008/2011 Māori boundaries |
| `constituency-2026.parquet` | 64 | Regional council constituencies |
| `maori-constituency-2026.parquet` | 22 | Māori constituencies |
| `enrolment_by_electorate_age.parquet` | 715 | Enrolment by electorate × age |
| `enrolment_national_by_age.parquet` | 11 | National enrolment by age |
| `advance_votes_by_date.parquet` | 15 | Daily advance votes comparison |

*GeoJSON versions of all boundary layers also included.*

## Provenance & Integrity

- **Capture dates**: 9 Nov 2026 (2026 preliminary + historical 1996–2023 phase); 10–11 Nov 2026 (verified batch: CKAN/figshare records, Wikipedia polls, Internet Archive per-place CSVs, 2011 referendum — see §§6–9)
- **Manifest**: `manifest.json` with SHA-256 for all captured objects
- **Content-Addressed Storage**: raw bytes under `objects/sha256/<2>/<sha256>` indexed per capture receipt
- **Receipts**: per-batch capture receipts with HTTP status, headers, timestamps and repair logs, e.g.
  `evidence/capture-<capture_id>.json`, `evidence/ckan-election-batch-20261110-{classification,capture}.json`,
  `evidence/polls-classification-2026111{0,1}-classification.json`, `evidence/polls-capture-2026111{0,1}-capture.json`
- **Source evidence**: Original HTML/PDF/XLSX/CSV preserved in `objects/` with per-file SHA-256 + Blake3 in the receipts
- **Wayback reliability caveat**: `id_` raw-byte URLs are used verbatim; their bytes depend on the archived snapshot, not on source-system drift. All Wayback-fetched per-place CSVs and referendum files retain their snapshot timestamp in the receipt (`source_url`).

## Licence & Rights

| Source | Licence | Attribution |
|--------|---------|-------------|
| Electoral Commission | Crown Copyright / CC BY 4.0 | "Electoral Commission (Te Kaitiaki Take Kōwhiri)" |
| Electoral Commission / Internet Archive `id_` snapshots (per-place CSVs, referendum records) | CC BY 3.0 NZ | "Electoral Commission (Te Kaitiaki Take Kōwhiri)" |
| Stats NZ Boundaries | CC BY 4.0 | "Stats NZ" |
| Enrolment/Voting Stats | Crown Copyright / CC BY 4.0 | "Electoral Commission" |
| CKAN: DIA Local Authority Election Statistics | CC BY 4.0 | "Department of Internal Affairs" |
| CKAN: Women's Franchise Petitions 1892 & 1893 | CC BY 3.0 NZ | "Department of Internal Affairs" |
| CKAN: Parliament — Members of Parliament | CC BY 4.0 | "Parliamentary Service" |
| CKAN: EC Enrolment and Voting Statistics 2008/2011/2014 | CC BY 3.0 NZ | "Electoral Commission" |
| Wikipedia opinion-polling pages (wikitext + rendered HTML) | CC BY-SA 4.0 | "Wikipedia contributors / Wikimedia Foundation" |
| figshare NZES 1993 | See figshare record | "New Zealand Election Study, via figshare (OAI-PMH)" |

## Citation

```
archive-govt-nz (2026). New Zealand General Elections — Complete Dataset (1996–2026) [Data set].
edithatogo/archive-govt-nz-global. Captured 9–11 Nov 2026. https://huggingface.co/datasets/edithatogo/archive-govt-nz-global
```

## Update Schedule

- **Current revision**: 2026 preliminary + historical 1996–2023 + 10–11 Nov 2026 verified capture batches (CKAN/figshare; opinion polls; per-place per-election CSVs 2017/2020/2023; CKAN-record evidence).
- **Next revision**: 2026 official results — **planned capture 27 November 2026** (~399k special votes outstanding; results are preliminary until then). At that revision, 2026 preliminary figures may be replaced by the official count, and any 2026 per-place CSVs (if published) re-captured.
- **2023/2020 per-place CSV completion**: Ongoing (Cloudflare/Incapsula-protected; captured via Internet Archive raw-byte snapshots instead — see §§6–8).
- **Stats NZ geodata re-capture**: Boundary **attributes** (2025/2020 general + Māori) and **geometry** (2002 general + Māori, plus an independent re-capture of all six 2007–2025 sets) captured and sha256-verified from `datafinder.stats.govt.nz`. GeoParquet WKB matches the archive's ArcGIS geometry to `3.7e-08` relative area (§9a). `STATS_NZ_API_KEY` alone is not sufficient: geometry needs a Koordinates token, held in `.env` as `KOORDINATES_API_KEY`.

## Part of

`archive-govt-nz-global` — Evidence-first archival system for NZ government datasets.
Repository: https://github.com/edithatogo/archive-govt-nz