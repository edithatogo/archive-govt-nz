# Health appropriations source-health and vintage-state report

This report rolls up the pinned resource and context censuses. It records
states and evidence boundaries; it does not approve rights, infer complete
calendars, or establish that every possible source vintage was discovered.

## Resource census

- Resources: 1
- Dispositions: `captured` 1
- Capture reconciliation: `capture_manifest_and_bronze_objects_verified` (1 Bronze objects verified)

| Source ID | Family | Inventory state | Recorded vintage/title | Rights state | Capture rights result | Temporal state | Layout state |
|---|---|---|---|---|---|---|---|
| treasury-vote-health-pdf-2013-14-estimates | treasury_vote_health_document | captured | Vote Health - The Estimates of Appropriations 2013/14 | policy_reference_recorded_not_evaluated | eligible | not_assessed_source_calendar_not_in_census | not_assessed_per_source_baseline_not_in_census |

## Context series and vintage states

- Context series/vintages: 11
- Qualification states: `unqualified` 11

| Series ID | Family | Source series | Vintage | Period description | Qualification | Rights | Temporal state | Layout state | Known gaps |
|---|---|---|---|---|---|---|---|---|---|
| core-crown-befu-2026 | core_crown | Core Crown Expense Tables!D26 / Core Crown expenses | BEFU-2026 | 2021-2030: Actual 2021-2025, Forecast 2026-2030; financial-year basis unverified | unqualified | not_evaluated | source_extent_recorded_calendar_completeness_not_assessed | not_assessed_per_vintage_baseline_not_in_census | financial_year_basis_unverified; formula_cache_not_qualified |
| core-crown-hyefu-2025 | core_crown | Core Crown Expense Tables!D25 / Core Crown expenses | HYEFU-2025 | 2021-2030: Actual 2021-2025, Forecast 2026-2030; financial-year basis unverified | unqualified | not_evaluated | source_extent_recorded_calendar_completeness_not_assessed | not_assessed_per_vintage_baseline_not_in_census | canonical_total_adapter_missing; financial_year_basis_unverified; formula_cache_not_qualified |
| core_crown-fiscal-2025 | core_crown | Spending!D4 / Core Crown Expenses | Fiscal-Time-Series-1972-2025 | 1994-2025; 32 annual cells; June year basis carried from A23 through old-GAAP A27 | unqualified | not_evaluated | source_extent_recorded_calendar_completeness_not_assessed | not_assessed_per_vintage_baseline_not_in_census | canonical_projection_receipt_recorded_outside_metadata_census; consolidation_and_accounting_comparability_not_qualified; no_year_only_or_cross_basis_join |
| cpi-2026q2 | cpi | CPIQ.SE9A | Stats-NZ-CPI-2026-Q2 | quarter-ending YYYY.MM; source observations span 1914Q2–2026Q2, 449 selected rows, 422 numeric and 27 NA | unqualified | not_evaluated | source_extent_recorded_calendar_completeness_not_assessed | not_assessed_per_vintage_baseline_not_in_census | fiscal_aggregation_not_qualified; household_prices_not_health_input_costs |
| gdp-stats-2026q1 | gdp | SNEQ / SG03AB01GE00S900 (separate publisher prefix/reference) | StatsNZ-GDP-2026Q1 | Captured March 2026 vintage: 60 quarters June 2011 through March 2026; June 2026 successor, published 17 September 2026, is a separate 61-quarter vintage, not spliced into this series | unqualified | not_evaluated | source_extent_recorded_calendar_completeness_not_assessed | not_assessed_per_vintage_baseline_not_in_census | annual_aggregation_not_qualified; canonical_projection_not_qualified; currency_code_unverified; successor_june_2026_vintage_recorded_separately |
| gdp-stats-2026q2 | gdp | SNEQ / SG03AB01GE00S900 (separate publisher prefix/reference) | StatsNZ-GDP-2026Q2 | 61 quarterly observations, June 2011 through June 2026; source row describes quarterly coverage; completeness not independently assessed | unqualified | not_evaluated | source_extent_recorded_calendar_completeness_not_assessed | not_assessed_per_vintage_baseline_not_in_census | annual_aggregation_not_qualified; canonical_projection_not_qualified; currency_code_unverified; rights_terms_observed_not_independently_adjudicated |
| gdp-treasury-2025 | gdp | Nominal GDP / C3 (publisher sheet selector) | Fiscal-Time-Series-1972-2025 | 1972-2025; March years through 1989, June years from 1990 | unqualified | not_evaluated | source_extent_recorded_calendar_completeness_not_assessed | not_assessed_per_vintage_baseline_not_in_census | cross_vintage_splicing_not_qualified; full_derived_measure_qualification_pending |
| population-hlfs-rejected | population | unqualified HLFS working-age series | HLFS June 2026 | June 2026 release; exact suitable all-age series absent | unqualified | not_evaluated | source_extent_recorded_calendar_completeness_not_assessed | not_assessed_per_vintage_baseline_not_in_census | wrong_population_universe |
| population-national-annual-mean | population | DPE056AA — Estimated Resident Population by Age and Sex (1991+) (Annual-Jun) | Stats NZ release 2026-08-18; current census basis 2023-06-30; provisional/revision status retained | Annual-Jun Mean year ended; 1991–2026; 36 source rows with flags, one unavailable '..' token and two provisional 'P' statuses | unqualified | not_evaluated | source_extent_recorded_calendar_completeness_not_assessed | not_assessed_per_vintage_baseline_not_in_census | analytical_selection_and_denominator_approval_not_selected; export_is_hash_pinned_in_population_annual_context_not_source_census; historical_export_vintages_not_retained; one_unavailable_source_observation_and_two_provisional_statuses; resource_rights_not_evaluated; transport_http_warc_receipt_unavailable |
| qes-2026q2 | qes | QEMQ.SASZ9A | QES-2026-Q2 | nine quarters June 2024 through June 2026 | unqualified | not_evaluated | source_extent_recorded_calendar_completeness_not_assessed | not_assessed_per_vintage_baseline_not_in_census | annual_join_not_qualified; currency_sex_adjustment_not_supplied; not_selected_as_deflator |
| total_crown-fiscal-2025 | total_crown | Spending!E4 / Total Crown Expenses | Fiscal-Time-Series-1972-2025 | 1997-2025; 29 annual cells; June years | unqualified | not_evaluated | source_extent_recorded_calendar_completeness_not_assessed | not_assessed_per_vintage_baseline_not_in_census | canonical_projection_receipt_recorded_outside_metadata_census; consolidation_and_accounting_comparability_not_qualified; no_year_only_or_cross_basis_join |

## Limits

- Resource states and policy references are copied from the pinned censuses; rights are not approved by this report.
- Temporal descriptions are source-census text; calendar completeness and cross-source period alignment are not assessed.
- Structural PDF baselines record page geometry and resources only; text, tables and semantic layout are not assessed. Other source families without a supplied baseline remain unassessed.
- Capture-manifest rights classifications are retained workflow evidence, not an independent legal assessment.
- This report does not certify discovery, vintage coverage, analytical comparability, or reconciliation completeness.
