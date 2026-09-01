# Design

```mermaid
flowchart LR
  A[Prerequisite and exact-main checks] -->|all pass| B[No-write preflight]
  B -->|valid seed parent credential and limits| C[Exact 500 dispatch]
  C --> D[Download retained artifacts]
  D --> E[Independent fixity accounting and reconciliation]
  E --> F[Continuation and durable recovery]
  A -->|missing prerequisite| X[Blocked receipt no dispatch]
  B -->|failure| X
```

The current observation follows the blocked path. Evidence records configured credential names only, never values. Static incompatibilities are blockers rather than authority to broaden this issue into Prompts 06 or 10.
