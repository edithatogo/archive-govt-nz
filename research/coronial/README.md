# Coronial delay: reproducible descriptive analysis

This public research recipe reconstructs the New Zealand annual series and checks Australian count/share comparisons from aggregate government statistics. It is distinct from raw-source archiving on Hugging Face. It contains no manuscript, reviewer correspondence or individual-level case data.

## Reproduce

Use the repository-qualified Python 3.15.1 interpreter (standard library only):

```sh
.venv/bin/python research/coronial/code/reproduce.py research/coronial
.venv/bin/python research/coronial/code/check_sensitivity.py research/coronial
```

The first command verifies 100 retained NZ extraction rows, 95 distinct edition cells, 55 latest-edition display cells, and the recent-period alternative-edition sensitivity. It uses explicit publication order, not file dates, to select the latest retained values. This is a display rule, not proof that a later administrative count is more accurate. The second checks counts, shares and change across all eight Australian jurisdictions. Annual means cannot reconstruct individual waiting-time distributions. Australian published coronial statistics can include fire matters. International clocks and populations are not pooled or ranked.

Original source files are identified in `raw-source-catalogue.json`, including publisher URLs and exact hashes. `raw-archive.json` records the actual publication status. Seven rights-cleared raw objects and their provenance are published in an [immutable source snapshot](https://huggingface.co/datasets/edithatogo/archive-govt-nz-global/tree/9ff39f9834de26754c3a80a7fe555456707fcbec/coronial/batches/95035b1e7b5056df696919ed202057a42ea3abb6940a699cda638c17137c489d) using archive-govt-nz content-addressed storage and Bronze manifests. Every published file was independently downloaded without authentication and matched by SHA-256 and byte size. Twelve further source records provide metadata and publisher links where full-file redistribution was not qualified. The snapshot is on an isolated revision of the existing archive; the commit-pinned link remains reproducible independently of main-branch updates. Some complete source files cannot be redistributed in this batch because their full-file rights were not qualified. Download those originals from the listed publisher URLs and check their hashes. Aggregate data and code here allow arithmetic reproduction independently of private files; source extraction still requires reading those originals. Numerical data were transcribed from the specified public source tables and are not individual-level records.

## Rights and attribution

Code is Apache-2.0 under the repository LICENSE and NOTICE. Source documents retain their own terms; that code licence does not apply to them. NZ numerical observations: Ministry of Justice / Coroners Court of New Zealand, Crown copyright, source-specific CC-BY terms. Australian observations: based on Productivity Commission data (CC BY 4.0). England and Wales: Ministry of Justice, Crown copyright, Open Government Licence v3.0. Other international aggregate figures retain named original publisher attribution in the observation tables. No official endorsement is implied.

This recipe performs descriptive arithmetic and sensitivity checks, not a causal evaluation, international performance ranking, systematic review, or validation of the underlying administrative records. To regenerate the retained descriptive plots, run `Rscript research/coronial/code/plot.R research/coronial` and `Rscript research/coronial/code/plot-comparison.R research/coronial`. They use R graphics and require the named font/device support; rendering is separate from the standard-library numerical checks. The conceptual cascade DOT source records a proposed pathway, not an empirically estimated model.
