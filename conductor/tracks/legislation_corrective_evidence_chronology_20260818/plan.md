# Plan: Evidence Correction and Chronology

1. Repair `tools/validate_contracts.py` with `jsonschema.Draft202012Validator`.
2. Harden `tools/evaluate_legislation_completion.py` with real evidence checks.
3. Write automated anti-simulation tests in `tests/tools/test_evaluate_legislation_completion.py`.
4. Invalidate previous `final-adversarial-verification.json` and generate honest incomplete report.
