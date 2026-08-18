# Design Specification: Legislation Consolidation Corrective Programme

## 1. Architectural Principles
- **Separation of Responsibilities**:
  - `NZLegislationAdapter` in `src/archive_govt_nz/adapters/nz_legislation.py` acts as the source-facing capture boundary and raw CAS payload writer.
  - Domain services in `src/archive_govt_nz/domains/legislation/` manage discovery, traversal, validation, manifests, checkpoints, and parquet/jsonl generation.
  - Shared HTTP infrastructure manages auth injection, rate limiting, and exponential retry.
- **Product Isolation**:
  - `edithatogo/legislation` is strictly preserved as an independent outward-facing package/MCP/CLI.
- **Safe Parsing**:
  - `xml.etree.ElementTree` and safe HTML parsing with script/style stripping are used. Unsafe regex replacements are eliminated.
