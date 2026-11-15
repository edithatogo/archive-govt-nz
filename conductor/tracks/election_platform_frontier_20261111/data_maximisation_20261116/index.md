# Election data maximisation and political-finance observatory — 16 November 2026

Status: **plan recorded, implementation unstarted, acceptance pending**. Parent: [NZ Election Explorer programme](../index.md). Repository: [archive-govt-nz](https://github.com/edithatogo/archive-govt-nz). Public product: [NZ Election Explorer](https://huggingface.co/spaces/edithatogo/nz-election-explorer). Dataset: [archive-govt-nz-global](https://huggingface.co/datasets/edithatogo/archive-govt-nz-global).

## Selected outcome

Maximise the verified analytical use of **already acquired** 1996–2026 election data before expanding to additional authorised sources. Establish a continuously monitored, timestamped and versioned elections/finance observatory with six linked consumers: (1) election results live, (2) political finance, (3) campaign advertising, (4) historical electoral atlas, (5) polling and research laboratory, and (6) parliamentary accountability.

**This subplan of the existing registered election programme is a roadmap and acceptance contract, not source acquisition, implementation, a new integration owner, permission to activate workflows, or certification of historical data completeness.** Do not treat archived PDF counts, existing Parquet paths, completed historical checkboxes or a published image as verified source-derived analysis.

## Scope and ownership boundaries

- Current shared election/dashboard and Conductor owner remains **6af41384-bab8-8324-ae28-c6219d0c8177** under [coordination issue #867](https://github.com/edithatogo/archive-govt-nz/issues/867); the pre-existing sole PR integrator controls merge/issue acceptance. This documentation branch owns only this **new** subplan directory. No edits to the parent programme, shared registry, source, workflows, publication targets, security infrastructure or native archives are authorised by this packet.
- Deliver implementation through existing programme tracks, not another ETL, data warehouse, model registry or security service. Coordinate first if an implementation touches an already assigned path/native operation.
- Existing required controls remain: repository-local CPython 3.15.1, locked dependencies, focused verification then full reviewable-PR harness, exact-head hosted checks, source rights, privacy and publication parity. Every subsequent batch must be independently accepted; no gate weakening or retroactive claims.
- Scope excludes individual voter targeting, collecting sensitive private profiles, implying donor-policy causation from an entity match, circumvention of source access controls, and publishing unverified speculative quantities.

## Workstream crosswalk

| New workstream | Existing authoritative implementation track | Completion boundary |
| --- | --- | --- |
| W0 Inventory, freshness, source versions, publisher readback | [01 release integrity](../../election_platform_01_release_integrity_20261111/index.md) | All public facts source-backed; stale/failed releases fail closed |
| W1 Bronze finance extraction, canonical Silver and financial Gold | [06 political economy](../../election_platform_06_political_economy_20261111/index.md) and [Silver ingestion](../../election_medallion_silver_ingestion_20261110/index.md) | Auditable official-finance totals, no synthetic rows |
| W2 Vote-place backfill, demographic joins, historical concordances | [03 spatial longitudinal](../../election_platform_03_spatial_longitudinal_20261111/index.md) | Coverage-aware, comparable geography/year/denominator |
| W3 Additional source onboarding and rights decisions | [01 release integrity](../../election_platform_01_release_integrity_20261111/index.md) and [06 political economy](../../election_platform_06_political_economy_20261111/index.md) | Explicit per-source licence, eligibility and provenance |
| W4 Six public products and reusable research downloads | [05 publication](../../election_platform_05_publication_20261111/index.md) | Accessibility, citations, reproduce/export parity |
| W5 Empirical model qualification, optional parliamentary links | [06 political economy](../../election_platform_06_political_economy_20261111/index.md) and [02 electoral lab](../../election_platform_02_electoral_lab_20261111/index.md) | Fit-only-on-observations; documented uncertainty and boundaries |
| W6 Performance, CI, safety, quality and auditability | [07 solo harness](../../election_platform_07_solo_harness_20261111/index.md) | Existing full gates retained; bounded tests and reproducible evidence |

Registered parent track: [election_platform_frontier_20261111](../index.md). No new top-level registry entry or standalone track is introduced.\n\nSee [requirements](requirements.md), [design](spec.md), [execution plan](plan.md), and [initial source register](source-register.md).

**Outcome and evidence links:** [15 question-to-data outcomes and 10 cross-dataset join tasks](outcomes-and-joins.md); [current November 2026 news and policy issue register](news-issue-register.md). These define what each new data source must help answer, how tables link, how question-specific Gold results are qualified and which claims remain unanswerable; both are planning-only. Optional advanced forecasting and experimental systems stay under existing 04/08 tracks and behind research-only qualification.

## Release policy

The election-results pane is authoritative only as a **source-verified snapshot** with an explicitly identified preliminary/official status. Financial data have independent filing calendars and must not be labelled complete 2026 spending before the post-election returns are available. Historical source capture and operational completeness must be reported separately.

## Source-sensitive findings requiring implementation verification

1. Existing `src/archive_govt_nz/domains/elections/materialize_parquet.py` materialises campaign-finance tables from fixed illustrative figures rather than evidenced 1996–2025 filings; historical names/paths are not proof of historical rows.
2. Existing `src/archive_govt_nz/domains/elections/finance_causal_engine.py` returns fixed IV/RDD statistics in some paths, which must not appear publicly as estimated effects.
3. Current GitHub release fixture contains the 7 November 2026 preliminary figures, while the separately inspected public HF Space repository retains legacy HTML and lacks the data fixture. Runtime readback and successful serving parity were **not** established.
4. HF Dataset Viewer metadata reports an unqueryable/failed Parquet viewer, although archived raw objects may still exist. Dataset Viewer health is not a raw-corpus inventory.
5. Historical voting-place Parquet coverage and captured raw-byte CSV coverage do not yet match; investigate reprocessing before additional crawling.

All five are **review observations**, not a claimed completed defect-fix or full corpus audit. Preserve receipts and qualify them against the latest head when implementing.
