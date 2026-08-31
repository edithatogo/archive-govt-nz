# Verification flow

```mermaid
flowchart LR
 A[Authenticated GitHub metadata and ZIP] --> B[Independent audit pins and ZIP digest]
 B --> C[Bounded safe quarantine extraction]
 C --> D[Roots, identities and every CAS byte]
 D --> E[Receipt and lineage consistency]
 E --> F[Hash-bound Prompt 04 inventory]
 B --> G[Failed mismatch ledger]
 D --> G
 E --> G
```

No network in verifier; no canonical or publication writer. Trusted audit pins plus live metadata are inputs, not values derived from archive contents. Verified ZIP bytes are used directly by the ZIP reader, avoiding a second-open race.
