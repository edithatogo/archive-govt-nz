# Track 4 Requirements (MoSCoW)

## Must Have
- **MUST-1**: Define canonical URI and identifier schemes for all source types (`ckan://`, `bluesky://`, `threads://`, `x://`, `youtube://`, `feed://`, `email://`, `web://`).
- **MUST-2**: Specify universal `SourceManifest`, `PreservationManifest`, `CaptureEvent`, and `PublicationReceipt` schemas with JSON Schema Draft 2020-12 validation.
- **MUST-3**: Support explicit tombstone and withdrawal states with tamper-evident justification records.
- **MUST-4**: Integrate W3C PROV-O JSON-LD metadata for all capture activities and software agents.

## Should Have
- **SHOULD-1**: Create automated schema validation tests in `tools/validate_schemas.py`.

## Won't Have
- **WONT-1**: Do not alter existing stored CAS digests or mutate active production manifests.
