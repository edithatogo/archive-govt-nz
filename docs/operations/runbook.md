# Operations Runbook: `archive-govt-nz`

This runbook outlines day-to-day operations, credential management, harvesting workflows, and troubleshooting procedures for `archive-govt-nz`.

---

## 1. Required Credentials & Repository Secrets

All repository secrets are referenced strictly by environment variable name:

| Secret Name | Scope | Purpose |
|---|---|---|
| `HF_TOKEN` | Repository Secret | Authenticates Git LFS push to Hugging Face datasets. |
| `ZENODO_TOKEN` | Repository Secret | Authorizes REST API deposition upload and DOI minting. |
| `BLUESKY_APP_PASSWORD` | Repository Secret | Optional authenticated AT Protocol rate-limit expansion. |
| `YOUTUBE_API_KEY` | Repository Secret | Google Cloud Data API v3 quota access for video metadata. |
| `HARVEST_WEBHOOK_URL` | Repository Secret | Optional Slack/Discord alert webhook for harvest anomalies. |

---

## 2. Routine Ingestion & Harvesting

Harvesting runs autonomously on a 6-hour cron via `.github/workflows/scheduled-multi-source-harvest.yml`.

### Triggering Manual Harvest
```bash
# Harvest specific source set locally
archive-govt-nz capture --source-type feed

# Harvest full social media source set
archive-govt-nz capture --source-type bluesky
```

---

## 3. Maintenance & Health Diagnosis

```bash
# Run integrity and environment audit
archive-govt-nz doctor

# Validate all registered seeds
archive-govt-nz sources --format json

# Execute zero-network replay verification
archive-govt-nz replay --verify-all
```

---

## 4. Troubleshooting Common Issues

- **Rate Limiting on Social APIs**:
  - The adapter automatically applies exponential backoff up to 30 seconds.
  - If exhaustion persists, the circuit breaker safely defers remaining tasks to the next scheduled harvest cycle.
- **Malformed Upstream XML/RSS Feed**:
  - The feed adapter parses defensively, capturing raw bytes in quarantine CAS before logging a structured schema warning.
