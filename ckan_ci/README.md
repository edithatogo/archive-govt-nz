# Stats NZ API — capability status (updated 2026-11-11)

Scope: track the Stats NZ API access needed by the election archive, and document what
is proven working versus still blocked. This file is an engineering note, not an artifact.

## Credential

- `STATS_NZ_API_KEY` — Stats NZ API Portal subscription key.
- Sent as the HTTP header `Ocp-Apim-Subscription-Key`.
- Stored only in the repo-local `.env`, which is gitignored (`.gitignore:16`). The value is
  never committed, logged, or copied into evidence. `.env.example` documents the variable.
- CI, when enabled, must inject it as a masked CI variable of the same name.

## Proven working: Aotearoa Data Explorer SDMX API

- Base URL: `https://api.data.stats.govt.nz/rest/`
- TLS valid at probe time (`CN=api.data.stats.govt.nz`, Google Trust Services, notAfter
  2026-12-14).
- Unauthenticated data request → **HTTP 401** (`Access denied due to missing subscription
  key`).
- Keyed data request → **HTTP 200** `text/csv` (verified slice:
  `data/STATSNZ,AGR_AGR_001,1.0/all?firstNObservations=2`, 47,360 bytes).
- Structure catalogue (`dataflow/STATSNZ/all?detail=allstubs`) is public and returns
  **HTTP 200** XML (654,591 bytes, NSI Web Service v8.19.7.0).

Receipt: `../evidence/stats-nz-api-capability-20261111.json`.

## Still blocked: OData boundary geodata

`https://api.stats.govt.nz/opendata/v1/` remains unusable:

- Certificate expired 2026-10-29 (`CN=api.stats.govt.nz`, DigiCert Global G2 TLS RSA
  SHA256 2020 CA1, serial `0A3D6AA25EA768AE270CCA6967BA2D05`).
- With certificate verification bypassed, the gateway answers **HTTP 502**
  (`Microsoft-Azure-Application-Gateway/v2`). Renewal of the certificate alone may not
  restore service.

Therefore no boundary-extractor CI is committed here yet: the endpoint cannot authenticate
successfully, and this directory will not ship a code path that claims otherwise.

## Unblock checklist

1. Stats NZ restores `api.stats.govt.nz` (renewed certificate **and** a working gateway).
2. Re-probe metadata page, feature count, and byte count end-to-end.
3. Capture boundary GeoJSON into the repo CAS with per-file receipts.
4. Wire GitHub Actions + GitLab CI keyed off masked `STATS_NZ_API_KEY`; no auditable
   payload may print the key.

Licence: Stats NZ data open under CC BY 4.0. See repo `docs/elections-dataset-card.md`
for the integrator card.
