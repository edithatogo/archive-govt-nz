# Design

```mermaid
flowchart LR
  A[Authenticated target asset] --> B[Outer SHA-256]
  B --> C[Git bundle verify]
  C --> D[Clean isolated clone]
  D --> E[Strict object-graph verification]
  E --> F[Live ref comparison]
  F --> G[Completeness disposition]
  G --> H[README and final-tag candidates]
  G --> I[Preservation-release candidate]
  H --> J{Donor mutation gate}
  I --> K{Release publication gate}
  J --> L[Controlled unarchive update tag rearchive]
  L --> M[Independent archived-state readback]
  K --> N[Independent release and asset readback]
```

The asset response, downloaded bytes, advertised bundle heads, restored Git
graph, live donor refs and required repository files are independent evidence
layers. A successful clone proves restoration of advertised refs; it does not
prove that every live branch and tag was included. Completeness therefore
requires an explicit set comparison.

The donor presentation is prepared as target-owned text. It cannot become a
claim about live donor state until the controlled external sequence and remote
readback occur. The bundle preserves repository history and code licensing; it
does not grant redistribution rights over every source payload referenced by
that history.
