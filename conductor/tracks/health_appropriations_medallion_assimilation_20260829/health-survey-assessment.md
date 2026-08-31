# Optional Health Survey aggregate linkage assessment

Metadata-only assessment, 2026-08-31. Decision: retain as a non-blocking S-05
candidate; do not yet acquire, normalize, federate or publish survey data.
No CSV, ZIP, workbook, PDF, microdata or respondent record was downloaded.

## Proposed analytical question

Could a descriptive national time series place published measures of access
barriers beside source-faithful health-spending observations? Start with adult
GP affordability, appointment delay and prescription affordability, not a causal
effect estimate. Survey denominators are not substitutes for the national
population series needed for spending per capita. Regional funding allocations
cannot be inferred from survey geography.

## Primary-source evidence

The [2024/25 annual release](https://www.health.govt.nz/publications/annual-update-of-key-results-202425-new-zealand-health-survey)
provides an official explorer and describes CSV export. It distinguishes adult
and child populations and notes questionnaire-related series breaks. A CSV's
actual columns, definition identifiers and release pin remain uninspected.

The [regional release](https://www.health.govt.nz/publications/regional-data-release-new-zealand-health-survey)
instead pools three survey years. It separates crude from age-standardised
estimates, includes uncertainty and quality flags, and documents changes to
weights and population bases. Ethnic groups overlap under total-response
classification. These are not single-year additive counts; suppressed values
must not become zero or be reverse-engineered. National annual and regional
pooled products require distinct record identities and comparison rules.

The Ministry's [correction notice](https://www.health.govt.nz/monitoring-statistics/surveys/new-zealand-health-survey/publications/202324-survey-publications/corrections-made-to-202324-data)
states that the earlier 2023/24 release was revised, including access-barrier
items. Therefore an observation needs both survey period and publication/revision
vintage; an updated explorer must not silently replace archived earlier bytes.

The [methodology landing page](https://www.health.govt.nz/publications/methodology-report-202425-new-zealand-health-survey)
identifies a sampled, weighted survey and explicitly labels that report CC BY4.0.
The [website copyright policy](https://www.health.govt.nz/about-this-site/copyright)
has a CC BY4.0 default with exclusions for graphics, logos and third-party work.
Neither observation is blanket qualification of an uninspected export or its
separately hosted application. No resource-level eligibility decision is made.

## Conditions before implementation

1. Select and pin an exact official aggregate export and its dictionary,
   methodology and correction metadata; confirm resource-specific rights and
   access conditions before acquisition. No login, hidden endpoints or access
   workarounds; no IDI/CURF or other unit-record data.
2. Retain complete original exports in Bronze, including superseded versions.
   Silver must preserve indicator definition, population/age eligibility,
   survey period, release vintage, geography/version, adjustment basis, units,
   confidence bounds and source quality/suppression flags without imputation.
3. Use explicit contextual links only in Gold/Platinum. Do not align a rolling
   pool to one fiscal year, pool annual and regional observations, infer funding
   effects, or substitute survey totals for the spending denominator.
4. Add negative tests for missing dictionaries, changed definitions, duplicate
   vintages, suppressed cells, incompatible periods and adjustment bases before
   a local pilot. New candidate/HF publication remains separately gated.

The evaluation is complete at this metadata scope. S-05 acquisition and the
conditional Phase5.3 integration remain pending and must not delay Must work.
