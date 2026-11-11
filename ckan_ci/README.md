# Stats NZ boundary geodata — capture status (updated 2026-11-11)

Scope: track the Stats NZ access needed by the election archive, and record what is proven
working versus still blocked. This file is an engineering note, not an artifact.

## Credentials

- `STATS_NZ_API_KEY` — Stats NZ API Portal subscription key.
  - Sent as `Ocp-Apim-Subscription-Key` (Aotearoa Data Explorer).
  - Sent as the `;key=` path parameter (datafinder WFS gateway).
  - **Not** a Koordinates API token; the datafinder spatial-query and data-table services
    reject it with `HTTP 403 invalid-api-key`.
- A Koordinates ID / API token (query + download scope) is a **separate** credential, only
  needed for geometry export.
- Both live only in the repo-local `.env`, which is gitignored (`.gitignore:16`). Values are
  never committed, logged, or copied into evidence. `.env.example` documents the variable.
  CI must inject them as masked variables of the same name.

## Proven working (1): Aotearoa Data Explorer SDMX API

- Base URL `https://api.data.stats.govt.nz/rest/`; TLS valid at probe time (notAfter
  2026-12-14).
- Unauthenticated data request → **HTTP 401**; keyed request → **HTTP 200** `text/csv`
  (verified slice `data/STATSNZ,AGR_AGR_001,1.0/all?firstNObservations=2`, 47,360 bytes).
- Public structure catalogue: 913 dataflows, including 335 `CEN23` (2023 Census) tables.

## Proven working (2): Geographic Data Service (datafinder, Koordinates)

- `https://datafinder.stats.govt.nz/` is the platform Stats NZ now names as its **primary
  geospatial service**; `api.stats.govt.nz/opendata/v1` is no longer the target.
- Layer catalogue `services/api/v1/data/` is public (HTTP 200, 61,004 bytes, 100 entries on
  page 1), all CC BY 4.0, and lists the electorate boundary families:
  `General Electorates 2025` (122741), `Māori Electorates 2025` (122742),
  `General Electorates 2020` (104580), `Māori Electorates 2020` (104579),
  `General Electoral District 2014` (104062), `General Electoral District 2007` (104065).
- **Captured and sha256-verified (2026-11-11):** 20 objects / 632,312 bytes in the local CAS
  by `scripts/capture_datafinder_attachments.py` — per-layer and per-version metadata for all
  six layers, plus attribute CSVs (electoral population, land area, area) and PDFs for the
  four 2025/2020 layers. Receipt: `../evidence/datafinder-attachments-20261111-capture.json`.
  The 2014 and 2007 layers publish no attachments.
- These attachments contain **no geometry**.

## Proven working (3): boundary geometry export

- `services/api/v1.x/exports/` is **HTTP 401** without a Koordinates token and **HTTP 201**
  with one. `STATS_NZ_API_KEY` is not accepted there — the spatial-query service rejects it
  with `HTTP 403 invalid-api-key`, so a free Koordinates API token
  (`exports:read`, `exports:write`) is the required credential.
- Eight layers exported as GeoParquet (EPSG:4326) on 2026-11-11, stored verbatim in CAS and
  sha256-verified (8 objects, 25,094,596 bytes):
  `scripts/capture_datafinder_exports.py`, receipt
  `../evidence/datafinder-geometry-20261111-capture.json`.
- **New coverage:** General Electoral District 2002 (62 features) and Māori Electoral
  District 2002 (7), closing the 2002/2005 boundary gap.
- **Verification:** for General Electorates 2025 the decoded WKB matches the archive's
  ArcGIS-sourced parquet — same 64 ids and names, 577,688 vertices in both, max relative
  area delta `3.7e-08`, max bbox delta `2.8e-08°`. Feature counts match for all six
  re-captured layers.

## Notes on access design

- The layer catalogue, per-layer metadata, and attachment CSVs/PDFs remain public, so the
  attribute capture needs no credential at all (20 objects, 632,312 bytes).
- Only geometry export is gated.
- `KOORDINATES_API_KEY` can be rotated at `https://datafinder.stats.govt.nz/my/api/`; it is
  independent of the Stats NZ portal key.

## Automation

| Workflow | Trigger | Credential |
|----------|---------|------------|
| `.github/workflows/stats-nz-boundary-capture.yml` | cron 08:00 UTC on 28 Nov + manual | `KOORDINATES_API_KEY` (fails closed without it) |
| `.gitlab-ci.yml` → `boundary-capture` | schedule / manual, `BOUNDARY_CAPTURE=true` | `KOORDINATES_API_KEY` (fails closed without it) |

Both run `scripts/capture_datafinder_attachments.py` first (credential-free) and then
`scripts/capture_datafinder_exports.py`. Neither echoes a credential; the geometry script
also strips the auth header before following the pre-signed storage redirect, because the
storage endpoint rejects a request that carries two auth mechanisms.

`objects/` is gitignored (`.gitignore`), which is why an unrelated `git clean -x` in the tree
can remove captured payloads. The capture scripts are idempotent and byte-reproducible, so
that recovery is a re-run rather than a loss.

## Unblock checklist

1. ~~Obtain a Koordinates API token.~~ Done 2026-11-11 (`KOORDINATES_API_KEY` in the
   gitignored `.env`).
2. ~~Export boundary geometry and verify.~~ Done for the eight layers above.
3. ~~Publish the new coverage to the Hugging Face dataset.~~ Done 2026-11-11 at commit
   `caf3532c` (2002 general + Māori boundaries, 21 files, 21 sha256-verified). The six
   verification-only re-captures were deliberately not republished. Receipt:
   `../evidence/huggingface-publish-receipt-20261111-datafinder.json`.
4. ~~Wire GitHub Actions + GitLab CI keyed off masked credentials.~~ Added
   `.github/workflows/stats-nz-boundary-capture.yml` and the `boundary-capture` job in
   `.gitlab-ci.yml`. Both fail closed if `KOORDINATES_API_KEY` is absent and print no
   secret material.

### Remaining operator action

Set these once in the repository settings; the workflows cannot read them from `.env`:

| Where | Name | Notes |
|-------|------|-------|
| GitHub Actions secrets | `KOORDINATES_API_KEY` | required for geometry export |
| GitHub Actions secrets | `HF_TOKEN` | only needed when `publish` is set |
| GitHub Actions secrets | `STATS_NZ_API_KEY` | optional; ADE capability probe only |
| GitLab CI/CD variables | `KOORDINATES_API_KEY` | mark **masked** (and protected) |
| GitHub Actions variables | `BOUNDARY_CAPTURE=true` | enable the schedule (default off) |
| GitLab CI/CD variables | `BOUNDARY_CAPTURE=true` | enable the scheduled job |

Schedules: GitHub cron runs 08:00 UTC on 28 November; GitLab runs the manual
`boundary-capture` job when `BOUNDARY_CAPTURE=true`. The 2026 official count is due
**27 November 2026**.

Licence: Stats NZ data open under CC BY 4.0. See repo `docs/elections-dataset-card.md` §9
for the integrator card.
