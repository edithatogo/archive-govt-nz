# Tech Stack

## Runtime

- Python 3.11+
- Packaging with `uv_build` (migrated from `hatchling`)
- CLI entry point: `nzlc`

## Core libraries

- `typer` for the command-line interface.
- `requests` for API access.
- `rich` for terminal output.
- `pyarrow` for Parquet writing and data handling.
- `defusedxml` for safe XML parsing.
- `huggingface_hub` and `hf-xet` for Hugging Face dataset publishing.
- `jsonschema` for schema validation.
- `zstandard` for compression support.
- `pydantic` and `pydantic-settings` for environment-based configuration
  (pydantic v2 with `BaseSettings`).

## Development tools

- `pytest` for tests.
- `ruff` for linting and import sorting.
- `ty` for static typing, with all available rules promoted to errors where
  the current `ty` release supports that severity.
- `pre-commit` for local checks.
- `hypothesis` for property-based testing of pure functions.
- `pytest-cov` for coverage reporting with `fail_under = 60`.
- `scalene` for CPU/memory profiling of performance-sensitive paths.
- `vale` for prose linting of documentation files (optional/advisory).

## Data and artifact formats

- JSONL for normalized records and provenance-oriented outputs.
- XML and HTML as source/provenance formats.
- Parquet for optimized tabular dataset shards.
- JSON manifests and checksum files for validation and audit trails.

## External services

- Official New Zealand Legislation API.
- Hugging Face Datasets.
- Zenodo.
- GitHub Actions for CI and release automation.

## Project structure

- `src/nz_legislation_corpus/` contains the application code.
- `tests/` contains unit and integration-style tests.
- `docs/` contains operational and release documentation.
- `schemas/` contains validation schemas and related artifacts.
- `scripts/` contains local and release automation helpers.

## Implementation notes

- Favor deterministic outputs and stable ordering where possible.
- Keep external-service interactions isolated behind narrow interfaces.
- Preserve provenance and hashes so downstream artifacts remain auditable.

## Publication and metadata environments

Track publication alignment across:

- GitHub for code, CI, releases, security posture, repository metadata, and lightweight artifacts.
- Hugging Face Datasets for operational/canonical Parquet publication, dataset cards, Xet-backed storage, access/gating state, and viewer health.
- Zenodo for immutable DOI snapshots, archive manifests, checksums, related identifiers, and source-rights-safe license metadata.
- OSF as an optional review or mirror environment only after a policy exists.
- Generated metadata packages such as Croissant, RO-Crate, Frictionless Data Package, DCAT, and PROV-O as future SOTA discovery/interoperability surfaces.


## Zenodraft requirement

Future Zenodo draft/archive workflow changes should use or formally evaluate https://github.com/zenodraft/zenodraft. Use sandbox first, validate .zenodo.json metadata, map tokens to ZENODO_ACCESS_TOKEN or ZENODO_SANDBOX_ACCESS_TOKEN only inside the relevant CI step, and keep publish commands behind protected reviewer approval.


## Bleeding-edge automation target

The corpus-family target is documented in `docs/bleeding-edge-versioning-ci-quality.md`. Prefer Rust-backed tooling where practical: `uv` for Python dependency management, `ruff` for lint/format/imports, `ty` for Python type checking, `typos` for spelling/identifier checks, `zizmor` for GitHub Actions security linting, `taplo` for TOML linting, and local `ripgrep` for maintenance audits. Retain best-in-class non-Rust tools where needed, including CodeQL, OpenSSF Scorecard, Renovate, and `actionlint`.

Release automation should separate code/package versions, dataset versions, schema versions, Hugging Face revisions, Zenodo DOI snapshots, and manifest hashes. Zenodo draft workflows should use or formally evaluate `https://github.com/zenodraft/zenodraft`.

## Arrow and Polars baseline

Both `pyarrow` and `polars` are baseline tabular/dataframe dependencies for corpus work. Use Arrow/PyArrow for Parquet/Arrow interoperability and stable artifact writing; use Polars for high-performance lazy/eager transformations, profiling, and larger derived-table workflows where it simplifies or accelerates the pipeline.
