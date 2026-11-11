# Stats NZ API — capability status (updated 2026-11-11)

Scope: track the Stats NZ API access needed by the election archive, and record what is
proven working versus still blocked. This file is an engineering note, not an artifact.

## Credential

- `STATS_NZ_API_KEY` — Stats NZ API Portal subscription key.
- Sent as the HTTP header `Ocp-Apim-Subscription-Key` (ADE) and as the `;key=` path
  parameter (datafinder WFS).
- Stored only in the repo-local `.env`, which is gitignored (`.gitignore:16`). The value is
  never committed, logged, or copied into evidence. `.env.example` documents the variable.
- CI, when enabled, must inject it as a masked CI variable of the same name.

## Proven working (1): Aotearoa Data Explorer SDMX API

- Base URL: `https://api.data.stats.govt.nz/rest/`
- TLS valid at probe time (`CN=api.data.stats.govt.nz`, Google Trust Services, notAfter
  2026-12-14).
- Unauthenticated data request → **HTTP 401** (`Access denied due to missing subscription
  key`).
- Keyed data request → **HTTP 200** `text/csv` (verified slice:
  `data/STATSNZ,AGR_AGR_001,1.0/all?firstNObservations=2`, 47,360 bytes).
- Public structure catalogue lists **913 dataflows**, including **335 `CEN23`** (2023
  Census) tables; `dataflow/STATSNZ/all?detail=allstubs` returns 200 XML (654,591 bytes).

## Proven working (2): Geographic Data Service (datafinder, Koordinates)

- `https://datafinder.stats.govt.nz/` is the platform Stats NZ now names as its **primary
  geospatial service**.
- Layer catalogue `services/api/v1/data/` is public (HTTP 200, 61,004 bytes, 100 entries on
  page 1) and lists `General Electorates 2025` (122741), `Māori Electorates 2025` (122742),
  `General Electorates 2020` (104580), `Māori Electorates 2020` (104579),
  `General Electoral District 2014` (104062), `General Electoral District 2007` (104065),
  plus census electoral-population layers.
- Per-layer metadata is public and CC BY 4.0; `public_access: download`. The GED 2025
  attribute CSV attachment downloads anonymously (HTTP 200, 4,556 bytes) but carries **no
  geometry**.
- The WFS gateway **accepts `STATS_NZ_API_KEY`** (`services;key=<key>/wfs/` →
  HTTP 200 capabilities, 94,189 bytes; without a key → HTTP 401), but the returned
  capabilities expose no `FeatureType` entries and per-layer WFS paths returned 404/400 in
  this probe. A GeoJSON `GetFeature` download is therefore **not yet proven**.
- Geometry export (`services/api/v1.x/exports/`) requires a **Koordinates account token**,
  which is distinct from the Stats NZ subscription key (HTTP 401 without one).

Receipt: `../evidence/stats-nz-api-capability-20261111.json`.

## Still blocked: legacy OData boundary API

`https://api.stats.govt.nz/opendata/v1/` remains unusable:

- Certificate expired 2026-10-29 (`CN=api.stats.govt.nz`, DigiCert Global G2 TLS RSA
  SHA256 2020 CA1, serial `0A3D6AA25EA768AE270CCA6967BA2D05`).
- With certificate verification bypassed, the gateway answers **HTTP 502**
  (`Microsoft-Azure-Application-Gateway/v2`). Renewal of the certificate alone may not
  restore service.

This host should no longer be the capture target; datafinder is the replacement platform.

## Unblock checklist

1. Obtain a Koordinates account/API token for datafinder if GeoJSON/SHP export is required,
   **or** resolve the per-layer WFS `typeName` with Stats NZ support.
2. Re-probe feature count, byte count, and licence end-to-end.
3. Capture boundary GeoJSON into the repo CAS with per-file receipts.
4. Wire GitHub Actions + GitLab CI keyed off masked `STATS_NZ_API_KEY`; no auditable
   payload may print the key.

Licence: Stats NZ data open under CC BY 4.0. See repo `docs/elections-dataset-card.md`
for the integrator card.
