# SOC04 real source cohort — 16 November 2026

The official Census/turnout capture is retained in Actions run43853935316, artifact14220795860. SOC02 now normalises four Census workbooks (2020/2025 general and Māori boundaries) and the 2023 electorate-by-age turnout table; original/derived identities remain separate.

`tools/build_soc_official_panel.py` consumes the SOC02 `census-long.json` and `turnout-age.json`. It selects 2020-boundary 2023 median personal income and groups the eleven non-overlapping age bands into electorate turnout counts. It uses exact source labels on the same boundary vintage, with no interpolation or fuzzy matching. `tools/verify_soc_official_panel.py` is explicit real-data verification using `SOC_NORMALISED`; it is not an unconditional unit-test dependency on absent downloaded data.

Local executed result: **72/72 electoral areas matched**, with no unused Census area and no dropped electoral area. Six source-anchor/negative tests passed on Python3.13.5. Native3.15.1 execution and full repository assurance remain pending for this new real-panel adapter; no old diagnostic pass is transferred.

All rows retain Census original hash/cell, turnout original hash/source rows, indicator status, numerator/denominator and a different-populations/same-area-context warning. Census Māori tables describe Māori-descent residents, not Māori-roll electors. Voters in the official turnout workbook include identified people who cast or attempted a vote; the totals are not required to equal valid ballots. Compilation dates in2025 mean this is a **retrospective** panel, not a pre-2023 forecast.

Next finite work: bind this adapter to independent normalisation-manifest pins; qualify the native runtime and complete harness; add more admitted indicators and a versioned canonical geometry key rather than expanding name matching; independently review cohort provenance and population definitions before interpreting or publishing associations. Do not mark SOC04 complete or deploy this dataset to the Space on this receipt.
