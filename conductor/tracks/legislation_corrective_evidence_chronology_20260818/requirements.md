# Requirements: Evidence Correction and Chronology

## Objectives
- Enforce strict JSON Schema validation for contracts using `schemas/contracts/v1/contract.schema.json`.
- Enforce evidence timestamp chronology and reject future-dated timestamps.
- Validate that evidence destinations exist and acceptance commands are within the allowlist.
- Ensure the completion evaluator reports `INCOMPLETE` with non-zero exit code when evidence indicates incomplete or simulated state.
