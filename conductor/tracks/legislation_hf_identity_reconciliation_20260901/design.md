# Design

```mermaid
flowchart LR
  L[Live exact-revision observations] --> V[Fail-closed verifier]
  S[Verified target state and coverage] --> R[Typed three-identity registry]
  V --> R
  R --> C[Canonical card candidate]
  R --> M[Monthly canonical reconciliation]
  C --> G{Explicit publication gate}
  G -->|pending| K[Immutable candidate and checklist]
  G -->|authorized| P[Existing canonical identity only]
  P --> B[Independent exact-revision readback]
```

Every remote statement is revision-bound. Registry roles are unique, coverage populations remain distinct, and rights describe source-specific evidence rather than a repository-wide licence.
