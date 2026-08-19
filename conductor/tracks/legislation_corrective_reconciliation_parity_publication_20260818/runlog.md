# Run Log: Historical Reconciliation, Parity, and Publication Identity

- **2026-08-18T12:54:00Z**: Initialized corrective child track.
- **2026-08-18T23:50:00Z**: Updated acceptance contract and MoSCoW requirements in Commit A.
- **2026-08-19T00:52:00Z**:
  - Upgraded `tools/generate_executable_legislation_parity.py` to use real API client network observations for smoke testing.
  - Executed differential parity suite generating receipts under `evidence/migrations/corpus-legislation-nz/parity/`:
    - `fixture-parity.json`
    - `historical-batch-parity.json`
    - `live-smoke-parity.json`
    - `publication-package-parity.json`
    - `aggregate-parity.json`
  - Validated external identity preservation and publication package staging.
  - Verified remote publication readback gating is enforced.
