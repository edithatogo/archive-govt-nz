# Operations Runbook: `archive-govt-nz`

This runbook describes the currently supported local global-CLI operations and
their evidence boundaries. It does not authorize remote publication or claim
that the scheduled multi-source workflow is operational.

## Current operational status

- Global `capture --source-type <name>` performs bounded network acquisition
  against the declared source sets in `config/source-sets/` and writes WARC
  evidence plus content-addressed capture receipts. Undeclared source sets
  remain fail-closed as `not_configured` with exit code 2.
- `.github/workflows/scheduled-multi-source-harvest.yml` runs capture,
  fixity manifest, verification, and complete CAS/WARC/receipt retention for
  90 days. The recurring default is `government-web`; other sets are manual.
  A green run evidences bounded acquisition only; it is not publication or
  redistribution authorization.
- Publication preparation is local-only. Credentials are capabilities, not
  rights clearance, package integrity, remote verification, or release evidence.

---

## 1. Required Credentials & Repository Secrets

All repository secrets are referenced strictly by environment variable name:

| Secret Name | Scope | Purpose |
|---|---|---|
| `HF_TOKEN` | Repository Secret | Credential capability for separately authorized Hugging Face operations. |
| `ZENODO_TOKEN` | Repository Secret | Credential capability for separately authorized Zenodo operations. |
| `HARVEST_WEBHOOK_URL` | Repository Secret | Optional notification destination used by the notification tool. |

Never print or commit secret values. Token presence does not make a publication
package ready and does not close publication or redistribution-rights gates.

---

## 2. Capture and workflow boundary

The scheduled workflow captures the configured government web targets every six
hours. Capture writes CAS originals and WARC records; fixity and replay run
before the complete recovery bundle uploads as an artifact. Download
`harvest-receipts-government-web` from the selected run, then verify its
`cas/government-web` and `warc/government-web` directories with the commands
below. Artifact retention is 90 days and is not permanent public preservation.

Treasury website capture is held after HTTP 403; metadata discovery uses the
separate public CKAN GET route locally. GitHub runners receive an HTML challenge
from the catalogue; `scheduled-discovery.yml` and
`scheduled-health-discovery.yml` are disabled until that access is resolved.
The existing local commands remain available:

```bash
.venv/bin/python tools/live_treasury_discovery.py --output-dir build/live/treasury --page-size 25
.venv/bin/python tools/discover_health_metadata.py --output build/live/health-discovery.json --page-size 100
```

Legislation needs its existing
`LEGISLATION_API_KEY` renewed after HTTP 401. Gazette has no discovery seed, so
its empty recurring job is deferred; social-media/newsletter setup and broader
publication are on the [roadmap](../roadmap.md). Do not retry unchanged access
failures. Parliament uses its existing hosted fenced workflow, one recent batch
per hour, and finishes retained work before new acquisition.

Use this probe only to confirm the fail-closed boundary for an undeclared
source set:

```bash
uv run --locked archive-govt-nz capture \
  --source-type feed \
  --format json
# Expected: status=not_configured and exit code 2.
```

A bounded live dispatch verified real acquisition on 2026-08-26 (run
32950524898; treasury captured 255,838 bytes, fixity verified). Treat any new
source-set enablement as requiring its own evidence gate.

---

## 3. Maintenance & Health Diagnosis

```bash
# Check the declared Python runtime only
uv run --locked archive-govt-nz doctor --format json

# Observe configured seed files (not discovery completeness)
uv run --locked archive-govt-nz sources --format json

# Stream-verify a populated production-layout CAS
uv run --locked archive-govt-nz replay \
  --cas-dir build/cas \
  --format json

# Verify WARC/WACZ structure and a closed fixity manifest
uv run --locked archive-govt-nz archive \
  --action verify \
  --output-dir build/warc \
  --manifest-path build/warc/manifest.json \
  --format json

# Verify CAS, JSON Schemas, provenance, and runtime together
uv run --locked archive-govt-nz verify \
  --cas-dir build/cas \
  --schemas-dir schemas \
  --provenance-path evidence/archive-evidence-ledger.json \
  --format json
```

Missing state and failed verification return non-zero. Preserve stderr and the
JSON receipt separately when collecting bounded evidence.

---

## 4. Troubleshooting Common Issues

- **`capture` returns `not_configured`**: This is the expected global CLI state,
  not a transient source failure. Use the applicable domain runner only after
  its track and runbook authorize operation.
- **`archive` returns `failed`**: Inspect the structured failure list. A matching
  filename or digest alone does not establish valid WARC/WACZ structure.
- **`replay` returns `no_state`**: Populate the CAS through
  `ContentAddressedStore`; flat files under `sha256/` are not valid store state.
- **`publish` returns `blocked_by_rights`**: Resolve the accountable rights gate.
  Do not change a manifest boolean or add a token as a substitute for clearance.
