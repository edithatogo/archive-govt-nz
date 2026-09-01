# Design

```mermaid
flowchart LR
  H[Immutable historical artefacts] --> I[Typed evidence index]
  N[Canonical Prompt 02-16 evidence] --> I
  I --> V{Active evaluator validator}
  V -->|eligible active proof| C[Four-dimension closeout]
  V -->|invalidated or unresolved| F[Fail closed]
  C --> S[Superseding corrected closeout]
```

The index records classification, content hash, scope, claim dimensions, and supersession links. Historical bytes stay unchanged. Active evaluator inputs may cite only eligible evidence and cannot infer completion from issue, PR, workflow, or CI state alone.
