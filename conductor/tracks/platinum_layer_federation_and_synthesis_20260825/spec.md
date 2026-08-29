# Specification: Platinum Layer Cross-Jurisdiction Federation, Croissant ML Metadata & Citable Synthesis

- **Track ID:** `platinum_layer_federation_and_synthesis_20260825`
- **Type:** feature
- **Alignment:** [`edithatogo/global-medicines-atlas`](https://github.com/edithatogo/global-medicines-atlas), [`edithatogo/fyi-archive`](https://github.com/edithatogo/fyi-archive), [`edithatogo/nlp-policy-nz`](https://github.com/edithatogo/nlp-policy-nz)

---

## 1. Overview & Architectural Vision

The **Platinum Layer** represents the highest tier of the Medallion Data Architecture. While Bronze guarantees immutable acquisition, Silver ensures bitemporal typed Parquet consistency, and Gold exposes DuckDB views and search indexes, the Platinum Layer delivers **cross-jurisdiction federated synthesis, AI/ML-ready Croissant metadata, universal Hugging Face dataset publishing, and complete donor repository retirement assurance**.

---

## 2. MoSCoW Requirements

### Must Have
- **MUST-1 (Schema-as-Code Unification):** Implement a single Medallion schema generator producing PyArrow schemas, Pydantic validation models, and W3C/MLCommons **Croissant (`croissant.json`)** descriptors with zero manual drift.
- **MUST-2 (Universal Hugging Face Hub Publication):** Scaffold and orchestrate automated publication of all 7 domain datasets (`nz-legislation`, `nz-gazette`, `nz-hansard`, `nz-hathitrust-historic`, `nz-cases-medilegal`, `archive-govt-nz-treasury`, `nz-ckan-catalogs`) with rich dataset cards and `croissant.json` descriptors.
- **MUST-3 (Zero-Copy Cross-Repository Federation):** Expose pre-built zero-copy DuckDB join views combining `archive-govt-nz` Silver/Gold tables with attached `global-medicines-atlas` (`gma_*`) and `fyi-archive` (`fyi_*`) Parquet files.
- **MUST-4 (Downstream `nlp-policy-nz` Export Contracts):** Establish canonical Parquet/Arrow export fixtures and typed streaming contracts for downstream NLP modeling in `nlp-policy-nz` (Hansard debate discourse, Medico-Legal tribunal outcomes, Hathi OCR text, Gazette notices).
- **MUST-5 (Five-Donor Archival & Drift Enforcement):** Extend `tools/check_claim_drift.py` and emission receipts to track and enforce GitHub archival state for all 5 donor repositories (`sm-govt-nz`, `corpus-legislation-nz`, `corpus-nz-hansard`, `hathi-nz`, `corpus-cases-medilegal-nz`).
- **MUST-6 (Fail-Closed Readback Verification):** Generate signed Ed25519 publication receipts recording bundle hashes, file counts, and remote readback validations.
- **MUST-7 (CLI / MCP Federation Queries):** Expose federated cross-jurisdiction queries via `archive-govt-nz query --federated` and MCP server tools.

### Should Have
- **SHOULD-1 (Polars LazyFrame Streaming Pipeline):** Optimize Silver pipeline batch conversions with out-of-core streaming chunks for 100-year historical corpora.
- **SHOULD-2 (Schema.org / DCAT-AP 3.0 Parity):** Ensure Croissant metadata seamlessly maps with DCAT-AP 3.0 catalog structures and RO-Crate 1.1 manifests.

### Could Have
- **COULD-1 (Interactive Cross-Atlas SQL Templates):** Provide sample federated SQL templates for cross-jurisdictional drug pricing and statutory policy analysis.

### Won't Have (This Track)
- **WONT-1:** Do not create any new GitHub repositories; consolidate all preservation into `archive-govt-nz` and downstream extraction into `nlp-policy-nz`.
- **WONT-2:** Do not publish to production Zenodo without explicit maintainer gate authorization.

---

## 3. Success Criteria
1. Single Medallion schema engine compiles Arrow, Pydantic, DCAT-AP, and Croissant descriptors with 100% field consistency.
2. Federated DuckDB queries join NZ statutory records with `global-medicines-atlas` in zero-copy execution (< 50ms).
3. All 7 domain datasets have valid `croissant.json` descriptors passing MLCommons validation.
4. `tools/check_claim_drift.py` tracks all 5 donor repositories.
5. All quality gates, static typing, and mutation tests pass with 0 errors and >= 95% test coverage.
