# Architecture & Governance Decisions

## ADR-01: In-Place Upgrade of Existing NZLegislationAdapter
- **Decision**: Upgrade existing class `NZLegislationAdapter` in `src/archive_govt_nz/adapters/nz_legislation.py` rather than introducing duplicate classes.
- **Rationale**: Maintain single coherent adapter boundary.

## ADR-02: Strict Separation of Standalone Legislation Product
- **Decision**: Keep `edithatogo/legislation` independent as outward-facing tool.
- **Rationale**: Prevent duplicate maintenance overhead and retain stable npm/MCP identity.

## ADR-03: Safe XML/HTML Parsing
- **Decision**: Use `xml.etree.ElementTree` without entity expansion and safe HTML tag stripping.
- **Rationale**: Regex parsing causes malformed statutory structures.
