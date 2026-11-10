# Stats NZ OData boundary geodata CI (provisioned as an engineering note, 2026-11-10)

Scope: document and formalize an inventory-level scaffold for an automated
extractor of Stats NZ OData boundary layers, triggered nightly from GitHub
Actions and GitLab CI, led by `STATS_NZ_ODATA_API_KEY` held as a **CI variable**
and never committed.

Current state (2026-11-10): **NOT operational. This file is an engineering note,
not an artifact.**

* Stats NZ TLS certificate for api.stats.govt.nz expired 2026-10-29 (subject
  api.stats.govt.nz; issuer DigiCert Global G2 TLS RSA SHA256 2020 CA1). TLS
  handshake is refused today, so even a valid key would not authenticate.
* 16-layer candidate enumeration from earlier recon is NOT independently
  verified; it is an inventory-only guess, not bytes.
* Before CI can pull data it must be verified end-to-end (metadata page,
  feature count, byte count) against a live endpoint with a valid
  certificate.

Deliverables deferred to a follow-up track, to be opened only when the
certificate is renewed and the key is provided by the repository owner:

1. Verify licence headers, manifest enumeration and licensing post cert
   renewal.
2. Capture boundary GeoJSON within the repo CAS.
3. Wire working GitHub Actions + GitLab CI entries keyed off
   ci-secret-only key material; no auditable payload ever prints the key.

Licence: Stats NZ data open under CC BY 4.0. See repo `docs/elections-dataset-card.md` for integrator card.

This directory deliberately contains no scripts that claim to fetch data —
the endpoint is unusable today, and we will not commit code paths that do not
already authenticate successfully.
