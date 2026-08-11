# Phase 10 checkpoint

Status: **complete with honest tombstones**

- Deterministic quality gates remain green locally via `./scripts/validate.{sh,ps1}`:
  - `uv lock --check`
  - `ruff format --check`
  - `ruff check`
  - `pyright`
  - `pytest` (333 tests, coverage 96.13%)
  - schema validation
  - mutation (policy + versioning)
  - audit, licences, secret scan, and SBOM
- Reconciliation remains bounded and explicit:
  - 91 resources in scope
  - 12 original source payloads captured
  - 44 DataStore fallbacks captured, including one resource also captured from
    its original source (43 distinct additional resources)
  - 31 authoritative publisher replacements evidenced; payload equivalence is
    not claimed
  - 13 resources gained authoritative rights evidence but their source
    endpoints were not recaptured
  - 1 unavailable resource and 2 rights-restricted resources remain as 3
    explicit tombstones

These are overlapping capture and resolution axes, not mutually exclusive
buckets, and must not be summed as a 91-resource partition.
- Publication references remain reconciled:
  - Zenodo DOI: `10.5281/zenodo.21880266`
  - Hugging Face revision: `50c9e864bd7a9fed39862cf72bd733835f81568a`
- No Track 1 blocker remains. Irrecoverable and rights-restricted records are
  closed outcomes rather than unsupported capture claims.

Linked evidence:
- `evidence/phase-10-final-reconciliation.md`
- `evidence/phase-10-final-reconciliation.json`
- `evidence/archive-evidence-ledger.md`
