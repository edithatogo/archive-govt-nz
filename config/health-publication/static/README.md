---
license: cc-by-4.0
task_categories:
- tabular-classification
tags:
- new-zealand
- government
- health-economics
- public-finance
- appropriations
pretty_name: New Zealand Health Appropriations
language:
- en
configs:
- config_name: health_spending_gdp_share
  data_files:
  - split: train
    path: data/gold/health_spending_gdp_share.parquet
- config_name: historical_nominal
  data_files:
  - split: train
    path: data/gold/historical_nominal.parquet
- config_name: historical_yoy
  data_files:
  - split: train
    path: data/gold/historical_yoy.parquet
- config_name: recent_classification_trends
  data_files:
  - split: train
    path: data/gold/recent_classification_trends.parquet
- config_name: recent_functional_breakdown
  data_files:
  - split: train
    path: data/gold/recent_functional_breakdown.parquet
- config_name: donor_facts
  data_files:
  - split: train
    path: data/silver/donor_facts.parquet
- config_name: field_lineage
  data_files:
  - split: train
    path: data/silver/field_lineage.parquet
- config_name: budget_2007_2008_appropriation_fact
  data_files:
  - split: train
    path:
    - data/silver/budget_2007_2008/2007/appropriation_fact.parquet
    - data/silver/budget_2007_2008/2008/appropriation_fact.parquet
- config_name: budget_2007_2008_field_lineage
  data_files:
  - split: train
    path:
    - data/silver/budget_2007_2008/2007/field_lineage.parquet
    - data/silver/budget_2007_2008/2008/field_lineage.parquet
- config_name: budget_2007_2008_numeric_evidence
  data_files:
  - split: train
    path:
    - data/silver/budget_2007_2008/2007/numeric_evidence.parquet
    - data/silver/budget_2007_2008/2008/numeric_evidence.parquet
- config_name: budget_2007_2019_revenue_field_lineage
  data_files:
  - split: train
    path:
    - data/silver/budget_2007_2019_revenue/2007/field_lineage.parquet
    - data/silver/budget_2007_2019_revenue/2008/field_lineage.parquet
    - data/silver/budget_2007_2019_revenue/2009/field_lineage.parquet
    - data/silver/budget_2007_2019_revenue/2010/field_lineage.parquet
    - data/silver/budget_2007_2019_revenue/2011/field_lineage.parquet
    - data/silver/budget_2007_2019_revenue/2012/field_lineage.parquet
    - data/silver/budget_2007_2019_revenue/2013/field_lineage.parquet
    - data/silver/budget_2007_2019_revenue/2014/field_lineage.parquet
    - data/silver/budget_2007_2019_revenue/2015/field_lineage.parquet
    - data/silver/budget_2007_2019_revenue/2016/field_lineage.parquet
    - data/silver/budget_2007_2019_revenue/2017/field_lineage.parquet
    - data/silver/budget_2007_2019_revenue/2018/field_lineage.parquet
    - data/silver/budget_2007_2019_revenue/2019/field_lineage.parquet
- config_name: budget_2007_2019_revenue_numeric_evidence
  data_files:
  - split: train
    path:
    - data/silver/budget_2007_2019_revenue/2007/numeric_evidence.parquet
    - data/silver/budget_2007_2019_revenue/2008/numeric_evidence.parquet
    - data/silver/budget_2007_2019_revenue/2009/numeric_evidence.parquet
    - data/silver/budget_2007_2019_revenue/2010/numeric_evidence.parquet
    - data/silver/budget_2007_2019_revenue/2011/numeric_evidence.parquet
    - data/silver/budget_2007_2019_revenue/2012/numeric_evidence.parquet
    - data/silver/budget_2007_2019_revenue/2013/numeric_evidence.parquet
    - data/silver/budget_2007_2019_revenue/2014/numeric_evidence.parquet
    - data/silver/budget_2007_2019_revenue/2015/numeric_evidence.parquet
    - data/silver/budget_2007_2019_revenue/2016/numeric_evidence.parquet
    - data/silver/budget_2007_2019_revenue/2017/numeric_evidence.parquet
    - data/silver/budget_2007_2019_revenue/2018/numeric_evidence.parquet
    - data/silver/budget_2007_2019_revenue/2019/numeric_evidence.parquet
- config_name: budget_2007_2019_revenue_revenue_fact
  data_files:
  - split: train
    path:
    - data/silver/budget_2007_2019_revenue/2007/revenue_fact.parquet
    - data/silver/budget_2007_2019_revenue/2008/revenue_fact.parquet
    - data/silver/budget_2007_2019_revenue/2009/revenue_fact.parquet
    - data/silver/budget_2007_2019_revenue/2010/revenue_fact.parquet
    - data/silver/budget_2007_2019_revenue/2011/revenue_fact.parquet
    - data/silver/budget_2007_2019_revenue/2012/revenue_fact.parquet
    - data/silver/budget_2007_2019_revenue/2013/revenue_fact.parquet
    - data/silver/budget_2007_2019_revenue/2014/revenue_fact.parquet
    - data/silver/budget_2007_2019_revenue/2015/revenue_fact.parquet
    - data/silver/budget_2007_2019_revenue/2016/revenue_fact.parquet
    - data/silver/budget_2007_2019_revenue/2017/revenue_fact.parquet
    - data/silver/budget_2007_2019_revenue/2018/revenue_fact.parquet
    - data/silver/budget_2007_2019_revenue/2019/revenue_fact.parquet
- config_name: budget_2009_2019_expenses_appropriation_fact
  data_files:
  - split: train
    path:
    - data/silver/budget_2009_2019_expenses/2009/appropriation_fact.parquet
    - data/silver/budget_2009_2019_expenses/2010/appropriation_fact.parquet
    - data/silver/budget_2009_2019_expenses/2011/appropriation_fact.parquet
    - data/silver/budget_2009_2019_expenses/2012/appropriation_fact.parquet
    - data/silver/budget_2009_2019_expenses/2013/appropriation_fact.parquet
    - data/silver/budget_2009_2019_expenses/2014/appropriation_fact.parquet
    - data/silver/budget_2009_2019_expenses/2015/appropriation_fact.parquet
    - data/silver/budget_2009_2019_expenses/2016/appropriation_fact.parquet
    - data/silver/budget_2009_2019_expenses/2017/appropriation_fact.parquet
    - data/silver/budget_2009_2019_expenses/2018/appropriation_fact.parquet
    - data/silver/budget_2009_2019_expenses/2019/appropriation_fact.parquet
- config_name: budget_2009_2019_expenses_field_lineage
  data_files:
  - split: train
    path:
    - data/silver/budget_2009_2019_expenses/2009/field_lineage.parquet
    - data/silver/budget_2009_2019_expenses/2010/field_lineage.parquet
    - data/silver/budget_2009_2019_expenses/2011/field_lineage.parquet
    - data/silver/budget_2009_2019_expenses/2012/field_lineage.parquet
    - data/silver/budget_2009_2019_expenses/2013/field_lineage.parquet
    - data/silver/budget_2009_2019_expenses/2014/field_lineage.parquet
    - data/silver/budget_2009_2019_expenses/2015/field_lineage.parquet
    - data/silver/budget_2009_2019_expenses/2016/field_lineage.parquet
    - data/silver/budget_2009_2019_expenses/2017/field_lineage.parquet
    - data/silver/budget_2009_2019_expenses/2018/field_lineage.parquet
    - data/silver/budget_2009_2019_expenses/2019/field_lineage.parquet
- config_name: budget_2009_2019_expenses_numeric_evidence
  data_files:
  - split: train
    path:
    - data/silver/budget_2009_2019_expenses/2009/numeric_evidence.parquet
    - data/silver/budget_2009_2019_expenses/2010/numeric_evidence.parquet
    - data/silver/budget_2009_2019_expenses/2011/numeric_evidence.parquet
    - data/silver/budget_2009_2019_expenses/2012/numeric_evidence.parquet
    - data/silver/budget_2009_2019_expenses/2013/numeric_evidence.parquet
    - data/silver/budget_2009_2019_expenses/2014/numeric_evidence.parquet
    - data/silver/budget_2009_2019_expenses/2015/numeric_evidence.parquet
    - data/silver/budget_2009_2019_expenses/2016/numeric_evidence.parquet
    - data/silver/budget_2009_2019_expenses/2017/numeric_evidence.parquet
    - data/silver/budget_2009_2019_expenses/2018/numeric_evidence.parquet
    - data/silver/budget_2009_2019_expenses/2019/numeric_evidence.parquet
- config_name: budget_2025_revenue_field_lineage
  data_files:
  - split: train
    path:
    - data/silver/budget_2025_revenue/2025/field_lineage.parquet
- config_name: budget_2025_revenue_revenue_fact
  data_files:
  - split: train
    path:
    - data/silver/budget_2025_revenue/2025/revenue_fact.parquet
---

# New Zealand Health Appropriations

This candidate preserves rights-eligible official fiscal originals and provides
source-faithful Parquet records, field lineage, donor-compatible analytics, and
reproducible metadata for New Zealand Vote Health appropriations and context.

## Medallion structure

- `original/`: unchanged, checksum-pinned Treasury/Budget and Ministry files.
- `data/silver/`: typed donor-parity facts and field lineage.
- `data/gold/`: rebuildable analysis tables; SQLite and plots remain downloadable
  compatibility artifacts rather than canonical tabular state.
- `metadata/`: census, rights, provenance, DCAT, Croissant, and RO-Crate records.

## Rights and attribution

Eligible official material is reused under the per-resource CC BY 4.0 evidence
and attribution recorded in `metadata/rights.json`, including Treasury,
Ministry of Health, Stats NZ, and Pharmac resources. Donor repository code is
Apache-2.0 and is not included as a blanket licence assertion for government
data. Logos, design elements, third-party content, and resources lacking
affirmative rights evidence are excluded or represented by metadata only.

## Limitations

The donor's checked-in SQLite is an observed parity oracle, not preservation
truth. Current longitudinal expansion is incomplete beyond the captured
cutoff. Fiscal classifications and institutional boundaries change over time.
The products are descriptive and must not be used as causal or forecasting
claims. Every amount must be interpreted with its unit, vintage, amount type,
and source lineage.

Candidate state: `release_candidate_pending_exact_manifest_approval`. Upload remains subject to exact-manifest
approval and independent hosted verification.

## Verified Hub access and use — 26 October 2026

Public repository; anonymous downloads enabled. Explicit table configurations isolate compatible records from manifests, evidence and unrelated source files.

The file inventory was checked at revision `9b85bac06597d4435fd078f6bed0f30bb008542b`. It describes published assets, not complete source coverage. Published plans/manifests do not establish that the underlying originals or full text are present.

Download individual assets with `hf_hub_download("edithatogo/nz-health-appropriations", filename="PATH_FROM_FILES_TAB", repo_type="dataset", revision="9b85bac06597d4435fd078f6bed0f30bb008542b")`. Use your own approved token only if the repository requires gated access. Keep the revision and available source checksums with derived results.

Viewer subsets use `train` as the Hub loading split, not as a prescribed scientific training partition. Different subsets may have different schemas; do not concatenate them without checking fields and units.

For reproducibility, cite the dataset identifier and pinned revision together with the upstream source and source-specific attribution. Report metadata or integrity concerns to the [archive project issue tracker](https://github.com/edithatogo/archive-govt-nz/issues); include the dataset/revision/path, and avoid posting sensitive payloads. Repository code licences do not override original-document rights.

## Budget 2007 and Budget 2008 Vote Health supplement

This supplement adds 160 Budget 2007 and 215 Budget 2008 expense observations,
4,875 field-lineage rows and 1,500 numeric witnesses. The edition and period
are separate. For period ending 2008, the two editions provide Main Estimates
and Estimated Actual respectively. Amount scale and currency are unverified
and remain null. The supplement is source-separated from existing donor and
Gold tables.

The Treasury, New Zealand. © Crown Copyright. Derived from the Treasury Budget
2007 and Budget 2008 expense workbooks under CC BY 4.0. The supplement includes
source coordinates, typed transformations and numeric evidence. See the
[resource-specific rights and provenance record](metadata/budget_2007_2008_rights.json)
for the exact workbooks, hashes and changes. It supersedes the extraction-time
rights state for these six supplementary files.

## Recovered Budget expenses and revenue

This supplement adds Vote Health expenses from Budget 2009–2019 and revenue
from Budget 2007–2019 and Budget 2025. Edition, reporting period and amount type
remain separate. Source cells and numeric witnesses support the legacy BIFF8
tables. The 2025 revenue table has its own schema and field lineage. Use the
recorded units and flags. Unknown units, currency and comparability remain
unresolved wherever flagged in the source recovery.

The Treasury, New Zealand. © Crown Copyright. The listed workbooks are reused
under CC BY 4.0. See the [source rights and lineage record](metadata/budget_recovery_licence_and_lineage.json)
and [file checksums](metadata/budget_recovery_supplement_manifest.json).
