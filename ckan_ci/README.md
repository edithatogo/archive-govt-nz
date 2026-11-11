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

## Still blocked: boundary geometry

- WFS gateway accepts `STATS_NZ_API_KEY` (`services;key=<key>/wfs/` → HTTP 200 capabilities,
  94,189 bytes; without a key → HTTP 401) but the capabilities expose **no `FeatureType`
  entries**, and per-layer WFS paths return 404/400.
- `services/api/v1.x/exports/` → **HTTP 401** ("Authentication credentials were not
  provided") without a Koordinates token.
- `services/query/v1/vector.json?key=<subscription key>` → **HTTP 403
  `invalid-api-key`**, which proves the subscription key cannot substitute for a Koordinates
  token.

## Unblock checklist

1. Create/sign in to a Koordinates ID and mint an API token with query/download scope.
2. Export GeoJSON (EPSG:4326) and/or SHP for layers 122741, 122742, 104580, 104579, 104062,
   104065 via the datafinder Export UI or the export API.
3. Verify byte count + sha256, store in CAS with per-file receipts.
4. Wire GitHub Actions + GitLab CI keyed off masked credentials; no auditable payload may
   print a key.

Licence: Stats NZ data open under CC BY 4.0. See repo `docs/elections-dataset-card.md` §9
for the integrator card.
