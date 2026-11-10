# New Zealand Election Study (NZES) — Source Provenance

The New Zealand Election Study is New Zealand's longest-running academic study of
electoral behaviour: a post-election survey run since 1987, now administered out of the
University of Auckland. Its **microdata are not openly downloadable**. They are
distributed under conditions of access, so this archive does not hold the survey data.
What it holds — and documents with cryptographic evidence — is the **provenance**: where
each wave lives, who publishes it, under what licence and access terms, and what every
custodian's public metadata says.

This record exists so that a later reader can reconstruct the chain of custody for the
study without re-discovering it, and can tell the difference between an open dataset
this archive can redistribute and a restricted one it cannot.

## Custodians

| Custodian | Role | Coverage | Access |
|-----------|------|----------|--------|
| **ADA Dataverse** (`dataverse.ada.edu.au`) | Current distribution point, Australian Data Archive | All waves 1987–2023 as DOI-identified datasets | Metadata public; **every file download is gated by a guestbook response** (name, email, institution, position) under the NZES conditions of use |
| **University of Auckland Figshare** (`auckland.figshare.com`) | Legacy deposits | NZES2017 (NZES2008 record withdrawn) | Deposit **metadata is CC0**; the API record attaches **no data files**, so these records are provenance only |
| **NZES project site** (`nzes.net`) | Project home and access policy | — | Documents access and citing requirements; points at the ADA Dataverse collection |

> The historical `nzes.org` domain now **301-redirects to `https://www.nzes.net/`**. The
> redirect is recorded here because older citations and the Internet Archive still refer
> to `nzes.org`.

## Waves

Thirteen waves are indexed by DataCite through ADA Dataverse, each with a DOI:

| Wave | DOI | Publisher |
|------|-----|-----------|
| 1987 | `10.26193/zyogjs` | ADA Dataverse |
| 1990 | `10.26193/u0nbfs` | ADA Dataverse |
| 1993 | `10.26193/9odfxu` | ADA Dataverse |
| 1996 | `10.26193/o0lrzz` | ADA Dataverse |
| 1999 | `10.26193/ungixj` | ADA Dataverse |
| 2002 | `10.26193/9de0x4` | ADA Dataverse |
| 2005 | `10.26193/wj8dgc` | ADA Dataverse |
| 2008 | `10.26193/6cveym` | ADA Dataverse |
| 2011 | `10.26193/yzdmf3` | ADA Dataverse |
| 2014 | `10.26193/mf9dnl` | ADA Dataverse |
| 2017 | `10.26193/28jjfb` | ADA Dataverse |
| 2020 | `10.26193/bpamyj` | ADA Dataverse |
| 2023 | `10.26193/hhmeuz` | ADA Dataverse |

The collection landing page is
`https://dataverse.ada.edu.au/dataverse/new-zealand-election-study`.

Legacy University of Auckland deposits:

| Deposit | DOI | Note |
|---------|-----|------|
| NZES2008: New Zealand Election Study | `10.17608/k6.auckland.2002830` | Landing page returns **HTTP 410 Gone**; the deposit has been withdrawn |
| NZES2017: New Zealand Election Study | `10.17608/k6.auckland.6453134` | CC0 metadata; `embargo_type = article`, no files in the API record |
| NZES: New Zealand Election and Referendum Study (collection) | `10.17608/k6.auckland.c.2174637` | Collection DOI; the Figshare collections API returns 404 for it, so only the landing page is real |

## How access is actually gated

Dataverse does not mark the NZES files as `restricted`. Instead each dataset carries a
**guestbook ID**, and Dataverse refuses to serve a file until the requester submits that
guestbook's response:

```
GET /api/access/datafile/20315
400 {"message": "You may not download this file without the required
      Guestbook response for guestbookID 53."}
```

Three guestbooks are in use. Their definitions are public and are captured here:

| Guestbook | Name | Used by | Required fields |
|-----------|------|---------|-----------------|
| 2 | ADA General Access Guestbook (2017) | 1993 | name, email, institution, position + custom questions |
| 22 | Standard Recorded Open Access Guestbook (2019) | 1987–2020 (all but 1993, 2023) | name, email, institution, position |
| 53 | ADA Standard Recorded Open Access Guestbook (2021) | 2023 | name, email, institution, position |

Independently, most waves also set `fileAccessRequest = true`, meaning an approved access
request is needed on top of the guestbook; the 2023 wave sets it `false` and relies on the
guestbook alone. Together these are the "conditions of use" the NZES imposes, and they are
why the microdata cannot be redistributed by this archive.

Each wave's public documentation — codebook, questionnaire, readme and, for 2020, section
frequency tables — is listed in `evidence/nzes-sources.json` under `ada_dataverse`, with
content type, byte size and the depositor's own checksum for every file. The data matrices
(`.dta` / `.sav` / `.rdata` / SPSS / SAS / CSV) are the access-gated part.

## What was captured

`tools/archive_nzes_sources.py` records every metadata response into the content-addressed
store as `objects/<sha2>/<sha4>/<sha256>.bin`, each with a `<sha256>.bin.json` sidecar
carrying the source URL, retrieval time, HTTP status, content type, byte size and SHA-256.
It then emits:

| Artefact | Contents |
|----------|----------|
| `evidence/nzes-sources.json` | Flat summary: custodians, 23 indexed DOI records, and every captured file with URL + SHA-256 |
| `evidence/nzes-sources-ro-crate.jsonld` | RO-Crate 1.1 JSON-LD graph (`Dataset` entities per DOI, `File` entities per captured response) |

Sources captured over plain HTTPS: the DataCite DOI index, the Figshare API/article and
collection records, and the four `nzes.net` policy pages (home, data, access conditions,
citing). The **ADA Dataverse API sits behind an Anubis proof-of-work challenge**, so its
per-wave records must be fetched through a headed Chrome — run the tool with
`--cdp-port 9222` to add those.

```bash
# Metadata-only sources (no browser required)
uv run python tools/archive_nzes_sources.py --objects-dir objects --evidence-dir evidence

# Add ADA Dataverse records (requires headed Chrome on the DevTools port)
uv run python tools/archive_nzes_sources.py \
    --objects-dir objects --evidence-dir evidence --cdp-port 9222
```

## Why the data itself is not archived

The NZES microdata are **access-restricted, not merely technically blocked**. Every wave
from 1987 to 2023 is held behind an ADA Dataverse request-and-approval process, and the
University of Auckland deposits have their files embargoed or withdrawn. Archiving the
survey responses would breach the custodians' conditions of use, so this archive records
the provenance and the access conditions instead, and cites the DOIs for anyone who can
meet those conditions.

The 23 DOI records captured include third-party **replication datasets that cite the
NZES** (for example a Harvard Dataverse study on majoritarian systems). Those are flagged
in `nzes-sources.json` as "not the source survey" so they are not mistaken for the study.

## Rights

Custodian metadata is captured for archival reference. The NZES itself remains the
property of its depositors and is not redistributed here. Cite the study through the
project's guidance at `https://www.nzes.net/data/citing-the-nzes/`.

## Part of

`archive-govt-nz-global` — Evidence-first archival system for NZ government datasets.
