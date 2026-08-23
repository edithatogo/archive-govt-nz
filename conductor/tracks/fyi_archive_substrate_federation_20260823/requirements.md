# Requirements: FYI (OIA) Archive Substrate Federation

- **Track ID:** `fyi_archive_substrate_federation_20260823`
- **Upstream / Donor:** `edithatogo/fyi-archive`
- **Consolidation Mode:** Shared archive/publication substrate; federated integration (excluding fyi-cli / foi-o)

## 1. Functional Requirements (MoSCoW)
### 1.1 MUST Have
- **MUST-1:** Leverage existing upstream assets: OIA request/attachment metadata, correspondence thread models, agency authority linkages.
- **MUST-2:** Integrate capability into `archive-govt-nz` preservation core without breaking existing domain boundaries.
- **MUST-3:** Enforce strict Bronze/Silver/Gold medallion data layering and provenance lineage.
- **MUST-4:** Maintain 100% test coverage for newly adapted domain code with zero placeholder patterns.

### 1.2 SHOULD Have
- **SHOULD-1:** Provide clean CLI inspection and verification tools.
- **SHOULD-2:** Generate machine-readable parity and recovery receipts.

### 1.3 WON'T Have (Explicit Boundaries)
- **WONT-1:** Full physical ingestion of standalone product repositories (e.g. `legislation`, `dnz`, `fyi-cli`, `foi-o`, `searchright`, `sourceright`, `reimbursement-atlas`).
- **WONT-2:** Breaking independent citation/versioning of upstream research corpora.
