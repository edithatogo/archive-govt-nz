# CPI/QES source context and numeric admission

Scoped Phase 1.2 / M-02, M-06, M-12 result: exact June-2026 CPI/QES
profiles are enumerated in `price-wage-context.json`. The new read-only
`price_wage_context.admit_retained` validates that definition and delegates to
the existing public CPI/QES adapter with `dry_run=True`. It adds no parser,
capture, derivative writer, analytical join or rights decision.

## Definitions and evidence strength

| Profile | Retained numeric source | Supplemental official observation |
| --- | --- | --- |
| CPIQ.SE9A | Nine-column CPI CSV; All groups, New Zealand; quarterly Index, source status FINAL; 449 selected rows from 1914Q2 through 2026Q2, including 27 NA | Infoshare CPI009AA; magnitude Units, unit Index; June 2017 quarter = 1000; publisher updated 21 July 2026 at 10:45am, timezone not supplied |
| QEMQ.SASZ9A | QES June-2026 workbook, Table 8, A8 prefix QEMQ / P8 SASZ9A; total-sector ordinary-time hourly earnings, earnings divided by paid hours; nine quarterly levels from 2024Q2 through 2026Q2; source label ($) | Infoshare QEM003AA; Total All Sectors - Total Both Sexes - Ordinary Time Hourly; magnitude Units, unit $; publisher updated 5 August 2026 at 10:45am, timezone not supplied |

The retained CSV/workbook bytes and existing Silver manifests were available
for local hash verification and native-adapter replay. The supplemental
Infoshare responses were observed earlier on 7 September 2026 but **not
retained**. Their digests record historical author observations, not independently
replayable evidence. The register explicitly preserves that distinction; neither
its validation nor native numeric admission upgrades supplemental qualification.
An observed current endpoint value match is not proof of historical-series or
methodology equivalence. No raw values or response bodies enter Git.

The existing source URLs in the JSON are stable version-specific Stats NZ
download locators, already bound to retained hashes in `context-census.json`.
The [Infoshare search page](https://infoshare.stats.govt.nz/SearchPage.aspx)
is a catalogue entry, **not** a static exact-series export URL. Searching the
exact identifiers, selecting the matching result and 2026Q2, and submitting
the CSV selection form produced numeric responses (HTTP 200, text/csv).
Selection/export uses session-bound POST state and transient `pxID` values;
no stable direct export URL or reusable session token is claimed. Response
hashes and lengths are in `price-wage-context.validation.json`.

## Adjustment, unit and base limitations

CPI's observed metadata says fresh fruit and vegetables were seasonally
adjusted through 2006Q2 and seasonally unadjusted from 2006Q3. This is a
component-history statement, not a uniform whole-history adjustment label.
It also notes exclusion of residential sections and interest from 1999Q3,
and that percentage changes use unrounded pre-2017Q2 index numbers. This
contract admits quarterly index levels only; it does not recalculate changes,
splice vintages, rebase, or equate household prices with health input costs.
The observed 2017Q2 = 1000 base remains supplemental; the native CPI receipt's
`index_base: null` and quality caveats are not overwritten.

QES is a dollar-per-paid-hour earnings level, not a constant-quality wage index;
an index base is not applicable. The $ label does not independently establish
an ISO currency code. Neither retained Table 8 nor the exact-series Infoshare
response supplies an adjustment label. Seasonally adjusted/trend labels on
other workbook tables must not be transferred to Table 8. Table 9 is a distinct
selection and cannot replace Table 8. Both-sexes context is supplemental only:
the existing native currency/sex/adjustment unknown flags remain unchanged.

## Admission and review

Every definition field is required and strictly validated against the reviewed
profile. Mixed hashes, URLs, vintages, units, bases, selectors and semantic
upgrades fail closed. Mutated model instances are revalidated before use.
The wrapper uses the native bounded hash/layout/literal-value validation;
wrong bytes and occupied or dangling-symlink probe paths fail. Native errors
propagate. The original native receipt is returned unchanged, beside—not
merged with—the supplemental definition. `preflight_passed` means numeric
preflight, never analytical eligibility or source rights.

TDD began with expected missing-module collection failure. Focused definition,
CPI and QES suites now pass: **109 tests; 100% of 56 module statements and
4 branches**. All-field semantic-drift, extra-field, model-mutation, adapter
dispatch, no-write, wrong-byte and path-boundary regressions are included.
Ruff lint/format and strict Pyright pass. A local read-only replay against both
retained originals matched native counts and source context to their existing
manifests; six existing derivative hashes were checked, not regenerated.
Original hashes remained unchanged. This is native-adapter replay, not an
independent alternative-parser or unretained-HTTP replay claim.

Conductor review: no in-scope unresolved correctness finding. Source-native
unknowns, separate evidence strength and no-promotion semantics were explicitly
checked. Existing adapters and shared capture/plan/runlog/metadata files are
unchanged. Full programme harness, hosted validation and integration belong to
the parent and were not run here.

## Remaining tasks, separately bounded

1. **Metadata evidence capture:** the capture owner can retain the exact
   Infoshare responses and HTTP context for independent replay. This does not
   block the already-retained numeric sources' preflight.
2. **QES semantic evidence:** qualify ISO currency and adjustment from exact,
   series-bound official evidence; do not invent them from other tables.
3. **Analytical qualification:** separately approve CPI/earnings deflator use,
   fiscal-year aggregation/weighting, output base and source-vintage joins.
   The approved M-12/design contracts require these identities but do not
   supply these choices. No analytical choice is needed for this admission
   slice, and none has been made. Population denominator choice stays separate.

Proposed parent status clause (no shared plan edited):

> Enumerate June-2026 CPIQ.SE9A and QEMQ.SASZ9A source definitions and validate
> retained numeric admission through existing adapters, preserving supplemental
> unretained metadata, source-native unknowns and unselected analytical joins.

This scoped clause is complete locally. It does not complete the broader
Phase 1.2 census, Phase 5.3 promotion, or Phase 6 analytical qualification.

## Reproduction

From the isolated checkout, use the existing environment (no dependency change):

```sh
PYTHONPATH=src /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m pytest tests/domains/health_appropriations/test_price_wage_context.py tests/domains/health_appropriations/test_cpi.py tests/domains/health_appropriations/test_qes.py -q --cov=archive_govt_nz.domains.health_appropriations.price_wage_context --cov-branch --cov-report=term-missing
/Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/ruff check src/archive_govt_nz/domains/health_appropriations/price_wage_context.py tests/domains/health_appropriations/test_price_wage_context.py
/Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/ruff format --check src/archive_govt_nz/domains/health_appropriations/price_wage_context.py tests/domains/health_appropriations/test_price_wage_context.py
/Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/pyright src/archive_govt_nz/domains/health_appropriations/price_wage_context.py tests/domains/health_appropriations/test_price_wage_context.py
```

For retained-source replay, load each JSON definition with
`PriceWageContext.model_validate`, resolve the existing
`bronze-cas/sha256/<first-two>/<source_sha256>` object below the external
health-appropriations archive, and call `admit_retained` with a nonexistent
child path of a temporary directory. Compare `native_receipt` counts,
source locator, vintage and observation time with the hash-pinned existing
manifest listed in the validation receipt. No output directory is created.
