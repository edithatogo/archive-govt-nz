# Plan: Evidence Correction and Chronology

1. Repair `tools/validate_contracts.py` with `jsonschema.Draft202012Validator`.
2. Harden `tools/evaluate_legislation_completion.py` with real evidence checks.
3. Write automated anti-simulation tests in `tests/tools/test_evaluate_legislation_completion.py`.
4. Invalidate previous `final-adversarial-verification.json` and generate honest incomplete report.


## 2026-08-30 record preservation

- [x] Preserve the original historical plan verbatim in [plan.original.md](plan.original.md) and record its hash.

The checkbox above records preservation only. Original phase prose has no individual task checkmarks; this reconciliation does not assert or reverify its historical completion. Existing completion claims remain attributable to the original record.
