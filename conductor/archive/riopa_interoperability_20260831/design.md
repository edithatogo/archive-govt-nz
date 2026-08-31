# Design: RIOPA interoperability integration

```mermaid
flowchart LR
  A[Archived receipt] --> B{Digest and revision checks}
  B -->|pass| C[RIOPA source/capture export]
  B -->|fail| Q[Quarantine and retain failure evidence]
  C --> D[Read-only consumer]
  C --> E[Hosted replay evidence]
```

The bridge is archive-only. Rights or legal-status uncertainty is carried as
data and blocks promotion; it is never resolved by the adapter.

Only `captured` receipts with resolved rights and an `observed` or `resolved`
legal-status observation qualify for mapping. Eligibility is not legal clearance,
payload verification, publication or release approval. Other capture/legal states
remain quarantined. All new exports include seven false `claims` flags regardless
of source capability observations, which remain preserved in `boundaries`.

The v1 schema accepts historical exports without `claims`; when present, the
object must include all seven false flags. This preserves existing archived
records while making the boundary explicit for newly generated exports.
