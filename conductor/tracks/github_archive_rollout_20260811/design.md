# Design

The current repository supplies the source-neutral architecture profile. The
target repository receives a compatibility assessment first; only a reviewed,
repository-specific patch may cross the external-repository boundary.

```mermaid
flowchart LR
    Profile[Canonical architecture profile] --> Review[Target trust-boundary review]
    Review --> Decision{Compatible and authorised?}
    Decision -->|no| Hold[Record gate and stop]
    Decision -->|yes| Patch[Prepare target-specific patch]
    Patch --> Checks[Target checks and hosted evidence]
    Checks --> Merge[Owner-approved merge]
```
