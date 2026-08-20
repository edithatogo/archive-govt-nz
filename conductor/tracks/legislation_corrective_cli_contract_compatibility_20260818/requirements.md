# Requirements: Truthful CLI Contract and Non-Affirmative State Compatibility

Track: `legislation_corrective_cli_contract_compatibility_20260818`  
Parent: `legislation_corpus_consolidation_corrective_20260818`  
Linked Issue: [#135](https://github.com/edithatogo/archive-govt-nz/issues/135)

## MoSCoW Requirements

### Must
1. **Truthful, Evidence-Driven Non-Legislation CLI Commands**:
   - Eliminate fictitious queue status in `capture`.
   - Eliminate unconditional verified archive status in `archive`.
   - Eliminate unconditional replay fixity success in `replay`.
   - Eliminate hardcoded 19 integrity checks in `verify`.
   - Eliminate fixed 350 entities count in `provenance`.
   - Eliminate unconditional publication readiness in `publish`.
   - Eliminate unconditional healthy status in `doctor`.
   - Execute real backend operations where available, or return precise non-success states (`not_configured`, `unsupported`, `no_state`, `not_found`).
2. **Static Capability Catalogue**:
   - `capabilities` command must report compiled engine capabilities with status `compiled` without claiming hosted or operational verification.
3. **Contractual Output and Exit Code Taxonomy**:
   - Structured JSON and human-readable text on `stdout`.
   - Warning and failure diagnostics on `stderr`.
   - Exit codes strictly within 0–5 (0: Success, 1: No State / Unverified, 2: Not Configured / Missing Configuration, 3: Not Found / Missing Resource, 4: Validation Error, 5: Unsupported).
   - Never leak secrets, tokens, or private keys.
   - Never report affirmative success without verified evidence.
4. **Negative Controls**:
   - Explicit negative assertions for absent CAS directories, absent provenance ledgers, absent sources, and unconfigured publication credentials.
