# Design

```mermaid
flowchart TD
  F[Deterministic fixture corpus] --> R[RO-Crate evaluation]
  F --> B[BagIt evaluation]
  F --> O[OCFL evaluation]
  R --> V[Independent or reference validators]
  B --> V
  O --> V
  V --> E[JSON and Markdown evidence]
  E --> D{Adoption decision}
  D -->|Evidence sufficient| A[Bounded adoption recommendation]
  D -->|Evidence insufficient| X[Defer; retain current formats]
```

The fixture corpus contains raw metadata, one small source object, a tombstone,
checksums, provenance, and a redacted transaction receipt. Each evaluator must
be deterministic, preserve the original bytes, and emit an explicit unavailable
or partial result when a validator cannot run.
