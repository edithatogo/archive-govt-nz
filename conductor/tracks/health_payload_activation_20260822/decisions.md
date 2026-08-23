# Decisions: Health Payload Activation

## DEC-HEALTH-001 — MoH Licence Evidence Acquisition

- **Date raised:** 2026-08-22
- **Status:** PENDING USER SELECTION
- **Blocking scope:** Payload-capture activation for the 158 recorded
  `decision-required` Ministry of Health resources. No other work blocked.

### Context

The deterministic evaluator (`tools/evaluate_health_payload_eligibility.py`)
classifies resources against machine-checkable open-licence evidence. Recorded
snapshots carry no licence fields, so all 158 resources remain honestly
`decision-required`. Activation requires per-dataset licence evidence for the
28 distinct datasets.

### Options presented

1. **Read-only CKAN licence probe tool (Recommended)** — new
   `tools/fetch_health_dataset_licences.py` querying `package_show` read-only
   for the 28 datasets, preserving raw responses, emitting the licence map;
   live query behind explicit flag; GET-fallback per Track 12 precedent
   (`321b8fd`). Reproducible, evidence-first, bounded pacing.
2. **Manual licence lookup** — maintainer supplies the 28-entry mapping from
   the CKAN web UI. Zero code; slow, non-reproducible, no evidence receipts.
3. **Defer activation** — keep honest zero-payload state until harvest cycles
   mature. Zero risk; leaves mechanical activation undone indefinitely.
4. **Rejected:** assuming catalogue-default CC-BY-4.0 without per-dataset
   evidence — would fabricate rights evidence and violate M-02 fail-closed.

### Rationale for recommendation

Read-only source queries are routine reversible engineering under
`autonomy.md`. Reuse-before-create applies via the existing
`BoundedCkanClient` shared POST/GET executor. Every predecessor track is
evidence-first; Option 1 is the only path producing machine-checkable licence
*evidence* rather than claims.

### Contingencies

| Failure | Response |
|---|---|
| Endpoint 400/unavailable | GET-fallback; bounded retries/backoff; diagnostic receipt; retry next cycle; stay fail-closed |
| All licences non-open | Retain honest zero-eligible receipt; close as rights-restricted observation |
| Mixed results | Only explicitly eligible subset proceeds to separately gated capture |
| Rate limited | Bounded pacing; resume next scheduled run |

### Reversibility & uncertainty

Fully reversible — any option writes local evidence only; no capture,
publication, or external state change. Licence distribution across the 28
datasets unknown until probed; some legacy resources may be restricted.

### Safe work while pending

None blocked. Weekly legislation/gazette harvests continue autonomously.

### Resolution

(awaiting user selection — to be recorded here with date and receipt paths)