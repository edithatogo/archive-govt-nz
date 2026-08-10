# Phase 10 checkpoint

Status: **partially complete (external gates remain open)**

- Deterministic quality gates remain green locally via `./scripts/validate.{sh,ps1}`:
  - `uv lock --check`
  - `ruff format --check`
  - `ruff check`
  - `pyright`
  - `pytest` (255 tests, coverage 95.34%)
  - schema validation
  - mutation (policy + versioning)
  - audit, licences, secret scan, and SBOM
- Reconciliation remains bounded and explicit:
  - 91 discovered / 91 resolved
  - 12 captured
  - 78 restricted
  - 1 unavailable
  - 79 tombstones
- Publication references remain reconciled:
  - Zenodo DOI: `10.5281/zenodo.21728726`
  - Hugging Face revision: `9406a3b0f877f0251c1baf89665cacc0c30dbae0`
- Confirmed explicitly unresolved/blocked requirements:
  - complete eligible payload capture under policy
  - external publication state transitions above local acceptance
  - clean-environment rerun in a fresh workspace (not yet claimed here)

Linked evidence:
- `evidence/phase-10-final-reconciliation.md`
- `evidence/phase-10-final-reconciliation.json`
- `evidence/archive-evidence-ledger.md`
