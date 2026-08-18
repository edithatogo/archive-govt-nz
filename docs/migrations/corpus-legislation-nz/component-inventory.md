# Component Inventory: Legislation Consolidation

| Repository | Path | Symbol | Disposition | Role |
|---|---|---|---|---|
| `archive-govt-nz` | `src/archive_govt_nz/adapters/nz_legislation.py` | `NZLegislationAdapter` | `reuse_in_place` | Source-facing capture boundary and raw CAS payload writer. |
| `corpus-legislation-nz` | `src/nz_legislation_corpus/nz_api.py` | `NZLegislationClient` | `port_behaviour` | Pacing, retry-after headers, and rate limiting logic ported to target. |
| `corpus-legislation-nz` | `src/nz_legislation_corpus/normalise.py` | `normalise_act` | `port_behaviour` | ElementTree XML parsing ported to domain normalization service. |
| `legislation` | `src/index.ts` | `nzlegislation` | `retain_external` | Standalone interactive legal search CLI/MCP. |
