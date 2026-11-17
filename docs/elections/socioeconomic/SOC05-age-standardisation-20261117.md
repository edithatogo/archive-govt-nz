# SOC05 direct age-standardised turnout — 17 November 2026

Status: real-data descriptive candidate; no causal estimate, independent-review acceptance, native qualification or deployment. Existing SOC author/I1/sole coordinator ownership is unchanged.

## Implemented and executed

`tools/standardise_soc_turnout.py` consumes the independently pinned retained `turnout-age.json` (SHA2562a257681b105e542e568340d0a64120cc1ed56113bd0ae891bcfd3639c24b2bc), not a new download. All72 electorates and11 age strata must be present, with unique identities, nonzero registered-elector denominators, the expected2020 boundaries/2023 election, original workbook identity and exact national count reconciliation.

It creates144 rows: each electorate's observed age-specific turnout is directly standardised to (a) the national enrolled-elector age distribution and (b) the corresponding general/Maori roll-system age distribution. It retains raw turnout, adjusted turnout, the difference in percentage points, reference counts and source hashes. Census resident counts are not substituted for registered electors. The two standardisations are sensitivity alternatives, not additive observations.

Formula: `100 * sum(reference_age_enrolled / reference_total_enrolled * area_age_voters / area_age_enrolled)`.

12 local CPython3.13.5 tests passed. All144 results independently match exact Fraction arithmetic to10 decimal places; duplicate/missing strata, boundary/source/name drift, invalid denominator, national-total corruption and tampered input bytes fail. Tests use the real retained dataset and mathematical references; this is author verification, not separate reviewer approval.

```
SOC_NORMALISED=/path/to/normalised python tools/verify_soc_age_standardisation.py -v
python tools/standardise_soc_turnout.py --input /path/to/normalised/turnout-age.json --output /new/output/path
```

Interpretation: descriptive area-level age-composition adjustment, not a forecast, individual voting inference or causal effect. Other socioeconomic, spatial and measurement differences remain. No confidence interval or statistical-significance claim is supplied.

Required native3.15.1/full repository, quality/security/current-head checks, shared adapter admission and independent review remain pending. This standalone analytical file does not import another unmerged PR's implementation. Its data dependency is the qualified retained SOC02 output; public adoption awaits the existing coordinator. Existing CI, Space and source-acquisition workflows were not changed or dispatched.
