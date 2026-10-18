# Track: New Zealand Health Appropriations Medallion Assimilation

## Overview

This approved, in-progress track implements zero-loss assimilation of the pinned
`nz_health_appropriations` donor into Archive Govt NZ. It extends the corpus
with directly relevant official fiscal/health series and defensible contextual
denominators, using a strict Bronze → Silver → Gold → Platinum contract.

The design retains all donor files and acquired originals as immutable Bronze
objects outside Git. It assigns typed records and lineage to Silver, rebuildable
analytics to Gold, and rights-aware metadata and publication to Platinum.
Completed preservation and publication receipts do not establish completion of
every planned record set, measure or operational workflow.

## Artifacts

- [SQLite inventory path and identifier repair](./sqlite-inventory-boundary.md)

- [Negative-fixture matrix](./negative-fixture-matrix.md)
- [JSON admission and readback validation](./normalization-admission-validation.json)

- [Exact record-set normalization prerequisite](./recordset-normalization.md)
- [Normalization validation receipt](./normalization-validation.json)

- [Metadata standards and verified local DCAT route](./metadata-standards-route.md)

- [Exclusive local resume execution](./resume-execution.md)
- [Pure local canonical provenance inventory](./local-provenance-inventory.md)

- [Pharmac/GDP operational extension](./source-operations-extension.md)
- [Forecast successor operations](./forecast-source-operations.md)
- [Explicit forecast source-validation preflight](./forecast-preflight.md)
- [Bounded source-profile CLI/MCP operations](./source-operations.md)
- [Exact quarterly GDP source profile](./gdp-profile.md)
- [Health analytical-context register](./analytical-context-register.md)
- [Source-context census](./context-census.md)
- [Source-context census data](./context-census.json)
- [June 2026 GDP release observation](./gdp-release-observation-20260930.json)
- [Context Gold GDP vintage evidence](./context-gold-gdp-vintages-20261002.md)
- [Context GDP June clean-room recovery receipt](./clean-room-recovery-20261002-context-gdp-june.json)
- [GDP-vintage Conductor phase 7 review receipt](./phase_7_gates-review-receipt-20261002-context-gdp-june.json)
- [Recovered BEFU Bronze object receipt](./bronze-object-recovery-20260930.json)
- [Source-health and recovery revalidation](./source-health-revalidation-20260930.json)
- [Whole-census source-health and vintage-state report](./source-health-report.md)
- [Machine-readable source-health report](./source-health-report.json)
- [Population census integration validation](./population-census-integration.json)

- [Exclusive local classification occurrence export](./classification-export.md)
- [Budget source-label classification occurrences](./budget-classification.md)
- [Fresh original-to-product replay and SQLite runtime drift](./originals-product-replay.md)

- [Pharmac medicines-budget HTML contract](./pharmac-cpb.md)
- [Additive eight-record-set structural contracts](./recordset-contracts.md)
- [Hash-bound Bronze adapter dispatch and validation](./adapter-dispatch.validation.json)
- [Named-column Budget workbook dispatch adapter validation](./budget-adapter.validation.json)
- [Budget revenue workbook dispatch adapter validation](./budget-revenue-adapter.validation.json)
- [Vote Health 2002/03 Part F revenue recovery](./vote-health-revenue-2002-03-20261003.md)
- [Vote Health 2002/03 Part F machine receipt](./vote-health-revenue-2002-03-20261003.json)
- [Vote Health 2002/03 overview headlines](./vote-health-estimates-overview-2002-03-20261003.md)
- [Vote Health 2002/03 overview machine receipt](./vote-health-estimates-overview-2002-03-20261003.json)
- [Vote Health 2004/05 overview headlines](./vote-health-estimates-overview-2004-05-20261003.md)
- [Vote Health 2004/05 overview phase review receipt](./phase_7_gates-review-receipt-20261003-vote-health-overview-2004-05.json)
- [Vote Health 2008/09 overview headlines](./vote-health-estimates-overview-2008-09-20261003.md)
- [Vote Health 2008/09 overview machine receipt](./vote-health-estimates-overview-2008-09-20261003.json)
- [Vote Health 2008/09 phase 7 review receipt](./phase_7_gates-review-receipt-20261003-vote-health-overview-2008-09.json)
- [Vote Health 2008/09 incremental capture request](./vote-health-estimates-overview-2008-09-capture-request.json)
- [Vote Health 2008/09 incremental capture receipt](./vote-health-estimates-overview-2008-09-capture.json)
- [Vote Health Supplementary Estimates 2005/06 overview totals](./vote-health-supplementary-2005-06-overview-totals-20261007.md)
- [Vote Health Supplementary Estimates 2005/06 machine evidence](./vote-health-supplementary-2005-06-overview-totals-20261007.json)
- [Vote Health Supplementary Estimates 2005/06 clean-room recovery](./clean-room-recovery-20261007-vote-health-2005-06.json)
- [Vote Health 2009/10 overview headlines](./vote-health-estimates-overview-2009-10-20261004.md)
- [Vote Health 2009/10 overview receipt](./vote-health-estimates-overview-2009-10-20261004.json)
- [Vote Health 2009/10 incremental capture request](./vote-health-estimates-overview-2009-10-capture-request.json)
- [Vote Health 2009/10 incremental capture receipt](./vote-health-estimates-overview-2009-10-capture.json)
- [Vote Health 2009/10 captured-source census addendum](./vote-health-estimates-overview-2009-10-census.json)
- [Vote Health 2009/10 source-health reconciliation](./source-health-report-20261004-vote-health-2009-10.md)
- [Vote Health 2009/10 source-health machine receipt](./source-health-report-20261004-vote-health-2009-10.json)
- [Vote Health 2010/11 overview headlines](./vote-health-estimates-overview-2010-11-20261004.md)
- [Vote Health 2010/11 overview machine receipt](./vote-health-estimates-overview-2010-11-20261004.json)
- [Vote Health 2010/11 incremental capture request](./vote-health-estimates-overview-2010-11-capture-request.json)
- [Vote Health 2010/11 incremental capture receipt](./vote-health-estimates-overview-2010-11-capture.json)
- [Vote Health 2010/11 captured-source census addendum](./vote-health-estimates-overview-2010-11-census.json)
- [Vote Health 2010/11 source-health reconciliation](./source-health-report-20261004-vote-health-2010-11.md)
- [Vote Health 2010/11 source-health machine receipt](./source-health-report-20261004-vote-health-2010-11.json)
- [Vote Health 2010/11 phase 7 review receipt](./phase_7_gates-review-receipt-20261004-vote-health-overview-2010-11.json)
- [Cumulative official source capture manifest, 2026-10-03](./official-capture-2026-10-03-health-complete.json)
- [Source PDF structural layout baseline, 2026-10-03](./source-pdf-layout-baseline-20261003.json)
- [Source layout inventory baseline, 2026-10-03](./source-layout-baseline-20261003.json)
- [Budget source-literal dimensions and unresolved mapping validation](./budget-source-dimensions.validation.json)
- [Context-source Bronze adapters](./context-adapters.md)
- [Context-source adapter validation](./context-adapters.validation.json)
- [Historical package snapshot verification](./historical-snapshot.md)
- [Hash-bound embedded-notice observations](./embedded-notices.md)
- [Standalone Budget-package operations](./budget-operations.md)
- [Specification](./spec.md)
- [Requirements](./requirements.md)
- [Design](./design.md)
- [Implementation plan](./plan.md)
- [Autonomous continuation route](./continuation.md)
- [Portable candidate original paths](./candidate-paths.md)
- [Pinned donor behavior](./donor-behavior.md)
- [Raw Budget extraction](./raw-budget.md)
- [Budget successor pilot and versioned contracts](./raw-budget-successors.md)
- [Raw BEFU/HYEFU extraction](./raw-forecast.md)
- [BEFU 2026 / HYEFU 2025 versioned source pilots](./forecast-successors.md)
- [Exact-series CPI source extraction](./cpi-source.md)
- [Bounded QES published earnings source profile](./qes-source.md)
- [Ministry published-indicator profiles](./moh-indicators.md)
- [Source, schema and population context gaps](./source-schema-gaps.md)
- [Annual resident-population context profile](./population-annual-context.json)
- [Annual population export validation receipt](./population-annual-export.validation.json)
- [Annual population export evidence and limitations](./population-annual-export.md)
- [Annual population context Silver package](./population-annual-silver.md)
- [Context Gold coverage mart](./context-gold-coverage-20260928.md)
- [Budget versus Estimated Actual diagnostic](./budget-actual-comparison.md)
- [Raw historical Health/GDP extraction and reconciliation](./raw-historical.md)
- [Preserved fiscal 1972–2025 successor pilot](./fiscal-2025-pilot.md)
- [Original-workbook orchestration](./raw-rebuild.md)
- [Typed workbook inspection](./workbook-inspection.md)
- [Raw compatibility projection and export contract](./raw-compatibility.md)
- [Source-derived analytical contracts](./raw-analytics.md)
- [Verified source-derived Gold export](./raw-gold.md)
- [Source-derived plot contracts and visual QA](./raw-plots.md)
- [Next raw-source ranges and semantic boundaries](./next-source-ranges.md)
- [Metadata](./metadata.json)
- [Run log](./runlog.md)
- [Evidence](./evidence.md)
- [Machine evidence](./evidence.jsonl)
- [Cutoff-bound source census](./source-census.json)
- [Self-review](./review.md)

## Current state

- Track state: `in_progress`.
- Scope and plan: explicitly approved on 2026-08-29.
- Donor preservation: 23/23 paths imported into external Bronze CAS and
  reconstructed, according to the recorded preservation receipts.
- Official source census: 74 captured resources and 68 discovery-only entries
  in the recorded 142-entry census; discovery is not capture. The June 2026
  Stats NZ GDP workbook is a separate captured vintage with an unqualified
  analytical and rights state.
- Exact CPIQ.SE9A source adapter: PR #271 observed merged after seven passing
  exact-head checks (1,956 hosted tests). Independent local builds retain 449
  selected facts, including 27 literal NA values, 4,041 lineage entries and
  all 22,701 source-row dispositions. Base metadata and real/per-capita products
  remain unresolved; the two local full-harness timeouts remain recorded.
- Derivatives: 312 Silver records, 1,699 field-lineage records and 12 Gold
  artifacts; donor SQLite parity and clean-room rebuild receipts are recorded.
- Separate raw Budget extraction: 215 Health facts, 3,655 cell-lineage rows
  and 6,504 input dispositions; all seven donor appropriation fields match in
  order. These new local outputs do not replace the published derivatives.
- Budget 2026 successor: 185 facts, 3,145 lineage entries and all 6,451 row
  dispositions in a separate pinned package, with independent XML reconciliation
  and two byte-identical builds. Standalone reader PR #273 is merged after seven
  exact-head checks; 61 focused tests achieve 100% critical coverage and the
  recovered cold mutation run kills all 110 mutants. The interrupted worktree
  loss and local timeout remain recorded separately.
- Separate raw BEFU/HYEFU extraction: 20 Health facts, 120 field-lineage rows
  and 4,665 cell dispositions; both ten-row donor summaries match in order.
  Actual/Forecast and vintage are retained; fiscal-year basis remains flagged.
- Separate raw historical extraction: 106 Health/GDP facts, 1,143 lineage rows,
  1,503 cell dispositions, 29 source-only annotated years and one explicitly
  retained precision difference. Historical extraction delivered in PR #232.
- Manifest-driven raw rebuilding: four stages, 341 selected facts, 18 files,
  independent byte-identical rebuild and verified complete-run reuse. This
  local operational result does not replace the published donor-derived data.
- Read-only raw-run CLI/MCP verification: matching live receipts, exact
  manifest pins, source/derivative fixity checks and no creation on missing state.
- Typed workbook inspection delivered in PR #245, with bounded decoded previews
  and original-byte verification. No formula evaluation or fact promotion.
- Persistent raw compatibility export locally validates all 341 facts, retains
  4,918 lineage rows and flags 15 binary representation differences. Independent
  builds match; all 312 donor SQLite rows are retained plus 29 historical years.
  Source-derived Gold tables and CLI now rebuild locally with all 321 selected
  analytical facts and 4,798 lineage records. PR #261 merged after seven
  exact-head checks passed; local timing failures remain recorded. Six new
  source-derived PNGs have matching independent builds and completed visual
  QA; final local assurance passes 1,906 tests and 128 current critical mutants.
  Plot PR #269 merged after all seven exact-head checks passed. Donor failure
  conformance and the four-profile pipeline pass 253 focused and 1,907 full
  tests. PR #270 is merged with seven successful exact-head checks and identical
  head/merge trees; this remains separate from broader source-area coverage.
- Hugging Face: `published_and_verified` for the pinned candidate, with
  [dataset](https://huggingface.co/datasets/edithatogo/nz-health-appropriations)
  revision `9b85bac06597d4435fd078f6bed0f30bb008542b` and manifest SHA-256
  `9a33babda857b0aa7c60a6012000cf1e730fed729781cb8ceb6e7a4714cae40e`.
  The existing receipt records 94 remotely verified manifest entries.
  Public revision visibility and HEOR collection membership were re-observed
  on 2026-08-30; the full byte audit was not repeated during that check.
- Parent issue: [#205](https://github.com/edithatogo/archive-govt-nz/issues/205).
  Issue closure is not evidence of full implementation; the plan and receipts
  remain the acceptance-criteria authority.

Full assimilation is not complete. Remaining plan work includes format-support
contracts, contextual-series semantics,
expanded normalization/analytics and operational/recovery coverage. Consult
[the plan](./plan.md) for individual pending tasks; do not infer their completion
from publication or green CI.

The annual Stats NZ DPE056AA mean-year-ended export is preserved in external
Bronze CAS and admitted to a typed, context-only Silver package with facts,
lineage and row dispositions. Rights, historical vintage coverage and
denominator approval remain open; no per-capita Gold measure is admitted.

Donor retirement remains outside this track (W-02). The donor was observed
unarchived on 2026-08-30. Originals and the existing published candidate are not
rewritten by subsequent inventory improvements. Historical observations in
`metadata.json` and the append-only evidence ledger retain their original dates;
they are not current-state assertions.

- [Implementation Plan](plan.md)
- [Read-only partial-rebuild planner](readonly-resume-planner.md)
- [Historical Budget and forecast source register](historical-source-register.md)
- [BEFU 2002 GAAP expense source/period census addendum](historical-source-register.md)
- [Exact source series and period/rights review](source-measure-review-20260927.json)
- [Budget source-label occurrence comparison](classification-label-occurrences-20260930.json)
- [GDP March/June vintage differences](gdp-vintage-reconciliation-20260930.json)
- [Canonical Gold source-coordinate drill-through](canonical-gold-source-coordinate-drillthrough-20261001.md)

- [Normalization and SQLite checkpoint integration](./normalization-checkpoint-integration-20260913.md)
- [Preserved final normalization checkpoint](./normalization-admission-checkpoint-20260906.json)
- [Bronze checkpoint durability contracts](./bronze-checkpoint-contracts.md)
- [POSIX directory durability validation receipt](./checkpoint-directory-durability.json)
- [Current-head clean-room recovery receipt (2026-10-01)](clean-room-recovery-20261001.json)
- [Vote Health 2009/10 overview phase 7 review receipt](./phase_7_gates-review-receipt-20261004-vote-health-overview-2009-10.json)

- [Vote Health 2011/12 overview extraction](./vote-health-estimates-overview-2011-12-20261004.md)
- [Vote Health 2011/12 machine receipt](./vote-health-estimates-overview-2011-12-20261004.json)
- [Vote Health 2011/12 captured-source census](./vote-health-estimates-overview-2011-12-census.json)
- [Vote Health 2011/12 capture manifest](./vote-health-estimates-overview-2011-12-capture-final.json)
- [Vote Health 2011/12 source-health reconciliation](./source-health-report-20261004-vote-health-2011-12.md)
- [Vote Health 2011/12 source-health machine receipt](./source-health-report-20261004-vote-health-2011-12.json)
- [Vote Health 2011/12 source-operation output receipt](./vote-health-estimates-overview-2011-12-source-operation.json)

- [Vote Health 2012/13 overview extraction](./vote-health-estimates-overview-2012-13-20261004.md)
- [Vote Health 2012/13 machine receipt](./vote-health-estimates-overview-2012-13-20261004.json)
- [Vote Health 2012/13 captured-source census](./vote-health-estimates-overview-2012-13-census.json)
- [Vote Health 2012/13 capture request](./vote-health-estimates-overview-2012-13-capture-request.json)
- [Vote Health 2012/13 capture manifest](./vote-health-estimates-overview-2012-13-capture-final.json)
- [Vote Health 2012/13 source-health reconciliation](./source-health-report-20261004-vote-health-2012-13.md)
- [Vote Health 2012/13 source-operation output receipt](./vote-health-estimates-overview-2012-13-source-operation.json)
- [Vote Health 2013/14 overview extraction](./vote-health-estimates-overview-2013-14-20261004.md)
- [Vote Health 2013/14 machine receipt](./vote-health-estimates-overview-2013-14-20261004.json)
- [Vote Health 2013/14 captured-source census](./vote-health-estimates-overview-2013-14-census.json)
- [Vote Health 2013/14 capture request](./vote-health-estimates-overview-2013-14-capture-request.json)
- [Vote Health 2013/14 capture manifest](./vote-health-estimates-overview-2013-14-capture-final.json)
- [Vote Health 2013/14 source-health reconciliation](./source-health-report-20261004-vote-health-2013-14.md)
- [Vote Health 2013/14 source-operation output receipt](./vote-health-estimates-overview-2013-14-source-operation.json)
- [Vote Health 2013/14 source-health machine receipt](./source-health-report-20261004-vote-health-2013-14.json)
- [Vote Health 2014/15 overview extraction](./vote-health-estimates-overview-2014-15-20261004.md)
- [Vote Health 2014/15 machine receipt](./vote-health-estimates-overview-2014-15-20261004.json)
- [Vote Health 2014/15 captured-source census](./vote-health-estimates-overview-2014-15-census.json)
- [Vote Health 2014/15 capture evidence](./vote-health-estimates-overview-2014-15-capture-evidence.json)
- [Vote Health 2014/15 source-health reconciliation](./source-health-report-20261004-vote-health-2014-15.md)
- [Vote Health 2014/15 source-health machine receipt](./source-health-report-20261004-vote-health-2014-15.json)
- [Vote Health 2014/15 source-operation output receipt](./vote-health-estimates-overview-2014-15-source-operation.json)

- [Source-qualified Fiscal Health shares](./fiscal-health-shares-20261004.md)
- [Fiscal share repeat-build receipt](./fiscal-health-shares-20261004.json)

- [Annual mean resident spending rate](fiscal-health-per-capita-20261004.md)
- [Per-capita native replay evidence](fiscal-health-per-capita-20261004.json)

- [Household CPI fiscal benchmark](fiscal-health-cpi-benchmark-20261004.md)
- [CPI benchmark native replay evidence](fiscal-health-cpi-benchmark-20261004.json)

- [Fiscal analytical Gold package](fiscal-analytical-gold-20261004.md)
- [Analytical Gold repeat-build receipt](fiscal-analytical-gold-20261004.json)

- [Read-only Fiscal analytical CLI/MCP access](fiscal-analytical-access-20261004.md)
- [Native CLI/MCP and Arrow comparison receipt](fiscal-analytical-access-20261004.json)

- [Fiscal analytical reports and metadata](fiscal-analytical-reports-20261004.md)
- [Report native repeat-build assurance](fiscal-analytical-reports-20261004.json)
- [Fiscal Gold source reconciliation](fiscal-gold-source-reconciliation-20261005.md)
- [Source reconciliation machine receipt](fiscal-gold-source-reconciliation-20261005.json)

- [Integrated Fiscal analytical recovery](fiscal-analytical-recovery-20261004.md)
- [Native reconstruction and interface evidence](fiscal-analytical-recovery-20261004.json)

- [Budget estimate-transition comparison](./budget-vintage-comparison-20261005.md)

- [Budget comparison Gold and operations](./budget-comparison-gold-20261005.md)

- [Local analytical Gold metadata](./gold-metadata-20261005.md)

- [Local Gold discovery profiles](./gold-discovery-profiles-20261005.md)

- [Fresh analytical products and metadata recovery](./analytical-metadata-recovery-20261005.md)
- [Analytical metadata recovery evidence](./analytical-metadata-recovery-20261005.json)
- [Scoped analytical metadata recovery review](./phase_7_gates-review-receipt-20261005-analytical-metadata-recovery.json)

- [2015/16 Vote Health overview](vote-health-estimates-overview-2015-16-20261005.md)
- [2015/16 overview evidence](vote-health-estimates-overview-2015-16-20261005.json)
- [2016/17 Vote Health overview source census](./vote-health-estimates-overview-2016-17-census.md)
- [2016/17 Vote Health overview census receipt](./vote-health-estimates-overview-2016-17-census.json)
- [Source/measure census review refreshed for this evidence snapshot](./source-measure-review-20261005.json)
- [Source/measure census review with BEFU 2002 period and scope](./source-measure-review-20261006.json)
- [Source/measure policy reconciliation at 16 October](./source-measure-review-20261016.json)
- [Historical Vote Health 2002 main and supplementary estimate locators](./historical-source-register.md#vote-health-estimates-and-supplementary-estimates-budget-2002--6-october-2026)
- [2016/17 Vote Health overview implementation and census review](./vote-health-estimates-overview-2016-17-review-20261005.md)
- [2016/17 Vote Health overview Conductor phase review receipt](./phase_7_gates-review-receipt-20261005-vote-health-2016-17.json)
- [2011/12 Vote Health Supplementary Estimates category totals](./vote-health-supplementary-2011-12-category-totals-20261006.md)
- [2011/12 category-total evidence](./vote-health-supplementary-2011-12-category-totals-20261006.json)
- [2011/12 category totals in clean-room recovery](./clean-room-recovery-20261006-vote-health-2011-12.json)
- [2010/11 Vote Health Supplementary Estimates category totals](./vote-health-supplementary-2010-11-category-totals-20261006.md)
- [2010/11 category-total evidence](./vote-health-supplementary-2010-11-category-totals-20261006.json)
- [2010/11 category totals in clean-room recovery](./clean-room-recovery-20261006-vote-health-2010-11.json)
- [2006/07 Vote Health Supplementary Estimates overview totals](./vote-health-supplementary-2006-07-overview-totals-20261007.md)
- [2006/07 overview-total evidence](./vote-health-supplementary-2006-07-overview-totals-20261007.json)
- [2006/07 overview totals in clean-room recovery](./clean-room-recovery-20261007-vote-health-2006-07.json)
- [2007/08 Vote Health Supplementary Estimates category totals](./vote-health-supplementary-2007-08-category-totals-20261007.md)
- [2007/08 category-total evidence](./vote-health-supplementary-2007-08-category-totals-20261007.json)
- [2007/08 category totals in clean-room recovery](./clean-room-recovery-20261007-vote-health-2007-08.json)
- [2008/09 Vote Health Supplementary Estimates category totals](./vote-health-supplementary-2008-09-category-totals-20261007.md)
- [2008/09 category-total evidence](./vote-health-supplementary-2008-09-category-totals-20261007.json)
- [2008/09 category totals in clean-room recovery](./clean-room-recovery-20261007-vote-health-2008-09.json)
- [2009/10 Vote Health Supplementary Estimates category totals](./vote-health-supplementary-2009-10-category-totals-20261006.md)
- [2009/10 category-total evidence](./vote-health-supplementary-2009-10-category-totals-20261006.json)
- [2009/10 category totals in clean-room recovery](./clean-room-recovery-20261006-vote-health-2009-10.json)
- [2013/14 Vote Health Supplementary Estimates category totals](./vote-health-supplementary-2013-14-category-totals-20261006.md)
- [2013/14 category-total evidence](./vote-health-supplementary-2013-14-category-totals-20261006.json)
- [2013/14 category totals in clean-room recovery](./clean-room-recovery-20261006-vote-health-2013-14.json)
- [2014/15 Vote Health Supplementary Estimates category totals](./vote-health-supplementary-2014-15-category-totals-20261006.md)
- [2014/15 category-total evidence](./vote-health-supplementary-2014-15-category-totals-20261006.json)
- [2014/15 category totals in clean-room recovery](./clean-room-recovery-20261006-vote-health-2014-15.json)
- [2015/16 Vote Health Supplementary Estimates category totals](./vote-health-supplementary-2015-16-category-totals-20261006.md)
- [2015/16 category-total evidence](./vote-health-supplementary-2015-16-category-totals-20261006.json)
- [2015/16 category totals in clean-room recovery](./clean-room-recovery-20261006-vote-health-2015-16.json)
- [2016/17 Vote Health Supplementary Estimates category totals](./vote-health-supplementary-2016-17-category-totals-20261006.md)
- [2016/17 category-total evidence](./vote-health-supplementary-2016-17-category-totals-20261006.json)
- [2016/17 category totals in clean-room recovery](./clean-room-recovery-20261006-vote-health-2016-17.json)
- [2017/18 Vote Health Supplementary Estimates category totals](./vote-health-supplementary-2017-18-category-totals-20261006.md)
- [2017/18 category-total evidence](./vote-health-supplementary-2017-18-category-totals-20261006.json)
- [2017/18 category totals in clean-room recovery](./clean-room-recovery-20261006-vote-health-2017-18.json)
- [2018/19 Vote Health Supplementary Estimates category totals](./vote-health-supplementary-2018-19-category-totals-20261006.md)
- [2019/20 Vote Health Supplementary Estimates category totals](./vote-health-supplementary-2019-20-category-totals-20261006.md)
- [2019/20 Vote Health category-total evidence](./vote-health-supplementary-2019-20-category-totals-20261006.json)
- [2020/21 Vote Health Supplementary Estimates summary totals](./vote-health-supplementary-2020-21-summary-totals-20261006.md)
- [2020/21 Vote Health summary-total evidence](./vote-health-supplementary-2020-21-summary-totals-20261006.json)
- [2021/22 Vote Health Supplementary Estimates summary totals](./vote-health-supplementary-2021-22-summary-totals-20261006.md)
- [2021/22 Vote Health summary-total evidence](./vote-health-supplementary-2021-22-summary-totals-20261006.json)
- [2022/23 Vote Health Supplementary Estimates summary totals](./vote-health-supplementary-2022-23-summary-totals-20261006.md)
- [2022/23 Vote Health summary-total evidence](./vote-health-supplementary-2022-23-summary-totals-20261006.json)
- [2023/24 Vote Health Supplementary Estimates summary totals](./vote-health-supplementary-2023-24-summary-totals-20261006.md)
- [2023/24 Vote Health summary-total evidence](./vote-health-supplementary-2023-24-summary-totals-20261006.json)
- [2024/25 Vote Health Supplementary Estimates summary totals](./vote-health-supplementary-2024-25-summary-totals-20261006.md)
- [2024/25 Vote Health summary-total evidence](./vote-health-supplementary-2024-25-summary-totals-20261006.json)
- [2025/26 Vote Health Supplementary Estimates summary totals](./vote-health-supplementary-2025-26-summary-totals-20261006.md)
- [2025/26 Vote Health summary evidence](./vote-health-supplementary-2025-26-summary-totals-20261006.json)
- [2025/26 Vote Health clean-room recovery](./clean-room-recovery-20261006-vote-health-2025-26.json)
- [2018/19 category-total evidence receipt](./vote-health-supplementary-2018-19-category-totals-20261006.json)
- [2018/19 category-total Conductor review](./phase_7_gates-review-receipt-20261006-vote-health-2018-19-totals.json)
- [Vote Health 2018/19 category totals in clean-room recovery](./clean-room-recovery-20261006-vote-health-2018-19.json)
- [Vote Health 2021/22 summary in clean-room recovery](./clean-room-recovery-20261006-vote-health-2021-22.json)
- [Vote Health 2022/23 summary in clean-room recovery](./clean-room-recovery-20261006-vote-health-2022-23.json)
- [Vote Health 2023/24 summary in clean-room recovery](./clean-room-recovery-20261006-vote-health-2023-24.json)
- [Vote Health 2024/25 summary in clean-room recovery](./clean-room-recovery-20261006-vote-health-2024-25.json)
- [Vote Health 2004/05 Supplementary Estimates overview](./vote-health-supplementary-2004-05-overview-20261007.md)
- [Vote Health 2004/05 overview extraction evidence](./vote-health-supplementary-2004-05-overview-20261007.json)
- [Vote Health 2004/05 overview in clean-room recovery](./clean-room-recovery-20261007-vote-health-2004-05.json)
- [Vote Health 2001/02 Supplementary Estimates overview](./vote-health-supplementary-2001-02-overview-20261007.md)
- [Vote Health 2001/02 overview extraction evidence](./vote-health-supplementary-2001-02-overview-20261007.json)
- [Vote Health 2001/02 overview in clean-room recovery](./clean-room-recovery-20261007-vote-health-2001-02.json)
- [Vote Health 2000/01 Supplementary Estimates overview](./vote-health-supplementary-2000-01-overview-20261007.md)
- [Vote Health 2000/01 overview extraction evidence](./vote-health-supplementary-2000-01-overview-20261007.json)
- [Vote Health 2000/01 overview in clean-room recovery](./clean-room-recovery-20261007-vote-health-2000-01.json)
- [Vote Health 2002/03 Supplementary Estimates overview](./vote-health-supplementary-2002-03-overview-20261007.md)
- [Vote Health 2002/03 overview extraction evidence](./vote-health-supplementary-2002-03-overview-20261007.json)
- [Vote Health 2002/03 overview in clean-room recovery](./clean-room-recovery-20261007-vote-health-2002-03.json)

- [Vote Health 1999/2000 Supplementary Estimates overview](./vote-health-supplementary-1999-00-overview-20261007.md)
- [Vote Health 1999/2000 overview extraction evidence](./vote-health-supplementary-1999-00-overview-20261007.json)
- [Vote Health 1999/2000 overview in integrated clean-room recovery](./clean-room-recovery-20261007-vote-health-1999-00.json)
- [Fiscal Gold cross-product query matrix and real-view exclusion](./fiscal-gold-query-matrix-20261007.md)
- [Canonical Gold named queries and readback evidence](./canonical-gold-queries-20261017.md)
- [Canonical Gold metadata profile and version compatibility](./canonical-gold-metadata-20261017.md)
- [Fresh canonical inputs and query/metadata recovery](./canonical-recovery-inputs-20261017.md)

- [Fresh canonical recovery native validation](./canonical-recovery-validation-20261017.json)

- [Independent ordered query recovery validation](./canonical-recovery-ordered-validation-20261017.json)

- [2002 BEFU/DEFU census observation](./source-census-2002-befu-defu-20261017.md)
- [2002 source identity/period/layout evidence](./source-census-2002-befu-defu-20261017.json)
- [Source/measure review after the 2002 slice](./source-measure-review-20261017.json)

- [BEFU 1998 census observation](./source-census-befu-1998-20261017.md)
- [BEFU 1998 source identity/layout evidence](./source-census-befu-1998-20261017.json)
- [Previous source/measure census review, BEFU 1998](./source-measure-review-20261017-1998.json)

- [BEFU 1999 and year-end publication census](./source-census-befu-1999-20261017.md)
- [BEFU 1999 source and disposition evidence](./source-census-befu-1999-20261017.json)
- [Previous source/measure census review, BEFU 1999](./source-measure-review-20261017-1999.json)

- [Remaining year-level source locator census](./source-census-locator-gaps-20261017.md)
- [Locator identity and period evidence](./source-census-locator-gaps-20261017.json)
- [Health component index discovery](./health-component-index-discovery-20261017.md)
- [Component table and method evidence](./health-component-index-discovery-20261017.json)
- [Previous source/measure census review, locator gaps](./source-measure-review-20261017-locator-gaps.json)
- [Source/measure review bound to retained census](./source-measure-review-20261017-cpi-snapshot-binding.json)


- [Retained capture inventory reconciliation](./capture-inventory-20261017.md)
- [Distinct 2019/20 Supplementary Addition census](./supplementary-addition-2019-20-census-20261017.md)
- [Latest bounded capture inventory including the Addition](./capture-inventory-20261017-addition.json)

- [Operational reviewed overview dispatch](./overview-operational-dispatch-20261017.md)
  and [native run inventory/pinned readback proof](./overview-operational-dispatch-20261017.json).

- [Operational overview review-fix native proof](./overview-operational-dispatch-review-fix-20261017.json).

- [Bounded donor-area partial metadata mappings](./donor-area-partial-mappings-20261017.json);
  not whole-sheet completeness or output verification. Phase4issue #210 remains open.

- [Reviewed forecast common adapters](./forecast-common-adapters-20261017.md)
  and [four-API/two-common native proof](./forecast-common-adapters-20261017.json).

- [Forecast evidence rebinding](./forecast-evidence-rebinding-20261017.json), [historical context snapshot](./context-census-pre-forecast-common-20261017.json), and [successor source-measure binding](./source-measure-review-20261017-forecast-binding.json).

- [Forecast common adapter full local validation](./forecast-common-adapters-validation-20261017.json).

- [Forecast operational dispatch checkpoint](./forecast-operational-dispatch-20261017.json).

- [Forecast operation native repeat/readback proof](./forecast-operational-dispatch-native-20261017.json).

- [Forecast operation full validation and timeout recovery evidence](./forecast-operational-dispatch-validation-20261017.json).

- [Forecast operation size review fix](./forecast-operation-size-review-fix-20261017.json).

- [Forecast operation size-fix native and real regression proof](./forecast-operation-size-fix-native-20261017.json).

- [Forecast operation size-fix full validation](./forecast-operation-size-fix-validation-20261017.json).

- [Forecast operational dispatch delivered and pruned](./forecast-operational-dispatch-delivery-20261017.json).

- [Context operation CPI literal/version boundary](./context-operation-cpi-vintage-20261017.json).

- [Five-profile context operational dispatch checkpoint](./context-operational-dispatch-20261017.json).

- [Context dispatch native repeat/recovery proof](./context-operational-dispatch-native-20261017.json) and [full local validation](./context-operational-dispatch-validation-20261017.json).

- [Context operations delivered and clean topic pruned](./context-operational-dispatch-delivery-20261017.json).

- [Operation-bound canonical context and QES lineage disposition](./context-operation-canonical-20261017.json).

- [Canonical operation native proof](./context-operation-canonical-native-20261017.json) and [full local validation](./context-operation-canonical-validation-20261017.json).

- [Canonical operation consumer delivered and topic pruned](./context-operation-canonical-delivery-20261017.json).

- [Operation Context Gold implementation and resource-contract checkpoint](./operation-context-gold-20261017.json).

- [Operation Context Gold actual-source repeat proof](./operation-context-gold-native-20261017.json).
- [Operation Context Gold initial full-gate failure evidence](./operation-context-gold-initial-validation-20261017.json).

- [Operation Context Gold full local validation](./operation-context-gold-validation-20261017.json).

- [PR704 reserved-output race correction checkpoint](./operation-context-gold-output-correction-20261017.json).

- [PR704 pinned-output actual-source repeat proof](./operation-context-gold-output-native-20261017.json).

- [Operation Context Gold protected delivery and pruning](./operation-context-gold-delivery-20261017.json).

- [Operation-context metadata in-progress checkpoint](./operation-context-metadata-20261017.json).

- [Operation-context metadata delivery](./operation-context-metadata-delivery-20261017.json) — PR705 merged, required checks passed, fetched/pruned proof; broader track remains open.

- [CPI source-evidence checkpoint](./cpi-source-evidence-20261017.json) — response-bound current metadata and same-byte CSV recapture; offline contract and census reconciliation in progress.

- [CPI offline source contract and replay](./cpi-source-evidence-20261017.md), [verified report](./cpi-source-evidence-report-20261017.json), [native proof](./cpi-source-evidence-native-20261017.json), and [preservation](./cpi-source-preservation-20261017.json) — current census reconciled; full/hosted delivery pending.

- [CPI source-review historical binding](./cpi-source-review-rebinding-20261017.json) — original review and assessment unchanged; successor retains the exact historical census digest rather than following mutable current metadata.

- [CPI source-health v2 profile](./cpi-source-health-20261017.md) — fixed source-evidence adoption; focused/static qualified, actual-source/full/hosted pending.

- [Operation-context metadata CLI/MCP](./operation-metadata-operations-20261017.md) and [focused checkpoint](./operation-metadata-operations-20261017.json) — source-regenerated v5 operations; native/full/hosted pending.
- [CPI source-health delivery](./cpi-source-health-delivery-20261017.json) — PR707 merged and verified; topic refs pruned.

- [Metadata operations delivery](./operation-metadata-operations-delivery-20261018.json) — PR708 merged, seven checks passed, fetched tree verified and topic refs pruned; historical pending receipt superseded.
- [Component-index source checkpoint](./component-index-source-checkpoint-20261018.json) — actual LCI/PPI exports and source metadata captured/preserved; offline qualification and rights observations pending.

- [Component-index source contract and guide](./component-index-source-evidence-20261018.md), [report](./component-index-source-evidence-report-20261018.json), [native proof](./component-index-source-native-20261018.json), [initial failure](./component-index-source-native-failure-20261018.json), and [full assurance](./component-index-source-assurance-20261018.json) — source-census qualification passes; rights/admission and hosted delivery remain separate.

- [Component-index corrected full assurance](./component-index-source-assurance-final-20261018.json) and [scan recovery](./component-index-source-scan-recovery-20261018.json) — native3/current report and corrected full2 pass; prior proof/scan evidence retained, no scanner policy changes.

- [Component-index delivery](./component-index-source-delivery-20261018.json), [current full assurance](./component-index-source-current-assurance-20261018.json), and [native comparison](./component-index-source-current-native-20261018.json) — PR709 merged after exact-head checks; original proofs/failures preserved and clean topic refs pruned.

- [Supplementary summary common dispatch checkpoint](./supplementary-summary-dispatch-20261018.json) — two existing source-specific normalizers now expose shared snapshot extraction; focused qualification complete, native/full/hosted pending.

- [Exact donor-stage reconstruction](./donor-area-reconstruction-20261018.json); two new retained runs match all50 historical file pins and12stage receipts. Remaining area bindings stay open.

- [Recovered nine-stage source-area bindings](./donor-stage-area-bindings-20261018.json); native613-fact/12binding report and full local assurance, with all global unit remainders open.

- [Five physical literal source adapters](./literal-common-adapters-20261018.json); seven shared native profiles, complete area qualifiers, two native replays and full harness qualified; hosted delivery pending.

- [Fiscal2024 historical common dispatch](./historical-common-dispatch-20261018.json); focused308, native two-run parity and full7954 passed; historical census binding reconciled; hosted delivery pending.

- [Compound native workbook contract](./compound-native-recordsets-20261018.md); planned typed forecast/detail composition with unchanged v1 consumers and native schemas.

- [Compound carrier checkpoint](./compound-native-recordsets-20261018.json); carrier, native dispatch, bounded envelopes and v1 regression checks pass96; source composition/native/full assurance pending.

- [Read-only native workbook inspection](./native-workbook-inspection-20261018.md) — delivered PR #716; actual Windows qualification, seven exact-head successes and verified cleanup.

- [Budget 2024 expenditure/revenue census](./source-census-budget-2024-20261018.md) — originals preserved; native headers/definitions and item notices observed; source-bound 2024 revenue locally qualified; hosted delivery pending.

- [Budget 2024 structural inventory](./budget-2024-layout-20261018.json) and [native definitions/item notices](./budget-2024-definitions-20261018.json).

- [Source/measure review with Budget 2024 retained-source overlay](./source-measure-review-20261018-budget-2024.json) — 19 existing series retained; wider edition and analytical gaps remain explicit.

- [Budget 2024 revenue native/full qualification](./budget-2024-revenue-qualification-20261018.json) —66facts, all1004rows accounted, byte-identical repeats; hosted delivery pending.

- [Budget 2024 source-operation entry correction](./budget-2024-source-entry-20261018.json) — supported CLI/MCP actual-source entry and corrected 32-stage full harness pass; fresh hosted delivery pending.

- [Budget2024 expenditure profile](./budget-2024-expenditure-profile-20261018.json) — native and hosted qualified; delivered PR 718, local timing failures retained.
- [PR717 delivery](./budget-2024-revenue-delivery-20261018.json) — protected merge and verified topic cleanup.

- [PR 718 delivery](./budget-2024-expenditure-delivery-20261018.json) — protected merge, full hosted assurance and verified cleanup.
- [Budget 2023 census](./source-census-budget-2023-20261018.json) — originals privately preserved; native definitions, layout and item rights pending.

- [Budget 2023 capture](./budget-2023-capture-20261018.json) — source fixity, WARC binding and receipts independently verified.

- [Budget 2023 bounded native inspection](./budget-2023-native-inspection-20261018.json)

- [Budget 2023 revenue native qualification](./budget-2023-revenue-native-20261018.json)

- [Budget 2023 revenue full assurance](./budget-2023-revenue-assurance-20261018.json)

- [Budget 2023 revenue protected delivery](./budget-2023-revenue-delivery-20261018.json)

- [Budget 2023 expenditure source profile](./budget-2023-expenditure-profile-20261018.json)

- [Budget 2023 expenditure native qualification](./budget-2023-expenditure-native-20261018.json)

- [Budget 2023 expenditure local assurance result](./budget-2023-expenditure-assurance-20261018.json)

- [Budget 2023 expenditure protected delivery](./budget-2023-expenditure-delivery-20261018.json)

- [Readable PDF layout diagnosis and focused parser fixes](./readable-pdf-layout-diagnostic-20261018.json)

- [Retained PDF layout qualification](./readable-pdf-layout-qualification-20261018.json) and [59-source layout baseline](./source-pdf-layout-baseline-20261018.json).

- [PDF local assurance](./readable-pdf-layout-assurance-20261018.json), [source-health qualification](./readable-pdf-source-health-qualification-20261018.json), [refreshed readable source-health report](./source-health-report-20261018-pdf-layouts.md) and [v2 JSON](./source-health-report-20261018-pdf-layouts.json). Prior default report remains a retained historical receipt.

- [PDF layout protected delivery and cleanup](./readable-pdf-layout-delivery-20261018.json) — PR721 merged and verified; topic refs pruned.

- [Budget2022 working source census](./source-census-budget-2022-20261018.json) — official release observed; bounded capture/native verification pending.

- [Budget2022 partial capture qualification](./budget-2022-capture-20261018.json) — workbook pair preserved; release-page403 and native/rights gates explicit.

- [Budget2022 native structure and definitions](./budget-2022-native-inspection-20261018.json) — observed row bounds and profile prerequisites; no numerical admission.

- [Budget2022 source-profile implementation and focused evidence](./budget-2022-profile-implementation-20261018.json) — native/full/protected qualification pending.

- [Budget2022 actual-source repeat/CLI/MCP/compatibility qualification](./budget-2022-native-qualification-20261018.json) — local source-native profiles pass; full/protected delivery pending.

- [Budget2022 original local assurance attempt](./budget-2022-assurance-20261018.json) — terminal test cap; all32clean-hosted and protected delivery required.

- [Budget2022 protected delivery and local failure dispositions](./budget-2022-delivery-20261018.json)

- [Context reader startup implementation](./context-reader-startup-implementation-20261018.json)
