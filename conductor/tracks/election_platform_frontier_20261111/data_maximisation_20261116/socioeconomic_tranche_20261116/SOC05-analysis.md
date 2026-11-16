# SOC05 — socioeconomic questions and analytical qualification

Status: pending real-data qualification. External prototype demonstrates synthetic rate derivation and unweighted area-level association only. Depends on SOC04, with original outcomes O03/O05/O07/O10/O11/O12/O14 retained rather than duplicated.

## First outcome set

| Question | Required joined data | First defensible output |
| --- | --- | --- |
| Where do turnout and enrolment differ by age, education, income and tenure? | Electoral denominators plus source-native compatible Census context | Coverage-aware geographic profiles and descriptive associations |
| How do rent, housing tenure/crowding and income distributions vary alongside vote shares or changes? | Target-boundary household/person tables and one party/election-vintage outcome | Source-linked descriptive comparisons; no individual-voter inference |
| Do spending comparisons change when expressed per eligible voter or alongside area-level context? | Already qualified finance, electoral denominators and SOC04 | Transparent numerator/denominator comparisons, not causal ROI |
| How do economic conditions relate temporally to election outcomes? | Published national/regional labour, income and CPI series; dated results | Contextual time/area analysis at published geographic support |
| How do local and national participation patterns compare? | Separately defined local/national eligible populations, rules and geographies | Qualified comparison, not pooled unlike turnout denominators |

## Executable tasks

- [ ] Publish independently verified profiles and counts before fitting models. Preserve perturbation, survey uncertainty, missingness and as-of boundaries.
- [ ] Implement area-level summaries with sample size, exclusions, units, lag and source coverage; suppress output when no valid variance or insufficient observations.
- [ ] Use independent numerical references. The external reference checks Pearson r against Python's separate standard-library correlation implementation; synthetic agreement is not an empirical finding.
- [ ] Before multivariable/historical models, pre-specify estimand, clustering/spatial dependence, confounding, measurement error, multiple comparisons and spatial/time-blocked evaluation. Do not substitute built-in p-values for identification.
- [ ] Treat rates computed from rounded counts as derived with input quality flags. Never recover suppressed cells, infer individual ethnicity/political affiliation or call an ecological relationship causal.

## Handoff prompt

Implement one SOC05 descriptive outcome using only an admitted SOC04 panel. Return data/method/source receipts, coverage/exclusions and an independent arithmetic reference. Leave causal effects, voter switching and intervention claims not_estimated unless a separately reviewed design and suitable source data establish them.
