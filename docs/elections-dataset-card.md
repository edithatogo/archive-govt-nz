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
| **2023** | OFFICIAL | 14 Oct 2023 | 72 | ⚠️ Partial (~55%) | ✅ 2020 review |
| **2020** | OFFICIAL | 17 Oct 2020 | 72 | ⚠️ Minimal | ✅ 2020 review |
| **2017** | OFFICIAL | 23 Sep 2017 | 71 | ❌ HTML/PDF only | ✅ 2014 review |
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
- **2023/2020**: Voting-place CSV for ~55% (2023) and ~3% (2020) of electorates
- **2017–1996**: HTML statistics pages, PDF reports, summary CSVs

| Election | Party Vote Rows | Candidate Vote Rows | Electorates with CSV |
|----------|----------------|---------------------|---------------------|
| 2026 (prelim) | 152,626 | 62,930 | 71 (100%) |
| 2023 | 48,895 | 33,660 | ~40/72 (55%) |
| 2020 | 2,424 | 2,122 | ~2/72 (3%) |

### 2. Stats NZ Electoral Boundaries (ArcGIS FeatureServer)
Authoritative boundaries from Representation Commission reviews, captured as GeoJSON (EPSG:4326) + Parquet:

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

- **Capture date**: 9 November 2026
- **Manifest**: `manifest.json` with SHA-256 for all 768 files
- **Content-Addressed Storage**: 740 raw objects in `objects/sha256/` indexed by `index.json`
- **Receipts**: CDP capture receipts with HTTP status, headers, timestamps
- **Source evidence**: Original HTML/PDF/XLSX/CSV preserved in `raw/`

## Licence & Rights

| Source | Licence | Attribution |
|--------|---------|-------------|
| Electoral Commission | Crown Copyright / CC BY 4.0 | "Electoral Commission (Te Kaitiaki Take Kōwhiri)" |
| Stats NZ Boundaries | CC BY 4.0 | "Stats NZ" |
| Enrolment/Voting Stats | Crown Copyright / CC BY 4.0 | "Electoral Commission" |

## Citation

```
archive-govt-nz (2026). New Zealand General Elections — Complete Dataset (1996–2026) [Data set].
edithatogo/archive-govt-nz-global. Captured 9 Nov 2026. https://huggingface.co/datasets/edithatogo/archive-govt-nz-global
```

## Update Schedule

- **Current revision**: 2026 preliminary + historical 1996–2023 (captured 9 Nov 2026)
- **Next revision**: 2026 official results — planned capture **27 November 2026**
- **2023/2020 CSV completion**: Ongoing (Cloudflare-protected)

## Part of

`archive-govt-nz-global` — Evidence-first archival system for NZ government datasets.
Repository: https://github.com/edithatogo/archive-govt-nz