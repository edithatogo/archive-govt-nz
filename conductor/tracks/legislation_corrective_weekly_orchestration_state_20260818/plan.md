# Plan: Weekly Legislation Orchestration and State Management

1. **Phase 1: Source-Set Configuration & Workflow Safety**
   - Verify `config/source-sets/legislation.yml` and `.github/workflows/scheduled-legislation-harvest.yml`.
   - Ensure action pin SHAs and security policy contracts are satisfied.
2. **Phase 2: Real Harvest Orchestrator Script**
   - Implement `tools/run_legislation_harvest.py` supporting configuration validation, safe credential check, checkpoint restore/promotion, incremental sync, validation gate, and structured outcome classification (`changed`, `no_change`, `partial_retryable`, `failed`).
3. **Phase 3: Automated Unit & Workflow Policy Testing**
   - Implement test suite in `tests/tools/test_run_legislation_harvest.py` testing all outcomes and negative controls.
4. **Phase 4: Full 19-Stage Gate & Evidence Generation**
   - Run `tools/check.py`, verify >=95% patch coverage, and record evidence receipts.
