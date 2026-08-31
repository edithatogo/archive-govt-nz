# Design

```mermaid
flowchart LR
 D[Donor ZIP + Prompt 03 pins] --> V[Independent parent verification]
 T[Latest target ZIP + GitHub pins] --> V
 V --> U[Sorted identity union + CAS deduplication]
 U -->|conflict| F[Failure ledger, no complete marker]
 U -->|unambiguous| O[Exclusive local state + full parents + receipt]
```

Same manifestation with changed bytes or metadata blocks without selecting a winner. Versions remain linked by work and expression. Conditional request caches reset for unconditional revalidation; parent originals remain retained. Canonical content is idempotent; execution lineage and completion inventory bind each run separately.
