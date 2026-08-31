# Design

```mermaid
flowchart LR
  Pins[Reviewed parent reference] --> Meta[Live identity and expiry checks]
  Meta --> Q[Bounded quarantine download]
  Q --> Zip[Digest and safe ZIP verification]
  Zip --> State[Manifest checkpoint CAS and receipt verification]
  State --> Lineage[Write parent lineage before acquisition]
  Authority[Separate bootstrap authority] --> Lineage
  Lineage --> Promote[Exclusive state promotion]
  Promote --> Acquire[Existing caller acquisition]
  Acquire --> Seal[Verify and seal complete continuation]
```

Any failure stops before promotion/acquisition and retains a sanitized failure receipt. Incoming receipt bytes remain content-addressed history. Remote storage and publication are outside this interface.
