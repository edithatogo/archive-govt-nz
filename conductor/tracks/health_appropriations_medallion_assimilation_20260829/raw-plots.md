# Source-derived plot contract and delivery route

These are new local derivatives, not replacements for the six donor PNGs.
The standalone PNG surface is the approved legacy-function replacement; no
dashboard, hosted widget or new publication is implied. Gold input manifest
pins, five typed tables, exact records and lineage remain the authority.

## Chart map

| Legacy filename stem | Question and supported interpretation | Form and input sufficiency |
| --- | --- | --- |
| historical_health_spending_nominal | How did nominal recorded spending vary? Levels are observations, not real purchasing power or one uninterrupted accounting basis. | Segmented line, 53 annual observations; isolate unknown bases/periods and split gaps. |
| historical_health_spending_yoy_growth | Which consecutive observations support nominal growth? Missing comparisons are not zero growth. | Bars, 48 comparable observations and five reason-coded omissions. |
| health_spending_vs_gdp | What is Health spending divided by same-source, vintage and period-end nominal GDP? Period starts and institutional scope remain unverified. | Segmented line, 53 aligned ratios; no new denominator joins. |
| recent_appropriations_functional_breakdown_2025_Estimated_Actual | How do the four source classifications compare for 2025 Estimated Actual? Labels are not a new classification mapping. | Horizontal bars, four categories; zero baseline and negative values retained. |
| recent_trends_health_classification | How do the six discrete source-year Health values compare? Actuals, Estimated Actual and Main Estimates are different amount types. | Grouped annual bars; six annual points are too sparse for a continuous trend claim. |
| recent_trends_no_classification | How do the six unclassified source-year values compare? No category reassignment is inferred. | Grouped annual bars, distinct amount types, fiscal basis unverified. |

The targeted sufficiency check used all 16 Gold Budget groups: each of the
last two views has Actuals 2021-2024, Estimated Actual 2025 and Main Estimates
2026. There is no finer time grain in these verified inputs. Preserve the
legacy filenames but explicitly record the two line-to-bar rendering changes;
do not imply pixel parity with donor plots or add unverified source years.

## Rendering and QA contract

- Static Matplotlib Agg, 14 by 8 inches, 100 dpi, DejaVu Sans, explicit PNG
  metadata and recorded Matplotlib/Pillow/FreeType versions.
- Single blue palette root with shades, distinct marker/hatch patterns and
  direct axis labels; white background, charcoal text and quiet grey grids.
  Signs use a zero line and open negative bars, never red/green alone.
- Exact decimal strings and source input IDs remain in the contract; conversion
  to finite binary floats happens only for display. Missing comparisons are
  omitted with reasons; empty views say no eligible observations.
- Lines never bridge a source/vintage/period/accounting-basis change or a missing
  year. Budget values are grouped by source/vintage/amount type, not pooled.
- Preserve complete original Gold inputs. New output directories are exclusive;
  failed partial outputs remain with a redacted failure receipt.
- Before delivery: compare independent PNG builds and inspect the exported
  images for label clipping, overlapping marks, signs, honest axes and source
  context.

## Local execution and visual QA

The dry-run-first `health-appropriations-render-plots` command takes `--gold-dir`,
`--manifest-sha256`, `--output-dir` and optional `--no-dry-run`.
It checks all eight Gold files, Arrow schemas, counts, input-ID closure and
bounded snapshots before creating a separate directory. Successful output is
six PNGs, exact `CONTRACTS.json` and `MANIFEST.json`; partial failure retains
bytes and a redacted receipt. Ambient Matplotlib settings cannot change output.

Retained root: `gold/raw-plots-20260831-v2` beneath the external Health store.
Manifest: `a04b1b8785d7a4da67ad1b83d6449592838ed0359de792368bb8f150155786d2`.
Three independent builds match all eight files, including the post-preflight-fix
build. Matplotlib 3.11.1, Pillow 12.3.0,
FreeType 2.14.3, Agg; cross-version byte identity is not claimed.

Inspected the six exported views. V2 fixes crowded ticks, preserves numeric-year
gaps in growth bars, centers groups only within the same year/category, uses
contrasting hatch strokes and labels all four breakdown values exactly. Labels
fit, bars retain zero baselines and negative values, and unavailable growth is
not drawn as zero. The unchanged GDP-share PNG also matches the inspected V1
hash. V1 remains preserved as a superseded QA build, not an original rewrite.
All 48 focused reader/contract/renderer tests pass at 100% critical line/branch
coverage. Dry-run and rendering share the 10,000-point/24-series limits; two
red regression cases exposed and now guard the earlier preflight omission.

Current mutation evidence is 44/44 reader, 26/26 contract and 58/58 renderer
mutants killed, with zero survivors, timeouts or pardons and cold caches.
Coverage-guided selection was disabled. Renderer mutation uses the documented
18-test unit/protocol selection, excluding the two slow full-six-PNG integration
tests only from mutation subprocesses; both remain in the normal suite. Real
single-PNG encoding and all figure semantics are still tested under mutation.
This is not a claim of full-suite mutation execution.

Reader report SHA-256:
`bddf14e38306e763243a087be53ac0b11152f9d5e2a8a99ee4bf65c692c948bb`.
Contract evidence is the 26 contract mutations in combined report
`08ad874967fcce964899fcf243e4e9860de31b508d374d77770492b2a0dd5121`;
its 57 renderer mutations predate the preflight fix. Final renderer report:
`2a0a3be0f3f91d9fd39268510109e967969310f7ed499f64e3bd9482d3c9fb72`,
bound to source `cb9436182d3ceec24681e6dd6f9f10783c54351b6efd1b45eaef2ff4f96963cc`.
Whole-repository final assurance and hosted delivery are recorded separately.

Final isolated `./scripts/validate.sh` on functional commit `eeb6200` passed:
1,906 tests, 96.48% overall coverage, eight existing SQLite resource warnings,
40 schemas/30 representative documents, 70 Conductor tracks, 9/9 parity,
all native mutation/supply-chain gates and 111-component SBOM. Runtime controls:
`COVERAGE_CORE=ctrace PYTHON_JIT=0 PYTEST_XDIST_AUTO_NUM_WORKERS=4`.
CAS throughput was 391.42 MB/s against the unchanged 25.0 MB/s minimum.
PR #269 merged as `b149d3725165b4d4116e17452955c5602ac40ec4` at
2026-08-31T05:52:48Z after all seven checks passed on exact head
`4f405e2abfba2444b8906412a65f7c128a269a13` (CI run `33361422682`).
Health source and tests are unchanged at merge; whole-tree identity is not
claimed because main also contains unrelated CLI/dependency/FOI changes.

The visualization skill influenced sparse-series chart selection, explicit
palette/non-color distinctions and the requirement for final-image inspection.
Pure contracts and input verification alone do not complete six-plot parity.
