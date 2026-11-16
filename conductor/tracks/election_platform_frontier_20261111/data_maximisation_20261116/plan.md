# Finite implementation plan — source-backed election observatory

Implementation sequencing, concurrent chat ownership, exact PR intake/merge steps and worker prompts: [ChatGPT delivery orchestration](chatgpt-delivery-orchestration.md) and [scheduled prompt pack](scheduled-chatgpt-prompts.md).

All boxes are intentionally unchecked. This subplan's planning PR claims **documentation only**: no harvest, no validated dataset, no scheduled execution, no dashboard release, no full harness or downstream owner acceptance. Implement only as selected bounded, evidence-backed increments through existing tracks; do not create another overlapping programme.

## Phase 0 — baseline trust, inventory and deployment (target weeks 1–2)

- [ ] **EDM-P00** Reconcile current `main`, Space served revision, archive HF dataset, all election CI/main rulesets and active owner comments; publish exact-head dataset/Space parity discrepancy receipt.
- [ ] **EDM-P01** Generate a source-asset/expected-filing coverage inventory across historical party/annual returns, 2026 donation disclosures, spending, voting places, polls, boundaries and supplementary datasets. Distinguish raw CAS, extracted, normalised, reconciled and public states; preserve source-rights and missingness. Output machine-readable manifest + audit table.
- [ ] **EDM-P02** Audit `materialize_parquet.py`, `predictive_engine.py`, `finance_causal_engine.py` and dashboard/static figures; create focused negative regressions preventing synthetic/fixed values in empirical releases. Do not 'repair' legacy numbers by changing authoritative fixtures or concealing failures.
- [ ] **EDM-P03** Repair a coherent release pipeline with separate source-published/captured/validated/deployed timestamps, SHA and revision history; fail-closed last-good release and stale-data warnings. Verify actual HF served files, not only GitHub source.
- [ ] **EDM-P04** Evaluate HF Dataset Viewer failure and supply correctly specified queryable datasets, or a documented download alternative with independent Parquet readback, before claiming Dataset Viewer support.

**Gate:** source and rights census, negative controls, exact-source results arithmetic, release hashes, offline browser smoke and exact serving parity. Ownership: existing 01, 05, 07; no changes to active shared assets without owner handoff.

## Phase 1 — exploit existing political-finance archive (target weeks 2–6)

- [ ] **EDM-P10** Pilot verified extraction on representative 2023–2025 annual donation/loan returns and 2023 party/candidate/promoter expenses. Record per-file actual source SHA, PDF page/cell/row locator, extraction confidence and independent monetary-total reconciliation.
- [ ] **EDM-P11** Expand through documented 1996–2025 party donations/loans and available 2008–2023 party expenses, 2011–2023 candidate and 2020/2023 promoter returns. Report expected/available/extracted/reconciled by party/year/filing category, with unresolved older-year availability held, not counted complete.
- [ ] **EDM-P12** Implement effective-dated finance thresholds, identities, donation/loan/in-kind and actual-vs-allocation scope, correction lineage, anti-double-counting of annual vs major disclosures, CPI basis, and range/null semantics. Produce audited Silver and Gold, not synthetic examples.
- [ ] **EDM-P13** Build fact definitions for spending per documented party/candidate vote, seat and enrollee, finance time series, disclosed donor top-k concentration and partial-disclosure bounds. Add independent accounting/denominator regression tests.

**Gate:** each declared return total reconciles or has an explicit documented discrepancy; no synthetic financial facts or unqualified all-donor Gini. Ownership: existing 06 and Silver.

## Phase 2 — deepen already-acquired electoral data (target weeks 4–10)

- [ ] **EDM-P20** Convert additional archived 2017/2020/2023 voting-place CSVs to comparable derivatives; reconcile to official totals, preserve edition and original source snapshots, quantify year/electorate coverage.
- [ ] **EDM-P21** Resolve historical aliases, electorate boundaries and changes, vote/candidate/election grain, missing datasets, denominator and census/geography vintage; avoid ecological interpretation of person-level preferences.
- [ ] **EDM-P22** Normalise captured 1993–2026 opinion polls with pollster, field dates, survey modes, sample sizes, and caveats; separately qualify NZES 1993 and future NZES datasets where rights and study compatibility allow.
- [ ] **EDM-P23** Produce historical turnout, advance voting, demographic/age/enrolment and vote share analyses. Validate parity for at least 2017, 2020 and 2023 before large-scale historical claims.

**Gate:** versioned comparable geography/crosswalks, independent tally totals, documented mapping gaps and rights.

## Cross-cutting join and research-outcome acceptance (applies to phases 0–5)

- [ ] **EDM-J00** Admit 15 question IDs **O01–O15** from [outcome/joins contract](outcomes-and-joins.md) as evidence-driven product backlog items (not automatically complete merely because the component exists). Map each to an existing 01/03/05/06/07 implementation owner and declared source/rights, coverage, historical vintage, unit, joins and expected dashboard view.
- [ ] **EDM-J01** Execute **JOIN-01–JOIN-10** in coherent nonoverlapping batches: source snapshots, stable party/candidate and organisational identities, versioned weighted geographic crosswalks, financial anti-duplication, advertising/organisations, versioned policies, external socioeconomic context, independently reconciled Gold, negative controls and accessible publication.
- [ ] **EDM-J02** Promote an outcome only after a **QuestionEvidenceReceipt** proves source/vintage hashes, join cardinalities, unmatched/duplicate counts, correct denominator/time basis, independent arithmetic, research class and deployed revision. Unsupported results remain visible as source-pending/blocked, not estimated.
- [ ] **EDM-J03** Triage the nine documented news/policy themes in [recent news register](news-issue-register.md) as bounded OID-linked research questions; record article metadata and original official data evidence separately, and refresh after new authoritative releases. No article-body scraping or source-rights exception.
- [ ] **EDM-J04** Make anti-misjoin tests blocking for (a) wrong election vintage, (b) candidate and party alias ambiguity, (c) cross-period policy claims, (d) geography version errors, (e) donation double counts, (f) protected donor de-anonymisation, (g) advertising spend-band point estimates and (h) person-level/ecological causal overreach.

**Dependency:** JOIN-01–03 require validated Bronze/source identity and source rights; JOIN-04–07 depend on admitted financial, socioeconomic and policy sources; JOIN-08–10 depend on reconciliation and required quality/security/serving checks. The news queue is a source of questions only. The exact implementation order is chosen by the existing owner/coordinator without creating a competing worker.

## Phase 3 — source expansion with eligibility (target weeks 6–12)

- [ ] **EDM-P30** Prioritise Electoral Commission 2026 immediate donations, party/loan annual disclosures, broadcasting allocations and registered promoters. Admit distinct source types with amendment and reporting-period metadata; capture only through permitted qualified access paths.
- [ ] **EDM-P31** Discover new candidate, party, broadcasting and promoter returns on actual publication, not just filing deadlines; distinguish filing due, received, published and captured dates. Track the expected official election declaration and detailed E9 statistics without assuming availability.
- [ ] **EDM-P32** Pilot Meta/Google political advertising libraries preserving spend/range and date coverage, then assess legal rights, platform completeness and advertiser identity matching.
- [ ] **EDM-P33** Evaluate Stats NZ/Companies Office/NZBN/Charities Services open datasets, local elections and NZES material; separately assess parliamentary interests, Hansard/divisions and procurement source rights. Do not create unsupported causal links.

**Gate:** per-source legal and technical admission, identity precision/recall audit for entity matching, privacy and provenance. Sources in [register](source-register.md) are candidates, not approved acquisitions.

## Phase 4 — shared public analytical products (target months 3–5)

- [ ] **EDM-P40** Publish verified Results Live and Political Finance Explorer (both provisional/official-vintage switch and return-class/time-range filters), then Campaign Advertising and Historical Atlas, based only on released Gold data.
- [ ] **EDM-P41** Deliver Polling & Research and optional Parliamentary Accountability surfaces only after underlying source/method qualification; clearly separate descriptive, estimated, counterfactual and experimental.
- [ ] **EDM-P42** Offer audited data/figure bundles (CSV/Parquet/Arrow), source-level citations, methodology, visible coverage/limitation warnings and history diff.
- [ ] **EDM-P43** Validate mobile, keyboard/screen-reader, empty/missing-source states, performance and privacy; verify serving SHA and downloaded-export parity on the actual HF Space.

**Gate:** independent browser/revision readback, data-to-chart reconciliation, source rights and exact-head CI, never a static screenshot as acceptance.

## Phase 5 — optional advanced and institutional research (target months 5–12)

- [ ] **EDM-P50** Where datasets and design justify it, implement measured forecast calibration, party-switching or spatial models with pre-registered features/estimand, leakage tests, confidence intervals, placebo and robustness controls. No fixed model result may masquerade as a fit.
- [ ] **EDM-P51** Link public MPs interests, bills/divisions, Hansard and procurement records only under qualified entity matches and conservative explanatory language, with suitable false-positive and privacy checks.
- [ ] **EDM-P52** Compare national and local elections when open data, geography and turnout definitions permit. Experimental game, quantum, biological and autonomous models remain isolated under existing 08 research track.

**Gate:** independent scientific review of model claims; optional research cannot block verified core products.

## Milestones / receipts

Each admitted implementation batch identifies: owner, nonoverlapping paths, source cohort, source/transform/target hashes, applicable original rights, focused red/green commands, full `./scripts/validate.sh` receipt for reviewable PR, required exact-head hosted checks, independent diff review, deployed revision/parity when relevant, residual holds. Only the designated coordinator merges, with expected-head SHA. Document-only check does not qualify an implementation or publication.

## Management indicators (per source family and year)

- **Coverage:** expected, discovered, captured, extracted, reconciled and published records/files, each with denominator and unresolved/missing count.
- **Accuracy:** source statement-to-derived total difference, duplicate/identity disputes, and unverified figure count.
- **Freshness:** time since source publication, latest successful check/capture/validate/deploy; count and duration of stale releases.
- **Availability:** exact queryable rows, Dataset Viewer health, export parity and accessible public product status.
- **Research:** share of outputs with methodology and original-source citations; proportion of optional model claims independently qualified.
