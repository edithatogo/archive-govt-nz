# Election-data maximisation — acceptance requirements (2026-11-16)

These are new programme requirements linked to, **not replacing**, the existing election-frontier Must/Should requirements and the repository's finite delivery contract. Mark none complete on this planning PR.

## Must: verification, integration and historical exploitation

- **EDM-M01 Inventory.** Build a machine-readable source/asset/expected-filing register by publisher, election, party/candidate, document type, event/vintage, rights and expected publication. Each asset carries lifecycle states `discovered|captured|extracted|normalised|reconciled|published|held|unavailable`, evidence pointers and reason codes; statuses are not inferred from filenames or dataset-card marketing.
- **EDM-M02 Reconciliation.** Independently reconcile source totals and row grains across Bronze immutable originals, Silver tables, Gold summaries and displayed records. Preserve null, nil, absent, unfiled, not-applicable and redacted distinctions; preserve revisions/corrections without overwriting previous vintages.
- **EDM-M03 Empirical isolation.** Replace/quarantine synthetic data falsely represented as empirical, including existing hard-coded 2026 finance/margin/donor sample outputs; no fixed coefficients, invented standard errors, p-values or donor-Gini population claims in production. Keep illustrative fixtures in labelled test/research namespaces.
- **EDM-M04 Election source versions.** Render and export only a single coherent verified source vintage per public view. Do not mix 2026 preliminary and subsequent official counts without explicit comparison labels. Independently verify statutory allocation and excluded-party denominator handling.
- **EDM-M05 Continuous verified refresh.** Maintain source publication time, successfully captured time, validated time, deployed time, source/release SHA and status. Run bounded source-drift checks, publish only validated changes, signal staleness/failures, roll back to last independently verified release; no false real-time claim.
- **EDM-M06 Historical finance.** Extract and reconcile eligible annual party donation/loan returns (archive asserts 1996–2025), party expense returns, candidate financial returns and registered promoter returns. Record observed versus expected coverage by election and return class; do not count one transaction twice when present in multiple filings.
- **EDM-M07 Financial accounting.** Separate donations, in-kind gifts, anonymous and protected donations, loans, repayments, income, campaign spending, organisational spending, candidate spending, third-party advertising, broadcast allocations and actual advertising expenditure. Effective-dated thresholds and regulatory periods required; do not combine incompatible scopes.
- **EDM-M08 Canonical identities.** Maintain stable party/candidate/electorate/org IDs and effective-dated aliases, reviewed donor/company matches, and a logged unresolved-entity state. For historic boundaries, use source-version crosswalks with unallocated counts.
- **EDM-M09 Privacy and rights.** Assess per-source reuse rights and public-record status; apply minimisation, false-positive-safe entity resolution and documented redaction/omission for sensitive disclosures. No voter-level sensitive profiling or targeting.
- **EDM-M10 Accessibility and inspectability.** Each public metric provides denominator, units, scope, source link, source vintage, computation revision, methodology and downloadable underlying observations; mobile and keyboard/screen-reader verification required.
- **EDM-M11 Assurance and release separation.** For **source/document PR admission and code integration**, require exact repo-local CPython 3.15.1, locked dependencies, Ruff, basedpyright, tests/property/fuzz, security, licence/SBOM, mutation/release gates as applicable, independent exact-head review, required hosted checks and protected receiving-main verification. For a **separately authorised external Hugging Face publication or outcome-acceptance claim**, additionally require independently verified actual served dataset/Space source-to-revision/hash parity, timestamps, accessibility/exports and rollback. A green code PR does not authorise publication; a planning PR does not require live publication to become mergeable. Preserve all existing native/publication holds.
- **EDM-M12 Future filings.** Add event-driven discovery for official results and subsequent party/candidate/promoter returns with independent filing dates; no 'complete 2026 expenses' assertion while returns are outstanding.

- **EDM-M13 Joined-outcome traceability.** Every public research question maps to a registered outcome OID, required datasets and their grains/keys, compatible time/geo-vintage bridges, deterministic join metrics, missingness, original source rights and evidence receipts. Require independent aggregation and cardinality controls; never silently multiply rows or borrow facts from incompatible vintages.
- **EDM-M14 News issue provenance.** Use dated reporting to discover neutral research questions, not as a substitute for primary-source data. Preserve source/outlet/title/date only as permitted, link to verified Commission/Stats NZ etc. facts, distinguish policy statements from enacted law and forbid unsupported misconduct or causal conclusions. Keep a versioned issue-to-OID matrix.

## Should: maximal analytical value

- **EDM-S01** Reprocess archived 2023/2020/2017 voting-place files into complete coverage-aware datasets; harmonise 1996–2026 votes/turnout, rule and electorate boundary vintages, and known missing years.
- **EDM-S02** Produce nominal and CPI-deflated historical donations/spend per election, party vote, elected seat and enrolled voter, preserving actual spend scope, denominator and historical regulatory changes.
- **EDM-S03** Publish defensible disclosed-donor concentration (top-k, top-share) and bounded Gini where lower-tail donations are not itemised; never estimate an all-donor Gini from only large donations.
- **EDM-S04** Use poll fieldwork/vintage, NZES survey methodology and geographic population weights for historical analysis; avoid ecological-to-individual claims.
- **EDM-S05** Onboard eligible 2026 major-party donations, broadcaster allocations, registered promoters, digital ad libraries and corporate/charity identifiers after source/rights/quality approval.
- **EDM-S06** Release six connected dashboard surfaces with filters, source receipts, readable version diff, dataset exports and reproducible figure bundles.
- **EDM-S07** For empirical causal/forecast models require pre-specified estimand, sample/grain, identification assumptions, uncertainty, placebo/robustness and independent reference/holdout evaluation. SHAP is noncausal by default.
- **EDM-S08** Publish a coverage/quality dashboard (expected vs captured vs parsed vs reconciled; failed viewer/parquet partitions; freshness lag by source).
- **EDM-S09** Provide source change alerts with de-duplicated receipts and reasonable refresh budgets; no external services or new credentials without separate authority.

- **EDM-S10 Outcome usability.** For each OID show answerable/partial/blocked/research-only status and named missing evidence, accessible dated source references, published method, subgroup/temporal coverage and version history; offer publishable one-question data extracts when qualified.

## Could: later research

- **EDM-C01** Link public MPs' interest declarations, Hansard, bill/division and procurement/charities data to verified organisational identities, explicitly as context and associations only.
- **EDM-C02** Add local-election comparators, reviewed manifesto/policy ontologies, and reproducible transparent text analysis.
- **EDM-C03** Add privacy-preserving research datasets and probabilistic entity resolution if independent accuracy/fairness tests and rights permit.

## Won't in the current implementation boundary

- Do not activate new crawlers, scrape around access challenges, alter publication or source permissions merely by recording this track.
- Do not infer corruption, bribery, preferential treatment or donor influence from funding–policy correlation or entity match.
- Do not present raw returns, snapshots, synthetic output, scenario forecasts, or model narrative as official validated derived facts without applicable gates.
- Do not duplicate shared Conductor ownership, bypass the sole PR coordinator, merge without current required checks, or mark implementation complete from a planning-only PR.
