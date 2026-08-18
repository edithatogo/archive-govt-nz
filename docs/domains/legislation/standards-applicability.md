# Standards Applicability: Legislation Archiving Domain

## Applicable Standards and Conformance Framework

| Standard | Role | Applicability | Validation Mechanism |
|---|---|---|---|
| **JSON Schema Draft 2020-12** | Data interchange & contract schemas | Normative | `tools/validate_schemas.py` and `tools/validate_contracts.py` |
| **NZ Legislation API XML/HTML** | Source bitstream preservation | Source Preserved | `src/archive_govt_nz/domains/legislation/normalise.py` |
| **FRBR (Work/Expression/Manifestation)** | Identity model | Canonical Internal | `src/archive_govt_nz/domains/legislation/identity.py` |
| **PREMIS / W3C PROV-O** | Preservation and provenance metadata | Canonical Internal | `src/archive_govt_nz/provenance.py` |
| **Parquet / Arrow (Snappy)** | Columnar corpus distribution | Publication | `src/archive_govt_nz/domains/legislation/corpus.py` |
| **RFC 3339 / ISO 8601** | Timestamps | Normative | `tests/tools/test_receipt_timestamps.py` |
| **Model Context Protocol (MCP)** | Agent tooling protocol | Interface | `src/archive_govt_nz/mcp_server.py` |
