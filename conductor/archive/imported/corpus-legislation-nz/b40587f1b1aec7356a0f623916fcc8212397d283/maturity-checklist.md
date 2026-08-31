# Maturity Dependency Checklist — corpus-law-nz

| Category | Status | Rationale |
|---|---|---|
| Python environment manager (uv/pixi) | **required** — uv | `uv.lock`, `.uv-cache` dirs, and `pre-commit` uv hook in place. No pixi — not applicable. |
| Python lint/format (ruff) | **required** | Dev dep with extensive config in `pyproject.tool.ruff`. Used in CI and pre-commit. |
| Python type checking (ty/pyright) | **required** — ty | Dev dep with config in `pyproject.tool.ty`. All rules promoted to error. |
| Python logging (loguru) | **required** | Core dependency (`loguru>=0.7.2`). Logger used across pipeline modules. |
| Python CLI UX (typer/rich) | **required** | Core deps. `typer` for CLI entry point (`nzlc`), `rich` for terminal output. |
| Config/env loading (pydantic-settings) | **required** | Core dep. `pydantic-settings` with `BaseSettings` for env-based config. |
| Boundary validation (pydantic v2) | **required** | Core dep `pydantic>=2.0.0` used for config models and data validation. |
| Hot record serialization (msgspec) | **deferred** | Pipelines use JSONL + Parquet. msgspec would improve JSONL round-trip perf but not yet needed. Evaluate when JSONL throughput becomes a bottleneck. |
| Dataframes (polars) | **required** | Core dep `polars>=1.0.0`. Used for high-performance lazy/eager transforms and derived-table generation. |
| Query validation (duckdb) | **deferred** | No current dependency. DuckDB would enable ad-hoc SQL validation of Parquet shards. Add as optional dev tool when post-hoc query patterns solidify. |
| Columnar data (pyarrow/Parquet) | **required** | Core dep `pyarrow>=21.0.0`. Baseline for Parquet artifact writing and Arrow interoperability. |
| JSON schema (jsonschema) | **required** | Core dep `jsonschema>=4.22.0`. Used for record and manifest validation. |
| HTTP clients (httpx/requests) | **required** — requests | Core dep `requests>=2.32.0`. Used for NZ Legislation API access. No httpx — not needed. |
| Retry/backoff (tenacity) | **optional** | No current dep. Retry is ad-hoc via `random` jitter. tenacity would formalize backoff for API calls and HF uploads. |
| HTML parsing (beautifulsoup4/selectolax) | **not_applicable** | Source format is XML (NZ Legislation API); parsed via `defusedxml`. No HTML content in pipeline. |
| Terminal UI (rich) | **required** | Core dep `rich>=15.0.0`. Used for console output, progress bars, and structured display. |
| Checksums/manifests | **required** | Implemented in-house (no library dep). JSON manifests and checksum files are a documented artifact pattern for audit trails. |
| Local vector store (lancedb) | **deferred** | No current dep. LanceDB would enable local embedding search over the corpus. Deferred until semantic search use cases are specified. |
| Service vector DB (qdrant) | **deferred** | No current dep. qdrant would serve hosted vector search. Deferred until a service-side embedding query path is defined. |
| RAG orchestration (haystack) | **deferred** | No current dep. Haystack would orchestrate retrieval-augmented generation over the corpus. Downstream consumer concern — defer to integration phase. |
| HF publication (huggingface_hub/datasets) | **required** | Core deps `huggingface_hub>=0.34.0` and `hf-xet>=1.1.0`. Xet-backed Parquet publication is a primary pipeline output. |
| Archive/DOI (Zenodo/OSF) | **required** — Zenodo; **optional** — OSF | Zenodo is a documented external service for annual DOI snapshots. OSF flagged as "optional review/mirror only after policy exists". No Python lib dependency — integration is CLI/CI-based. |
