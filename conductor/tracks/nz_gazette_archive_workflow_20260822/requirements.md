# Requirements: NZ Gazette Archive Workflow (MoSCoW)

## Must

- **M-01**: A deterministic gazette harvest orchestrator (`tools/run_gazette_harvest.py`)
  validates the source-set config, audits credential presence safely, restores and
  atomically promotes checkpoints, and classifies outcomes as `changed`,
  `no_change`, `partial_retryable`, or `failed` with exit codes 0/1.
- **M-02**: Discovery produces typed notice identities against official Gazette
  endpoints with bounded requests; no regex-based HTML parsing.
- **M-03**: Normalisation converts captured raw payloads into schema-conforming
  `GazetteRecord` dicts matching `schemas/gazette/v1/gazette-record.schema.json`
  with no blind defaults; unknown values remain explicit.
- **M-04**: Validation enforces required fields, hash format, URI scheme, year
  bounds, and timestamp chronology (no future-dated retrieval timestamps).
- **M-05**: A scheduled CI workflow (`.github/workflows/scheduled-gazette-harvest.yml`)
  runs the orchestrator with pinned action SHAs, uploads receipts, and passes
  publication readback in read-only mode.
- **M-06**: Focused test suite achieves >=95% patch coverage on the orchestrator
  with negative controls for invalid config, disabled source-set, sync failure,
  validation failure, and CLI entrypoint.

## Should

- **S-01**: Checkpoint schema versioned as `archive-govt-nz.gazette-checkpoint/v1`.
- **S-02**: Harvest receipt records processed notice IDs and promotion state.

## Could

- **C-01**: Cross-source reconciliation report generation wired into the orchestrator.

## Won't (this track)

- Historical Victoria/LexisNexis gazette sources (deferred by registry gate).
- Remote publication writes (publication remains gated).
- Modification of the existing `NZGazetteAdapter` transport contract beyond reuse.