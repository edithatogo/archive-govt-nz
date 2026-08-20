# Operations Runbook: `archive-govt-nz`

This runbook describes the currently supported local global-CLI operations and
their evidence boundaries. It does not authorize remote publication or claim
that the scheduled multi-source workflow is operational.

## Current operational status

- Global `capture` is fail-closed as `not_configured` with exit code 2 because
  no standalone daemon or worker queue is connected.
- `.github/workflows/scheduled-multi-source-harvest.yml` exists, but its capture,
  archive-manifest, and replay-state wiring belongs to the later workflow track.
  Do not interpret a dispatch or workflow result as capture completeness.
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

The scheduled workflow has a six-hour cron declaration, but it is not a valid
production-harvest route in the current sequence. Its generic capture command
returns `not_configured`, archive verification requires a closed fixity
manifest, and replay requires populated production-layout CAS state.

Use this probe only to confirm the fail-closed boundary:

```bash
uv run --locked archive-govt-nz capture \
  --source-type feed \
  --format json
# Expected: status=not_configured and exit code 2.
```

Do not trigger the scheduled workflow as a production harvest until its later
corrective track supplies real acquisition, manifest, checkpoint, and replay
state and a bounded live run verifies them.

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
