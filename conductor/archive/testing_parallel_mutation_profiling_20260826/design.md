# Design: Testing Modernization and Performance Frontier

## Assurance flow

```mermaid
flowchart LR
    C[Locked configuration] --> M[Mutation runner]
    C --> P[Parallel pytest]
    C --> H[Hypothesis properties]
    C --> S[Scalene profile]
    M --> R[Structured local receipts]
    P --> G[Repository validation]
    H --> G
    S --> R
    R --> G
```

Mutation and profiling are bounded, explicit assurance lanes. They write
derived receipts under `build/`; they do not modify archived originals or
constitute hosted execution, publication, or release evidence.

`pytest-gremlins` configuration lives in `pyproject.toml` so local and CI
invocations share targets and operator policy. Coverage-guided selection stays
enabled by omitting the disabling flag. The configuration permits no pardons;
an exception therefore requires an explicit, reviewed policy change.
