# NZ Election Explorer: reproducible platform frontier (2026-11-11)

Owner: solo maintainer. Status: **active / partially implemented**. Existing election tracks remain the authoritative historical record; these corrective tracks supersede unsupported claims without deleting research source or historical evidence.

## Mission
An independently reproducible election results product, electoral research workbench and versioned NZ public-sector data platform. The public interface must never mistake a hypothetical, provisional, counterfactual, forecast or experimental model for observed official results.

## Delivery order and linked tracks
| Track | Description | MoSCoW | Dependency |
|---|---|---|---|
| 01 | Release integrity, vintages and verification | Must | PR #861 correction |
| 02 | Statutory MMP engine, properties and laboratory | Must | 01 |
| 03 | Geospatial and longitudinal election intelligence | Should | 01 |
| 04 | Special votes and coalition uncertainty | Should | 02,03 |
| 05 | Research models and publication packaging | Must | 01 |
| 06 | Advanced causal, finance, demographics and policy text | Should | 03,05 |
| 07 | Single-developer harness, security and profiling | Must | 01 |
| 08 | Experimental parliamentary game theory and frontier systems | Could | 02,04,05 |

Each track has a concrete index and acceptance requirements below. Overall completion requires executable code, trusted source evidence, test output, docs, a successful exact-head CI run and deployed-revision parity (when public). A designed track is NOT an implemented track.

## Architectural decision
Use existing Pydantic/JSON Schema and Arrow/Parquet provenance contracts, DuckDB SQL and **Polars LazyFrame** for tabular analyses; keep Python 3.15.1 and uv locked as the repository's primary environment. Select Polars only where it improves columnar ETL over existing Arrow/DuckDB; no blanket rewrite. Embed 2026 results in a static release bundle generated from canonical Gold artifacts, not hand-coded into HTML.

## Workstream and status
- [x] Prior corrective dataset and static public page proposed in PR #861, **not yet deployed**.
- [x] Test and action-pin corrections committed on PR #861 branch (hosted verification pending).
- [ ] End-to-end data freshness/validation and browser tests.
- [ ] Fully strict basedpyright for scoped new modules, then measured widening; zero new untracked diagnostics.
- [ ] Generate/update uv.lock for any added Polars dependency before locked gates. **Do not edit pyproject without regenerating lock**.
- [ ] Reconcile legacy causal and experimental values to qualified evidence, not illustrative fixtures.
- [ ] Merge PR #861 only after exact-head green gates and verify served HF revision.
