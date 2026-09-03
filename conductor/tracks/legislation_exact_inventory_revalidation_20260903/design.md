# Design

```mermaid
flowchart LR
  D[Confirmed manual dispatch] --> S[Resolve seed registry ID]
  S --> P[Prompt 08 quarantine restore]
  P -->|verified| A[Force 500 source revalidations]
  P -->|failure| F[Retain sanitized failure]
  A --> R[Reconcile IDs, roots, CAS and v3 accounting]
  R --> B[Enforce resource bounds]
  B --> C[Seal continuation lineage]
  C --> O[Retain complete state and receipts]
  A -->|partial or failure| F
```

Only acquisition receives the optional source credential. The parent reference
and stable seed ID form the pre-network trust boundary. Exact-inventory and the
existing discovery writer share one repository concurrency key.
