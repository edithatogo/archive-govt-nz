# 07_solo_harness — Must acceptance specification

## Scope
Ruff ALL, basedpyright all-mode ratchet, Python3.15 uv lock, Polars, pytest/Hypothesis/gremlins/Scalene, differential tests, CodeQL, Presidio/Gitleaks and release attestations.

## Completion conditions
Exact-head CI green; broad ignores ratcheted; tools pinned; measured mutation/profile budgets; no required multi-person approvals.

## Research and release contract
Observed, derived, estimated, counterfactual and experimental results must be distinguishable. Every output binds to source-vintage, software revision, model assumptions and hash. Single developer automation rather than reviewer bureaucracy. No green gate or source provenance may be inferred from a committed plan.
