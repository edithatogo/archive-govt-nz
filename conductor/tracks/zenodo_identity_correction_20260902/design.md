# Design

```mermaid
flowchart LR
  V[Live immutable version record] --> R[Superseding readback receipt]
  C[Concept identity] --> R
  S[Target state and lineage] --> T[Typed future metadata template]
  R --> G[Corrected registry and source contracts]
  T --> O{Operation state}
  O -->|prepare| P[Local candidate]
  O -->|update draft| D[Remote draft receipt required]
  O -->|publish| X[Explicit gate and returned DOI required]
```

Historical records remain unchanged. Current contracts point to the correct concept and version identities; any future publication claim requires a remote receipt rather than a locally supplied DOI.
