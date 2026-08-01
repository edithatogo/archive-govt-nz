# Design

```mermaid
flowchart LR
  Q[Versioned queries and facets] --> C[CKAN Action API]
  C --> R[Bounded raw responses]
  R --> N[Normalize and deduplicate]
  N --> K[Health relevance and rights classification]
  K --> E[JSON/Markdown evidence ledger]
  K --> F[Follow-up candidates]
  E --> V[Deterministic rerun reconciliation]
  F -. gated handoff .-> P[Future capture track]
```

All network access is read-only metadata discovery. Raw responses are retained
only within the configured response limit and are linked by SHA-256. A stable
dataset identifier is the deduplication key; query provenance remains separate
so overlapping searches are auditable.
