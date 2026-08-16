# Track 7 Requirements (MoSCoW)

## Must Have
- **MUST-1**: Implement `ArchivePacket` v1 and `PublicationReceipt` v1 models with JSON Schema validation.
- **MUST-2**: Maintain Hugging Face dataset slug continuity without minting orphan or duplicate repositories.
- **MUST-3**: Support Zenodo concept DOI versioning with automatic deposit validation and checksum verification.
- **MUST-4**: Generate Croissant metadata, RO-Crate profiles, and DCAT-AP 3.0 graphs for every publication release.

## Should Have
- **SHOULD-1**: Support dual dry-run comparison between donor and target publication payloads.

## Won't Have
- **WONT-1**: Do not execute live production publication in this track without passing Track 10 canary validation.
