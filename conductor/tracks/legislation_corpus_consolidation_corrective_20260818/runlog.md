# Run Log: Corrective Programme

## 2026-08-18 / 2026-08-19: Contract Validator and Evaluator Hardening
- Repaired `tools/validate_contracts.py` with `jsonschema.Draft202012Validator`, command allowlist, track reference validation, and timestamp checks.
- Hardened `tools/evaluate_legislation_completion.py` to scan for fixed constants, evaluate active donor issues, verify hosted readback tokens, check child track states, and emit honest blockers with non-zero exit code.
- Verified that evaluator exits 1 with `INCOMPLETE` state.
