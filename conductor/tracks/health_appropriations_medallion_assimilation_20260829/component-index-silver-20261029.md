# Component-index Silver normalization

Refs #207, #209 and #211. This source-separated normalization reads the exact
retained LCI and PPI CSV and query objects only after verifying the complete
component evidence cohort, including its response bindings. It writes quarterly
facts, source-cell lineage and row dispositions. Missing publisher tokens remain
null with their original tokens; decimal text and scale are retained. The
internal table-and-selector key is not a claimed official full series code.
Rights remain `not_evaluated`; no analytical policy, fiscal aggregation,
comparability, deflator or publication is selected.

On Python 3.15.1, two native builds per family produced byte-identical output
files and unchanged source hashes. Every source period and token was compared
with its corresponding fact, and both lineage coordinates were compared with
its source row: 135 LCI rows and 270 lineage links; 129 PPI rows and 258 links.
The accompanying machine receipt records the exact input and output hashes.
The 19 focused synthetic evidence/normalization tests and scoped typing pass.
These checks do not establish full phase or track completion; the original
repository harness and protected delivery are separate gates.

The first native output attempt failed because the shared fact schema requires
`series_id`. The explicit table-plus-selectors key corrected that local defect;
the failed output was retained separately. No source bytes were modified.
