# Project Design

## Architectural intent

Archive Govt NZ separates source observation, immutable preservation,
reproducible derivation, and external publication. The preservation truth is the
combination of original objects, versioned manifests, and auditable evidence;
operational databases and search indexes remain reconstructable.

## System context

```mermaid
flowchart LR
    subgraph Sources["Government data sources"]
        CKAN["data.govt.nz CKAN API"]
        Files["Publisher resource URLs"]
        Other["Complementary non-CKAN sources"]
    end

    subgraph Archive["Archive Govt NZ"]
        Discover["Discovery and scope reconciliation"]
        Capture["Bounded streaming capture"]
        CAS["Content-addressed original objects"]
        Ledger["SQLite operational ledger"]
        Manifest["Versioned manifests and evidence"]
        Transform["Transparent transformations"]
        Tabular["Parquet and JSONL derivatives"]
        Graph["Optional graph projections"]
        Vector["Optional vector projections"]
        Verify["Integrity and recovery verification"]
    end

    subgraph Publication["External publication"]
        GitHub["GitHub source and compact evidence"]
        HF["Rolling Hugging Face datasets"]
        Zenodo["Immutable Zenodo releases"]
    end

    CKAN --> Discover
    Other --> Discover
    Discover --> Capture
    Files --> Capture
    Capture --> CAS
    Capture --> Ledger
    Capture --> Manifest
    CAS --> Transform
    Manifest --> Transform
    Transform --> Tabular
    Tabular --> Graph
    Tabular --> Vector
    CAS --> Verify
    Manifest --> Verify
    Ledger --> Verify
    Verify --> GitHub
    Verify --> HF
    HF --> Zenodo
    Manifest --> GitHub
```

The optional graph and vector projections are downstream of validated tabular
derivatives. They cannot overwrite originals, manifests, or publication state.

## Autonomous delivery control

```mermaid
stateDiagram-v2
    [*] --> Reconcile
    Reconcile --> Execute: next safe task
    Execute --> Verify
    Verify --> Recover: check fails
    Recover --> Execute: changed hypothesis within budget
    Recover --> IndependentWork: affected branch blocked
    Verify --> Commit: evidence passes
    Commit --> Checkpoint: phase complete
    Commit --> Reconcile: more tasks
    Checkpoint --> Review: track complete
    Checkpoint --> Reconcile: next phase
    Review --> Fixes: actionable findings
    Fixes --> Verify
    Review --> NextTrack: review clean
    NextTrack --> Reconcile: approved work remains
    Execute --> Decision: new authority or material choice required
    Decision --> IndependentWork: safe work remains
    Decision --> Reconcile: decision receipt recorded
    IndependentWork --> Reconcile: work available
    IndependentWork --> Waiting: only blocked scope remains
    NextTrack --> Complete: all approved work complete
    Waiting --> Reconcile: external state or decision changes
    Complete --> [*]
```

Task, phase, checkpoint, review, and track boundaries automatically return to
`Reconcile`; they are not handoff stops. Decision gates block only the affected
branch, and repository evidence provides the resumable state ledger. The
human-readable and machine-readable authority is linked from
`conductor/index.md`.

## Observation and publication states

```mermaid
stateDiagram-v2
    [*] --> Discovered
    Discovered --> Eligible: scope and policy permit capture
    Discovered --> Restricted: policy or rights gate
    Eligible --> Attempted
    Attempted --> Captured: original bytes or metadata stored
    Attempted --> Unavailable: source cannot be retrieved
    Attempted --> Failed: bounded terminal failure
    Attempted --> Eligible: safe retry scheduled
    Captured --> Validated: integrity and schema checks pass
    Captured --> Failed: integrity or policy failure
    Validated --> Unchanged: fingerprint matches prior observation
    Validated --> Versioned: relevant content changed
    Versioned --> Transformed
    Transformed --> DerivativeValidated
    DerivativeValidated --> Uploaded
    Uploaded --> RemotelyVerified
    Uploaded --> UploadUnverified
    UploadUnverified --> Uploaded: bounded reconciliation
    RemotelyVerified --> Released: explicit Zenodo release gate
    Versioned --> Withdrawn: source disappears or is withdrawn
    Withdrawn --> Tombstoned
    Tombstoned --> Restricted: verified exception decision
```

An observed state transition produces a timestamped receipt. A workflow outcome
does not skip publication states.

## Trust boundaries

```mermaid
flowchart TB
    Public["Untrusted public metadata and files"]
    Runner["Ephemeral local or CI runner"]
    Local["Local operational state"]
    Evidence["Reviewed compact evidence"]
    Secrets["Environment-scoped credentials"]
    HF["Hugging Face"]
    Zenodo["Zenodo"]

    Public -->|"validate, bound, hash"| Runner
    Runner -->|"immutable objects and ledger transactions"| Local
    Local -->|"redacted manifests and reports"| Evidence
    Secrets -->|"least privilege; never logged"| Runner
    Runner -->|"explicit upload gate"| HF
    HF -->|"remote read-back verification"| Runner
    Runner -->|"explicit immutable release gate"| Zenodo
    Zenodo -->|"DOI and checksum read-back"| Runner
```

Inputs from public sources remain untrusted. Filenames, media types, archive
members, redirects, decompression, schemas, and claimed checksums require
validation and resource bounds.

## Version identity

A source observation identifies:

- catalogue and source dataset identifiers;
- metadata response object hash;
- each resource URL and retrieved object hash;
- observation and retrieval timestamps in UTC;
- prior observation relationship;
- policy, licence, rights, and availability state;
- transformation and derivative relationships;
- Git, Hugging Face, and Zenodo publication receipts.

Versions are created from material metadata or object changes, not merely from a
scheduled run. An unchanged verification still produces evidence without
duplicating the archived version.

## Storage roles

| Layer | Role | Authoritative |
| --- | --- | --- |
| Content-addressed objects | Original bytes and durable derivatives | Yes |
| Versioned manifests | Identity, provenance, relationships, states | Yes |
| SQLite ledger | Transactions, checkpoints, retries, resumability | Operational |
| Parquet/JSONL | Portable analysis and interchange | Derived |
| DuckDB | Reconciliation, validation, reporting | Rebuildable |
| Graph engine | Relationship query acceleration | Optional projection |
| Lance/LanceDB | Semantic retrieval | Optional projection |
| GitHub | Source, schemas, compact evidence, issues | Delivery evidence |
| Hugging Face | Rolling public dataset archive | Verified remote copy |
| Zenodo | Immutable citable release snapshot | Verified release copy |

## Recovery principle

A bounded release must be reconstructable from its manifest and referenced
objects without relying on SQLite, DuckDB, graph, or vector database files.
Recovery tests verify object integrity, manifest closure, derivative receipts,
and external publication relationships.
