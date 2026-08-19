# Requirements: Real Legislation CLI Service Integration and nzlc Compatibility

Track: `legislation_corrective_cli_contract_compatibility_20260818`  
Parent: `legislation_corpus_consolidation_corrective_20260818`  
Linked Issue: [#135](https://github.com/edithatogo/archive-govt-nz/issues/135)

## MoSCoW Requirements

### Must
1. **Application Service Integration Across All 11 Actions**:
   - Connect `legislation` CLI commands directly to `LegislationArchiveService` and domain backends:
     - `discover`: queries API client / discovery inventory for candidate works.
     - `sync`: runs bounded resumable sync pipeline (`sync_works`), supporting partial retry and atomic checkpoint promotion.
     - `validate`: validates records and manifest against v2 FRBR schema.
     - `manifest`: generates or inspects manifest without simulated counts.
     - `coverage`: dynamically calculates coverage from observed records/manifest; removes 33,693 and 100% constants.
     - `changes`: detects expression-level and feed modifications.
     - `status`: inspects CAS store, checkpoints, and manifest existence.
     - `replay`: executes zero-network deterministic CAS replay drill.
     - `publication-plan`: builds deterministic artifact plan for HF/Zenodo.
     - `publication-verify`: verifies remote publication readback or reports unconfigured tokens.
     - `doctor`: evaluates live API connectivity and storage health.
2. **Forbidden Hardcoded States**:
   - Remove 33,693 fixed counts, 68-batch fixed counts, 100% fixed coverage, and unconditional affirmative states.
   - Manifest alterations must dynamically alter output counts.
3. **Capture Redirection**:
   - `capture --source-type legislation` rejects invocation and directs users to `legislation sync`.
4. **`nzlc` Legacy Compatibility Parity**:
   - `compat_nzlc_main` preserves supported legacy arguments and maps to the real service with stderr deprecation warning.
5. **Contractual Output and Exit Code Taxonomy**:
   - Structured JSON on stdout, diagnostics on stderr.
   - Exit codes strictly within 0–5.
