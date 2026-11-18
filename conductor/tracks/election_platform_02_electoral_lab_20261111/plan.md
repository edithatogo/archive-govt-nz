# Executable delivery plan — 02_electoral_lab

- [ ] Identify source contracts, archival rights, input hashes and assumptions.
- [ ] Add a focused failing unit/property-based test for the next narrow behavior.
- [ ] Implement a deterministic source-backed calculation or adapter, preferably reusing Polars/Arrow/DuckDB and existing domain contracts.
- [ ] Add independent fixtures, schema checks, reference differential tests and uncertainty/model-status labels.
- [ ] Run affected Ruff, basedpyright, pytest/Hypothesis, mutation/security gates; preserve exact receipts.
- [ ] Generate versioned outputs, complete browser/performance/a11y evidence as relevant.
- [ ] Confirm exact-head CI, review data/Space release parity and archive only with evidence.

## 02 Statutory electoral lab and sensitivity — reader questions, 18 November 2026

- [ ] **G1 / EQ02–03/EQ06.** Reuse Sainte-Laguë allocation/overhang engine for independently verified 120-seat baseline plus party overhang, 5% and electorate qualification, exact quotient ties, excluded votes and 2023 by-election distinction; compare 2026 to all 11 MMP elections with source-capture confidence.
- [ ] **G1 / EQ02/EQ04.** Determine minimum *integer* party-vote transfer and candidate margin flips that alter seats under an explicitly vote-conserving scenario. Reject scenarios with negative votes, unqualified source vintages or mixed individual/aggregate ballots; independent reference fixtures and property tests.
- [ ] **G4 / EQ14.** Add separated counterfactual rule profiles (current MMP vs alternative thresholds, coat-tail and levelling compensation), preserving baseline election votes and displaying statutory-versus-hypothetical status.

Use the existing focused/red-green and complete PR/release assurance contract. These unchecked tasks are **not completed** by this planning PR and do not transfer source, code or publication ownership. Detailed question IDs and qualification states: [parent EQ matrix](../election_platform_frontier_20261111/decision_questions_20261118.md).
