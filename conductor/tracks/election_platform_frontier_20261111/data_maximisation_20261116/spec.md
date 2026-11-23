# Technical design — election data maximisation

## Principle

**Archive once, verify by source and vintage, transform once, publish many.** Extend existing `archive_govt_nz` Bronze/CAS, Silver, Gold, Arrow/Parquet, DuckDB/Polars, Pydantic/JSON Schema and static Hugging Face deployment. Reuse existing CLI/assurance/manifest infrastructure; no second ETL or cryptography framework.

## Canonical interoperable contracts (design targets)

1. `ElectionSourceAsset`: `source_id, source_url, publisher, source_type, reporting_period, election_year?, party_id?, candidate_id?, electorate_id?, published_at?, captured_at_utc?, retrieval_method, content_hash, byte_count, licence, rights_status, revision_of?, lifecycle_state, receipt_id, access_disposition`.
2. `ElectionSourceRelease`: `release_id, release_vintage, preliminary_or_official, relevant_source_hashes, schema_versions, code_sha, validated_at_utc, published_at_utc?, served_hf_revision?, previous_release_id, parity_evidence`.
3. `FinanceDisclosure`: `disclosure_id, source_asset_id, filing_id, disclosure_type, donor/creditor_id?, party_id?, candidate_id?, promoter_id?, received_at?, declared_at?, reported_at?, amount_nzd?, currency?, in_kind, donor_display_name?, reporting_scope, effective_rule_id, status, amendment_of?, row_source_locator`. Keep raw declaration and canonical entity match separately.
4. `FinanceExpense`: `source_asset_id, filing_id, expenditure_type, advertiser/payer/beneficiary ids?, electorate_id?, amount_or_range, allocation_or_actual, regulated_period, transaction_vintage, reconciliation_status`. Advertising platforms' range data remain ranges.
5. `ElectionObservation`: `election_year, source_vintage, boundary_id, party/candidate_id, vote_kind, votes, denominator_id, vote_place_id?, source_receipt`.
6. `EntityMatch`: `left_source_id, right_source_id, match_kind, confidence, evidence, review_status, valid_from?, valid_to?`. No unreviewed fuzzy link published as identity.
7. `DerivedMeasure`: `name, numerator, denominator, unit, cohort, reported_currency_basis, cpi_base_period?, source_release_ids, transform_sha, result_kind, limitations`.

Do not force all these into one JSON schema initially. Select the smallest first-source cohort, add conformance tests, then expand through versioned migrations with documented compatibility.

## Finance metric definitions and exclusions

- Donations to a party are **not** party election spending; loans are not gifts; broadcasting allocations are not actual expenditure. Candidate totals, party totals and third-party promoter totals are distinct reporting scopes and may overlap real-world advertising.
- Cost-per-vote = eligible documented **election advertising/spending amount** for explicitly stated entities and reporting period / valid party votes (or candidate votes for candidate spending). Do not call this a causal return on investment.
- Inflation adjustment uses Stats NZ source vintage, CPI series, explicit base quarter/year and a published deflator; do not compare nominal and real values without labels.
- Donor metrics report disclosure coverage and threshold changes (including years with unobserved micro-donations); offer observed top-1/top-5 shares and uncertainty/bounds, not a fabricated all-donor Gini.
- Financial timeline distinguishes donation receipt date from reporting/disclosure date and app ingestion date. Annual and immediate disclosure duplicates resolve to one transaction only when supported by evidence; otherwise flag a possible duplicate without collapsing it.
- Payment and recipient identities use exact documented names; privacy policy protects unpublished/suppressed identities. Legal disclosure thresholds and campaign caps are effective-dated, not constants in model source.
- Observed/derived/estimated/counterfactual/experimental are exclusive public result classes. RDD/IV require actual fitted data, valid running-variable/treatment/instrument design and diagnostics, and may return `not_estimated` rather than hard-coded fallback.

## Release and refresh design

Source-check cadence is a **proposal**, not active automation: election count daily (hourly around official declaration); major donations daily; annual/candidate/promoter returns daily within expected filing windows and weekly otherwise; older archives weekly. Check `ETag`/`Last-Modified` where reliable, compare hashes and provenance otherwise; avoid unauthorised scraping of blocked endpoints. Revisions are append-only. Every published release must pass source->Silver->Gold->HTML/export checks and independent on-host byte/revision readback. Maintain last known good release on failure, explicit `stale`/holding status and a bounded operator alert. Display source publication time, successful captured time, validation time and deployed time in NZST/NZDT with machine-readable UTC timestamps and explicit offsets.

## Public consumers (not yet implemented)

1. **Results Live:** source-vintage election results, comparison, turnout, threshold/overhang arithmetic, geographical election returns.
2. **Political Finance:** party/candidate/promoter finances, timeline, donor concentration, loans, comparative real/nominal amounts, declared-total reconciliation.
3. **Campaign Advertising:** registered promoters, broadcasting allocation/actual, Meta/Google political advertising with spend intervals and limitations.
4. **Historical Election Atlas:** 1996–2026 and local elections when sourced; boundary crosswalks; voting-place coverage; enrolment/census and spatial trends.
5. **Polling and Research:** NZES comparability, poll fieldwork/house effects, calibration, descriptive and independently qualified analytical models.
6. **Parliamentary Accountability:** parliamentary register interests, legislation/divisions/Hansard, organisation network and public contracts, with conservative inference boundaries.

All products share stable filters (year, electorate/boundary vintage, party, source vintage, financial reporting class), link to source and analytical reproducibility receipts and accessible CSV/Parquet/Arrow exports. Make optional or not-yet-sourced data visibly unavailable, never silently empty.

## Acceptance and engineering

Use [requirements](requirements.md), executable [plan](plan.md) and [source register](source-register.md). Confirm rights, eligibility, source totals, manifest hashes, schema row-level invariants, mutation/negative tests, CVE/license gates, performance budgets and actual browser accessibility; separate static offline qualification from external publication and natural recurrence. No staging or release permission follows from this planning document.
