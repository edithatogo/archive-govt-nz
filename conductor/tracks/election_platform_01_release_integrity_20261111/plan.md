# Executable delivery plan — 01_release_integrity

- [ ] Identify source contracts, archival rights, input hashes and assumptions.
- [ ] Add a focused failing unit/property-based test for the next narrow behavior.
- [ ] Implement a deterministic source-backed calculation or adapter, preferably reusing Polars/Arrow/DuckDB and existing domain contracts.
- [ ] Add independent fixtures, schema checks, reference differential tests and uncertainty/model-status labels.
- [ ] Run affected Ruff, basedpyright, pytest/Hypothesis, mutation/security gates; preserve exact receipts.
- [ ] Generate versioned outputs, complete browser/performance/a11y evidence as relevant.
- [ ] Confirm exact-head CI, review data/Space release parity and archive only with evidence.

## 01 Release integrity and vintage gate — reader questions, 18 November 2026

- [ ] **G0 / EQ07.** Freeze and identify preliminary vote/electorate/list outcomes and the future official release as distinct snapshots, including publisher/capture/validation/served dates, rights and exact digests; reject mixed-vintage joins. Restore trusted static release through source-safe repair acceptance, not an unqualified PR #866 merge.
- [ ] **G0.** Prove browser-offline fallback, missing-source fail-closed behaviour, rollback and exact Hugging Face served revision; keep historical source hashes null where uncaptured and do not conflate Port Waikato's later seat with 2023 general-election overhang.
- [ ] **G2 / EQ07.** After the actual official 2026 publication, compute independently reconciled provisional→official per-party/electorate and seat/overhang/majority changes; version the old 7 November release unchanged.

Use the existing focused/red-green and complete PR/release assurance contract. These unchecked tasks are **not completed** by this planning PR and do not transfer source, code or publication ownership. Detailed question IDs and qualification states: [parent EQ matrix](../election_platform_frontier_20261111/decision_questions_20261118.md).
