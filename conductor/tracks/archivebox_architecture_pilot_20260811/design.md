# Design

```mermaid
flowchart LR
    Discovery["CKAN and publisher discovery"] --> Bounded["Bounded deterministic retrieval"]
    Bounded --> Objects["Content-addressed objects"]
    Bounded --> IA["Internet Archive triangulation"]

    Exceptions["Selected unresolved pages"] --> ArchiveBox["Isolated ArchiveBox pilot"]
    Exceptions --> Browser["Manual Chrome or browser-agent inspection"]

    ArchiveBox --> Admission["Existing hashing, rights and validation gates"]
    Browser --> Candidates["Candidate URLs only"]
    Candidates --> Bounded
    Admission --> Objects

    Objects --> HF["Rolling Hugging Face archive"]
    HF --> Zenodo["Gated immutable Zenodo releases"]
```

```mermaid
flowchart TB
    Config["Reviewed HTTPS pilot configuration"] --> Validate["Python policy validation"]
    Validate -->|"accepted, max 5"| Container["ArchiveBox image pinned by digest"]
    Validate -->|"rejected"| Closed["Fail-closed receipt"]
    Container --> Output["HTML, WARC, screenshot and metadata outputs"]
    Output --> Inventory["Bounded inventory and SHA-256 receipt"]
    Inventory --> Artefact["30-day GitHub Actions artefact"]
    Inventory --> Gate["Future durable admission decision"]
```

ArchiveBox is an isolated producer of secondary representations. The Python
policy layer owns input admission and receipt semantics. Existing archive gates
own durable object admission. GitHub Actions storage is not durable preservation.

The canonical reusable diagram and explanatory profile live at
`docs/archive-system-architecture.md`; publication systems copy or package that
file rather than maintaining divergent diagrams.
