# Requirements: Corrective Legislation Corpus Consolidation

## Core Invariants & Anti-Simulation Rules
- **Contract-First Validation**: Every YAML contract must strictly validate against `schemas/contracts/v1/contract.schema.json`.
- **Honest Completion Evaluation**: The completion evaluator (`tools/evaluate_legislation_completion.py`) must evaluate real evidence and exit non-zero reporting `INCOMPLETE` as long as production defects, fixed constants, or open gates exist.
- **No Simulation**: Completion cannot be inferred from file or directory existence.
