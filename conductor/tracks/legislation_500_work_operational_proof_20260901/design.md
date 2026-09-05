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

The superseding observation follows the successful path. Standalone preflight
33968519628 precedes full run 33968609350; both use the reviewed source-preflight
correction on main. Independent readback verifies the artifact digests, state,
accounting and continuation. Earlier blocked and failed observations remain
historical evidence. Credential values are never recorded. The approved durable
552-record parent and retained 904-record output have distinct custody scopes.
