# Tranche 2 — socioeconomic sources and election analysis

**16 November 2026. Status: nested tracks recorded; production implementation/admission pending.** Parent: [data maximisation](../index.md). This tranche responds to Dylan's explicit request to inventory/reuse existing socioeconomic data, acquire missing eligible data, integrate it into analysis, and implement what is safely possible. It does not assert that previous data-maximisation or GitHub-to-Hugging-Face work is complete.

## Current evidence and decision

Main inspected: `cf64faca56eb50db14b97f534def3a17a89555f9`; planning base PR868: `a8d398ce3eb5384fdc5329d4158834862b294aa8`. The inspected `materialize_parquet.py` Census section contains five hard-coded records, not a verified source extractor. The dataset card describes archived boundary/enrolment assets; those claims do not establish a complete socioeconomic table inventory. HF metadata was accessible, but an exhaustive current file listing and underlying bytes were not. **Unknown presence is not absence and must not trigger duplicate acquisition.** See [source inventory](source-inventory.json).

Preferred approach: audit and reuse original source bytes first; prefer directly published Census-by-electorate tables on the target boundary vintage; use qualified count/distribution concordances only where necessary. Reject an indiscriminate re-harvest or conversion of the existing example rows into purported empirical data. Maintain the existing Python/Pydantic/Arrow/Polars/DuckDB architecture; the external standard-library prototype is a reference/transfer artifact, not a replacement ETL or an installed repository component.

## Six nested Conductor tracks

| Track | Outcome | Dependencies | Current evidence |
| --- | --- | --- | --- |
| [SOC01 — inventory and reuse](SOC01-inventory.md) | Source/asset census; inspect before acquiring | Existing source/rights owners | Partial metadata/code inspection; inventory incomplete |
| [SOC02 — source-native ingestion](SOC02-ingestion.md) | Reviewed CSV/ADE profiles and qualified observations | SOC01 admitted source cohort | External synthetic prototype only |
| [SOC03 — geography and population](SOC03-geography.md) | Exact boundary/universe identities; qualified concordances | SOC01 metadata; can run alongside SOC02 | Exact-join rejection controls prototyped; real crosswalk pending |
| [SOC04 — temporal and electoral joins](SOC04-joins.md) | Reconciled socioeconomic/election analytical panels | SOC02 + SOC03 + accepted electoral keys/results | External exact-join prototype only |
| [SOC05 — socioeconomic outcomes](SOC05-analysis.md) | Source-backed descriptive analyses, then qualified research | SOC04 | Synthetic descriptive association only |
| [SOC06 — publication and freshness](SOC06-publication.md) | Inspectable datasets, accessible views, source-state badges | Accepted SOC04/05 outputs | Not implemented or deployed |

Machine-readable order and dispositions: [tracks.json](tracks.json). Progress and exact prototype hashes: [implementation-receipt.md](implementation-receipt.md).

## Sequence and parallelism

SOC01 first. Once an eligible small source cohort and metadata are admitted, SOC02 source parsing and SOC03 geography/universe work may proceed independently in separately reserved paths. SOC04 follows accepted outputs from both and the existing P2/P6 interfaces. SOC05 descriptive outcomes follow, with additional source cohorts continuing independently. SOC06 connects each accepted outcome to the existing publication owner; it need not wait for every historical source or advanced model.

These SOC identifiers do not renumber G0–G7 or P0–P10. Link semantically: SOC01/02 to P1/P2/P5 source admission; SOC03 to P4 geography; SOC04 to P6 joins; SOC05 to P7/P8/P10 analyses; SOC06 to P9 publication. Gates require evidence, never elapsed time. Census/income/housing source preparation need not wait until the end of P10 once its own dependencies and ownership are accepted.

## Scope, permissions and independent acceptance

This planning author writes only within the existing `data_maximisation_20261116/` documentation namespace. Shared Conductor/application source remains with `6af41384-bab8-8324-ae28-c6219d0c8177`; sole integration remains with `6aec6190-76c0-8322-b3f4-824a0e4ef399` via issue867. Admission authority is not registry/source/publication authority. No new worker, schedule, source recapture, credential, native pipeline or HF publication is activated. No top-level Conductor registry is changed.

Ordinary code/document admission requires applicable repo-local CPython3.15.1, prescribed harness, independent exact-head review, required hosted checks and receiving-main verification. Live dataset/Space parity and rollback are separate later publication-acceptance requirements, not a reason to publish in order to merge a planning PR. Existing runtime and owner holds remain.

The downloadable offline reference implementation was developed/tested separately in the conversation sandbox, not written into the repository application. Its Python3.13.5 synthetic tests are useful prototype evidence but **not** native3.15.1 or full-repository qualification. The production owner must review/adopt the interfaces into existing modules rather than create a competing pipeline.
