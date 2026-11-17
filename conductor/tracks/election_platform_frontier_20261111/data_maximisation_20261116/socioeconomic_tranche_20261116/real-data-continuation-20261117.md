# SOC socioeconomic delivery — 17 November 2026 continuation receipt

Status: **partial implementation, not merged, not deployed**. The sole integrator and shared dashboard owner defined in [coordination #867](https://github.com/edithatogo/archive-govt-nz/issues/867) retain merge and HF publication decisions. All implementation outcomes below refer to exact source/head or hosted receipts, not the status of the public Space.

## What was implemented in the existing track PRs

| Track | Working candidate | Evidence | Remaining gate |
| --- | --- | --- | --- |
| SOC01 [#872](https://github.com/edithatogo/archive-govt-nz/pull/872) | Retained-byte inventory, four official Stats NZ Census original SHA pins; new manual-only content-addressed HF preservation tool and workflow | Five offline Python tests passed on 3.13.5; explicit runtime rights gate, source hash, symlink, duplicate, incomplete-inventory and no-overwrite controls | Full current-head CI and existing owner/rights approval; manual HF activation and actual remote bytes unperformed; never upload separately licensed Electoral Commission source under Stats NZ rights |
| SOC02 [#873](https://github.com/edithatogo/archive-govt-nz/pull/873) | Rights- and SHA-bound Census/turnout parsing, expanded 22 Census table-family extraction, strict Arrow IPC/Parquet exporter, locked 3.15.1 hosted workflow and source-output roundtrip | Initial official 8,046 Census rows/792 turnout exported to Parquet + Arrow with explicit original value/text and 12 suppressed; hosted run 44071554793 passed, artifact 14323206694 SHA256 `158cd5d0d86a09a4eb06aa12019e5c64e63d8fcdb2a534a7950ca6fb9320f2d8` | 34,208-row expanded export pending new hosted run; source/row checks and format/type/security/current-base full harness must pass; manual HF publication unperformed |
| SOC03 [#874](https://github.com/edithatogo/archive-govt-nz/pull/874) | Source-bound count concordance and rates, suppression propagation | 17 synthetic focused tests earlier (3.13.5) | Official population weights, SA2 identifier and source-rights qualification, native full CI |
| SOC04 [#875](https://github.com/edithatogo/archive-govt-nz/pull/875) | Real 2023 retrospective 72/72 electorate median income/turnout join on 2020 boundaries, explicit separate resident and registered-elector populations | Prior real-source cohort and six negative-control tests | Extended 13-indicator/party-vote joins, source naming, native full CI and independent scientific review |
| SOC05 [#876](https://github.com/edithatogo/archive-govt-nz/pull/876) | Real 2023 age-standardised national/same-roll turnout; descriptive correlations and leave-one-out sensitivity | 144 outputs with independent reference checks, 38 refinement tests run locally earlier | Native full CI (Ruff format first failure), spatial uncertainty/age composition bias and independent methods review |
| SOC06 [#877](https://github.com/edithatogo/archive-govt-nz/pull/877) | Synthetic-only publication contracts with checksum/last-good rollback; additionally prepared a **local candidate** 72-area HTML/JSON data explorer with income, employment, housing, qualification, age and age-standardised turnout choices | Local preview had 7 passing tests and local SOC05 sensitivity had 6 (13 total) on 3.13.5; it preserves source pins, 2020-vintage scope, no synthetic/causal misrepresentation and verifies two input CSV hashes | The standalone preview implementation and source-gated tests are now committed to SOC06 #877 (head e109273bc72c8b03f6779407ec83cbe330a98beb), but **not served on HF**; existing Space owner must select design, independently validate it on 3.15.1, integrate, run browser/a11y checks and verify served SHA |

## Official data and source preservation

Four 2023 Census workbook cohorts are direct electorate-level data published by Stats NZ and served through New Zealand Parliament. General/Māori and 2020/2025 boundaries must remain distinct. Current native datasets were acquired with original SHA-256s in `data/soc-official-profiles.json` and retained in GitHub Actions artifact run `43853935316` (expiry **16 December 2026**). SOC01 proposes an explicit manual process to preserve **only four Stats NZ CC BY workbooks** in HF's public dataset by content-addressed paths. An operator must verify rights, approve, enable trusted main dispatch, supply `HF_TOKEN` and independently confirm remote bytes; **none of these actions has been claimed complete**. The Electoral Commission's separately licensed turnout files require an independent rights disposition.

The existing HF dataset has historical electoral boundary and vote Parquet files, but no socioeconomic Census or turnout artifacts were found by the November 17 HF filename inventory. Do not assume absent originals from an incomplete filename search; reconcile against the full CAS manifest/rights/coverage.

## Data and analytical definition holds

- The Census values refer to **2023 resident populations**; 2023 turnout uses **enrolled electors**. Māori-descent resident Census statistics are not Māori-roll elector statistics. Area-level joins do not identify individual political behaviour or establish causation.
- Original Census counts can be randomly rounded, suppressed and non-additive across overlapping domains. Never aggregate medians by summing/averaging. Preserve suppressed as null.
- Census workbooks for 2025 boundaries can be used to provide **2026 electoral geography context**; do not retroactively label them 2023 election-vintage areas. Historical 2023 electoral outcomes use 2020 boundaries.
- The first run of the Arrow exporter passed using repository-locked Python 3.15.1. The broader 34,208-record new export requires **its own** exact-head hosted tests and new output hashes before declaring columnar completion.
- The viewer preview is not the live Space. It explicitly says candidate/not published, identifies historical source years and maintains distinct observations vs publication timestamps.

## CI and merge-blocking evidence

- Workflow policy initially failed due missing `concurrency` in SOC01 and SOC02 workflows. Both were patched and their next isolated policy-lint jobs passed.
- Full CI for SOC01/SOC02/SOC05 remains held on Ruff formatting of both new and older election source files, plus additional dependent stages. Do not suppress `ruff format --check .` or waive coverage. Coordinate pre-existing shared election files through their owner in [#866](https://github.com/edithatogo/archive-govt-nz/pull/866).
- Hosted CodeQL and privacy had passed for scoped heads when checked, but those passes must be repeated at current receiving head. A green source-normalisation job does not substitute for complete `./scripts/validate.sh`, release/mutation/security, independent review or the sole integrator's admission.

## Next non-overlapping implementation order

1. **SOC02:** independently verify the 34,208-row Arrow/Parquet source-normalisation artifact (new exact run, export receipt SHA and suppression consistency); preserve a reviewable candidate under the existing PR. If the artifact fails, repair only SOC02-owned files and retain failing receipt.
2. **SOC01:** qualify and apply the manual rights-gated content-addressed original preservation using a verified HF readback on trusted main, once owner approval and branch checks pass. Do **not** upload the public Election Commission workbook without separate rights review.
3. **SOC01+02 native assurance:** format owned files to current Ruff requirements, run focused tests and full native 3.15.1 harness; route the separate pre-existing shared election formatter and policy defects to #866 owner.
4. **SOC04+05:** integrate existing 72/72 source-backed electorate panel, 13 indicators and 144 age-standardised observations with the verified columnar outputs; validate null/alias, overlapping population, time and boundary invariants, and descriptive scientific limitations.
5. **SOC06:** choose/qualify a chart/table UI in the existing HF Space and publish only after source licence, snapshot, accessibility, static export and served-revision checks. Preserve last known good public release; do not claim natural refresh without observed scheduled captures.
6. **Broader sources and analyses (separate admitted tracks):** NZDep2023 deprivation, MBIE tenancy bonds, Stats NZ prices/employment/income, distinct neighbourhood SA2 boundaries, 2026 result vintages and party finances; each needs its own original source, rights, grain, temporal join and accepted scientific test.

No new parallel integrator, CI waiver, silent merge, unsanctioned publishing, or source acquisition should follow merely from this plan. All checkboxes remain held until actual accepted evidence exists.
