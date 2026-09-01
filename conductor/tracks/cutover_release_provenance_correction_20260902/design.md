# Design

The correction is additive. A deterministic renderer authenticates the observed
release and repository attestation, then appends one dated addendum. The public
release is edited once under Prompt 18 authority and independently read back.

```mermaid
flowchart LR
  GH[GitHub release, runs, jobs, artifacts, issue 142] --> V[Fail-closed verifier]
  A[Hash-bound repository attestation] --> V
  V --> D[Local dated addendum]
  D --> P[Authorised release-body edit]
  P --> R[Independent release GET]
  R --> E[Machine correction receipt]
  E --> T[Schema, tests, mutation and hosted checks]
```

Trust boundaries:

- hosted responses are observed evidence and are hash-bound before mutation;
- the attestation is authoritative only at its exact repository path and hash;
- local preparation cannot set `applied_readback_verified`;
- remote success requires a post-write GET matching release ID, tag, tag commit,
  corrected addendum, and unchanged cycle 2 chain;
- the historical release tag, assets, issue comments, attestation, and receipts
  remain unchanged.
