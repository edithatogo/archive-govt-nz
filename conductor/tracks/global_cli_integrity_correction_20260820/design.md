# Design

```mermaid
flowchart LR
  CLI[Global CLI] --> CAS[ContentAddressedStore verifier]
  CLI --> ARC[WARC and WACZ validators]
  CLI --> PROV[Closed provenance validator]
  CLI --> IDX[Scope manifest to semantic index]
  CLI --> PUB[Publication preparation backend]
  PUB --> GATE[Rights and publication authority remain pending]
```

Each command delegates to an existing domain backend or a bounded validator.
Filesystem presence, filenames, empty directories, and credential presence are
observations rather than proof. Validation failures are structured and
fail-closed. Remote publication is not performed by this track.
