# Specification: Platinum Layer Cross-Jurisdiction Federation, Croissant ML Metadata & Citable Synthesis

- **Track ID:** `platinum_layer_federation_and_synthesis_20260825`
- **Type:** feature
- **Alignment:** [`edithatogo/global-medicines-atlas`](https://github.com/edithatogo/global-medicines-atlas), [`edithatogo/fyi-archive`](https://github.com/edithatogo/fyi-archive)

---

## 1. Overview & Architectural Vision

The **Platinum Layer** represents the highest tier of the Medallion Data Architecture. While Bronze guarantees immutable acquisition, Silver ensures bitemporal typed Parquet consistency, and Gold exposes DuckDB views and search indexes, the Platinum Layer delivers **cross-jurisdiction federated synthesis, AI/ML-ready Croissant metadata, and immutable citable publication packages**.

---

## 2. MoSCoW Requirements

### Must Have
- **MUST-1 (Federated Join Architecture):** Expose pre-built zero-copy DuckDB join views combining `archive-govt-nz` Silver/Gold tables with attached `global-medicines-atlas` (`gma_*`) and `fyi-archive` (`fyi_*`) Parquet files.
- **MUST-2 (Croissant Metadata Generation):** Generate valid W3C/MLCommons **Croissant (`croissant.json`)** descriptors for all published domain datasets (Legislation, Gazette, Hansard, Medico-Legal, Treasury).
- **MUST-3 (Multi-Target Publication Routing):** Orchestrate publication pipelines across Hugging Face, Zenodo (concept DOIs & draft depositions), GitHub Releases, and OSF.
- **MUST-4 (Fail-Closed Receipt & Fixity Verification):** Generate signed Ed25519 publication receipts recording bundle hashes, file counts, and remote readback validations.
- **MUST-5 (CLI / MCP Federation Queries):** Expose federated cross-jurisdiction queries via `archive-govt-nz query --federated` and MCP server tools.

### Should Have
- **SHOULD-1 (Automated Hugging Face Readback):** Verify remote Parquet file availability and SHA-256 fixity immediately after scheduled dataset sync.
- **SHOULD-2 (Schema.org / DCAT-AP Parity):** Ensure Croissant metadata seamlessly maps with DCAT-AP 3.0 catalog structures and RO-Crate 1.1 manifests.

### Could Have
- **COULD-1 (Interactive Cross-Atlas Exploration):** Provide sample federated SQL templates for cross-jurisdictional drug pricing and statutory policy analysis.

### Won't Have (This Track)
- **WONT-1:** Do not merge external partner repositories physically into `archive-govt-nz`.
- **WONT-2:** Do not publish to production Zenodo without explicit maintainer gate authorization.

---

## 3. Success Criteria
1. Federated DuckDB queries join NZ statutory records with `global-medicines-atlas` in zero-copy execution (< 50ms).
2. `croissant.json` metadata passes validation against the official MLCommons Croissant schema.
3. Distribution publisher produces verifiable publication receipts with remote readback hashes.
4. All quality gates, static typing, and mutation tests pass with 0 errors and >= 95% test coverage.
