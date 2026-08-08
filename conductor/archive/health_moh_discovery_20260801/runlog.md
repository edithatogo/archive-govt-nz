# Run log

## 2026-08-08 — bounded handoff

Discovery evidence is stable at 28 datasets and 158 resources. The receipt was
handed to `health_payload_capture_20260802` for resource-level rights and
sensitivity classification. No payload download or publication authorization
was granted.

## 2026-08-01 — metadata-only discovery

- Ran `tools/discover_moh_metadata.py` against the official HTTPS CKAN catalogue.
- Enumerated 28 Ministry of Health datasets and 158 declared resources.
- Ran a bounded second discovery and reconciled identifiers/resource counts.
- Reconciliation was stable; no payloads, credentials, or publication actions occurred.
- Receipts: `evidence/moh-discovery-20260801.json`, `evidence/moh-discovery-20260801-rerun.json`, and `evidence/moh-reconciliation-20260801.json`.
