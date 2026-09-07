# Stage 1: persist existing literal admissions

Base `de2d3a25e3f09ed520a238b22a61cde11f70e5fe`; M-04/M-05/M-07/M-15/M-18,
AC-03/AC-05/AC-13/AC-16. Dedicated evidence only, no shared lifecycle change.

`literal_packages.package_admitted_source` invokes the existing pinned detail
or Crown admission, then uses the existing exclusive workbook writer. The
detail admission now returns its already-computed inventory instead of
discarding it. No parser, formula evaluator, capture, Gold or rights logic is
added. Revenue already has its own package and is unchanged in this commit.

An explicitly profile-tagged literal transport schema retains decimal128(38,17)
amounts and the complete source admission record as deterministic JSON. JSON
preserves original field names, nulls, notes, source-reference chains, temporal
context and Crown's field-to-coordinate map. A separate context-lineage table
indexes raw evidence; it is not a new canonical semantic-field mapping. Detail
occurrences get profile/source/sheet/cell IDs; Crown's existing record and
observation IDs and observation time survive packaging. A run timestamp cannot
replace the Crown observation. Source-bound operational admission is distinct
from the documented pure writer used by synthetic transport tests.

Area dispositions retain each admitted cell, detail formula-total range
exclusions and each sheet's remainder expressed as `whole_sheet` minus explicit
selectors. These states are adapter-scoped: `admitted`, `excluded`, and
`preserved_only`, not globally normalized or Gold-ready. The versioned runner
and verified coverage join are the next commit, not claimed here.

Tests began red with missing module. Self-review added a red Crown observation-ID
regression when timestamp reformatting changed the generated identity; corrected
by retaining the existing source observation ID. Sixteen focused package tests
pass with 57/57 statements and 14/14 branches covered. Ninety affected tests
(packages, detail, Crown, shared writer) passed before that narrow ID fix;
the package suite was rerun afterward. No coverage exclusions or mutant pardons.
Final cold mutation run killed 29/29 mutants with zero survivors/cache hits.

Commands use the existing repository environment and `PYTHONPATH=src`:

```sh
python -m pytest tests/domains/health_appropriations/test_literal_packages.py -q --cov=archive_govt_nz.domains.health_appropriations.literal_packages --cov-branch --cov-report=term-missing
python -m pytest tests/domains/health_appropriations/test_literal_packages.py tests/domains/health_appropriations/test_donor_health_detail.py tests/domains/health_appropriations/test_fiscal_crown_literals.py tests/domains/health_appropriations/test_workbook_common.py -q
python -m pytest tests/domains/health_appropriations/test_literal_packages.py -q --gremlins --gremlin-targets=src/archive_govt_nz/domains/health_appropriations/literal_packages.py --gremlin-clear-cache --gremlin-workers=4
```

Ruff and basedpyright cover package, tests and replay. The mutation tool's
previously-imported-module warning is separate from the focused coverage run.
`replay_packages.py ARCHIVE_ROOT NEW_OUTPUT_ROOT` compares all 221 persisted
record JSON documents and exact amounts against the already source-qualified
admissions across two deterministic builds. The retained source files and all
output payloads stay outside Git; see `packaging-replay.json`. This is transport
replay, not a second independent source-semantic parser. Independent source
replays are retained with the original detail/Crown implementations.

Conductor implement/review skills guided TDD and self-review. Parent owns
independent review and full integrated harness. No full gate/publication or
whole-programme completion is claimed.
