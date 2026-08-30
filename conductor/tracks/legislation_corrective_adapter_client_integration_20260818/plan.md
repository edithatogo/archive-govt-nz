# Plan: Adapter and Client Transport Integration

1. **Phase 1: Async Client Implementation**
   - Implement `NZLegislationApiClient` with pacing, retries, and conditional headers.
2. **Phase 2: Adapter In-Place Upgrade**
   - Upgrade `NZLegislationAdapter` to delegate network transport to `NZLegislationApiClient`.
3. **Phase 3: Automated Coverage & Transport Verification**
   - Characterize 429 backoff, rate limiting, and CAS dual-hash persistence in `tests/adapters/test_nz_legislation.py`.


## 2026-08-30 record preservation

- [x] Preserve the original historical plan verbatim in [plan.original.md](plan.original.md) and record its hash.

The checkbox above records preservation only. Original phase prose has no individual task checkmarks; this reconciliation does not assert or reverify its historical completion. Existing completion claims remain attributable to the original record.
