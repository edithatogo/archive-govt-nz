# Design

```mermaid
flowchart LR
  D[Exact donor checkout] --> B[68 batch verifier]
  T[Target state receipts] --> A[Population analyzer]
  H[Public HF and Zenodo observations] --> A
  B --> A
  A --> J[Coverage JSON]
  A --> M[Decision report]
  A --> C[Prompt 17 correction manifest]
```

Counts carry population type, observation status and hash-bound evidence. Identity sets are unioned rather than arithmetically summed. Missing acquisition or publication evidence remains unknown and does not imply absence.
