# GDP/Crown source-bound context and admission policy

Phase 1.2 / M-02, M-06, M-12 scoped result: six GDP/Crown selections now have
a deterministic source-bound register and a pure qualification contract.
`qualify_context` binds reviewed metadata to exact original bytes, under a
1 MiB limit. It does **not** parse or normalize a workbook. A caller-supplied
native receipt can only be matched to the exact quarterly GDP contract; that
match is expressly not execution attestation. `preflight_stats_gdp` separately
executes the existing GDP adapter read-only and checks its receipt. No new
workbook adapter, raw capture or canonical projection was introduced.

## Retained audit and distinct states

| Selection | Original evidence | Admission in this slice |
| --- | --- | --- |
| Stats NZ quarterly expenditure GDP | 60 literal facts, Table 1 C27:BJ27; 2011Q2–2026Q1; actual current prices; prefix SNEQ and reference SG03AB01GE00S900 remain separate | Existing native preflight passes: 60 facts, 900 lineage entries, 2,287 dispositions |
| Fiscal 2025 nominal GDP | C5:C58, 54 annual literals; March years 1972–1989, June years 1990–2025 | Existing retained historical package transport verified; semantic/currency qualification remains separate, not re-normalized |
| Fiscal 2025 core Crown | Spending D27:D58, 32 literal numeric cells, 1994–2025 | Reviewed metadata hash-bound; not admitted as new numeric facts: existing historical adapter selects Health/GDP only |
| Fiscal 2025 total Crown | Spending E30:E58, 29 literal numeric cells, 1997–2025 | Same explicit non-admission; never interchangeable with core Crown |
| BEFU 2026 core Crown total | Core Crown Expense Tables F26:O26; 10 formulas, all with stored numeric cache presence | Not admitted: cached values and freshness unqualified; existing forecast adapter selects Health only |
| HYEFU 2025 core Crown total | Core Crown Expense Tables F25:O25; 10 formulas, all with stored numeric cache presence | Same non-admission, preserved as a distinct vintage |

Every source URL, capture observation, vintage, hash, selector, literal unit,
period, amount type and reason-coded gap is in `gdp-crown-context.json`.
The original byte lengths are 49,887 (GDP), 116,265 (Fiscal), 193,830 (BEFU)
and 191,581 (HYEFU). All four hashes were verified before archival inspection
and remained unchanged. No network request was needed.

Inspection used existing bounded `inventory_workbook` and literal-token helper,
then `openpyxl` read-only, `data_only=False`, on byte snapshots. Existing
inventory's cache-state metadata reports presence/type only. Neither cached
amounts nor recalculated formulas were admitted. Original amounts were not
copied into Git. This extends the earlier `context-census.observation.json`
cache observation without retroactively rewriting that evidence.

The retained GDP manifest
`639b3c7da60f2afa1b860c5f6c8f1c4c0ae24bf17aa7af63bf8a06a1f6471b35`
and all three derivative hashes were verified. The public
`read_historical_snapshot` verified Fiscal's original plus manifest
`aee4578f1ee83f8c1ede63e36e840c6cd2140df8c6f463e71ec93da9e4e7d75a`
and its three derivative members: 108 Health/GDP facts, 1,164 lineage rows,
1,531 dispositions, zero selected rejections. Its 54 GDP facts are distinct
from the 60 quarterly GDP facts. This transport reader explicitly does not
claim source-semantic execution. No existing historical adapter was duplicated
merely to add another GDP reader.

## Semantic boundaries

Fiscal's literal unit is `$ millions`; the existing historical adapter emits
`NZD_millions`. The latter is preserved as a native transformation observation,
**not** independent source evidence for an ISO currency code. This context
contract leaves currency null. Stats GDP likewise retains `$(million)` and
null ISO currency. No existing fact or native receipt was overwritten.

Fiscal core Crown begins in old-GAAP at A27 (1994), inheriting June-year basis
from A23. IFRS starts at A30 (1997), PBE Standards at A38 (2005); total Crown
begins at A30. Spending column C Financial Net Expenditure and the percent-GDP
block at A68 are not Crown expense substitutes. Original annotated year labels
remain in the retained source: `*` on 1994–1996, `^` on 2001–2019, and `#` on
2019. Relevant notes are A60 (GAAP not backdated on IFRS), A61 (GST annotation),
A64 (total Crown inter-entity Income Related Rent Subsidy restatement), and
A65 (2019 PBE restatement). A total-Crown-specific note is not generalized to
core Crown merely because the year column is shared. No cross-basis or
consolidation equivalence is asserted.

Fiscal has no explicit Actual/Forecast row in these selections. Its historical
amounts are labelled `historical_as_published`, not upgraded to a supplied
Actual flag. BEFU/HYEFU explicitly label 2021–2025 Actual and 2026–2030 Forecast
at F6:O6 / F5:O5 respectively. Their financial-year and accounting-basis
qualification remains unresolved. Each total formula sums its own source
column (BEFU rows 8:24; HYEFU rows 7:23); no cache correctness/freshness or
analytical total was inferred from formula syntax or numeric cache presence.

Capture observation `2026-08-29T09:00:17Z` is not the historical derivative's
local processing observation `2026-08-31T12:26:32Z`, publication date, or
reference period. Stats GDP publication is 18 June 2026 for 2026Q1. No vintage
splice, annual aggregation, price conversion, fiscal-year equivalence or
denominator selection occurs.

## Validation and review

TDD began with the expected missing-module import failure. Review added a red
regression for a stale `native_preflight_required` gap after successful GDP
execution; the wrapper now removes only that resolved gap, preserving currency
and annual-join gaps. The paired validation receipt records focused tests,
coverage, cold unfiltered mutants and lint/types. No full harness or hosted
validation was run, and shared lifecycle records were not edited.

The register comparison tests preserve all six exact definitions. Negative
tests reject changed source bytes, unsupported profiles, oversized/non-byte
inputs, mixed or upgraded native receipts and wrong-profile success. Metadata
qualification never admits Crown numbers. Detached returned data cannot mutate
the reviewed register or caller's receipt. Conductor review found no remaining
in-scope correctness issue. New Crown normalization would be a separate
loss-accounted adapter task, not hidden inside this pure policy contract.

## Proposed parent clause and remaining work

> Qualify retained GDP/Crown metadata by original hash; replay the existing
> 60-fact quarterly GDP preflight and reject cross-profile numeric admission,
> preserving fiscal/core/total, vintage, period, currency and formula-cache gaps.

That clause is locally complete, not full M-12 analytical completion. Subsequent
tasks remain separately bounded: literal Crown fact/lineage adapter qualification;
forecast total formula/cache and period qualification; historical currency
evidence and semantic projection; then explicitly chosen analytical joins.
The metadata census is not globally blocked by those later tasks. No user
analytical choice is needed to apply this source-context policy.

## Focused commands

From this checkout, with the existing shared environment:

```sh
PYTHONPATH=src /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m pytest tests/domains/health_appropriations/test_gdp_crown_context.py tests/domains/health_appropriations/test_gdp.py tests/domains/health_appropriations/test_historical_snapshot.py -q --cov=archive_govt_nz.domains.health_appropriations.gdp_crown_context --cov-branch --cov-report=term-missing
PYTHONPATH=src /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m pytest tests/domains/health_appropriations/test_gdp_crown_context.py --gremlins --gremlin-targets=src/archive_govt_nz/domains/health_appropriations/gdp_crown_context.py --gremlin-report=json --gremlin-workers=2 --gremlin-no-coverage-filter --strict-pardons --max-pardons=0 --no-cov -q
/Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/ruff check src/archive_govt_nz/domains/health_appropriations/gdp_crown_context.py tests/domains/health_appropriations/test_gdp_crown_context.py
/Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/ruff format --check src/archive_govt_nz/domains/health_appropriations/gdp_crown_context.py tests/domains/health_appropriations/test_gdp_crown_context.py
/Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/pyright src/archive_govt_nz/domains/health_appropriations/gdp_crown_context.py tests/domains/health_appropriations/test_gdp_crown_context.py
```

For local replay, read each register source from the external archive's
`bronze-cas/sha256/<first-two>/<source_sha256>` and pass those bytes plus profile
ID to `qualify_context`. For Stats GDP call `preflight_stats_gdp` with that
source path and an unused temporary child path. It creates no output directory.
