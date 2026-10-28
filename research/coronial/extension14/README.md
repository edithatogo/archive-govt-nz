# Coronial delay: extension14 replication view

Creator: Dylan Mordaunt. Prepared29October2026 for the descriptive study of NZ
coronial delays, their consequences, international comparisons and policy reform.
This extends the earlier coronial research recipe without replacing its history.

Run Python3.15.1, standard library only:

    python reproduce.py /tmp/coronial-extension14-results

Compare the17generated files with results/ by SHA256. The11input files are
explicitly hashed in input-manifest.json. To reproduce plots with R4.3.0,
ggplot2 3.4.3 and Cairo:

    Rscript --vanilla code/plot.R . /tmp/coronial-extension14-figures

The recipe reproduces calculations from retained aggregate extractions, including
all8Australian jurisdictions and missing codes. It preserves different clocks,
cohorts, units, fiscal bases and source editions. It does not infer causal effects,
rank jurisdictions or estimate missed referrals. Original extraction code is
retained separately in code/source-analysis.py with source hashes/locators and
row-lineage.json. The conceptual cascade is a separate DOT source, not measured
causal effects or participant validation.

The NIIO PDF and StatsNZ workbook are excluded from this small release. Public
reproduction reads the1254retained age cells, checks monthly totals and carries
the saved denominator-eligibility inventory as context. That is not an independent
re-extraction or revalidation of the excluded originals. Fetch publisher originals
and verify their listed hashes to audit extraction. Raw-source redistribution
limits are explicit in raw-source-catalogue.json and RIGHTS.md. The seven earlier
rights-cleared originals remain in the isolated immutable core snapshot:
https://huggingface.co/datasets/edithatogo/archive-govt-nz-global/tree/9ff39f9834de26754c3a80a7fe555456707fcbec/coronial/batches/95035b1e7b5056df696919ed202057a42ea3abb6940a699cda638c17137c489d

Code/data identity does not establish scientific truth, journal acceptance or
permission to submit. No manuscripts or private records are distributed here.
