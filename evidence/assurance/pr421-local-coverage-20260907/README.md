# PR421 local coverage repair

Test-only slice from `bb14b88f`; diff merge base with the locally available
`origin/main`: `8d38c3bea6ad8d3e94add33d4e5ee91f69aced38`.
No external provider inspected. No hosted result is inferred from this proof.

## Local baseline

Read parent `.coverage` without modifying it:
`/Volumes/PortableSSD/GitHub/archive-govt-nz-health-foi-integration-20260907/.coverage`.
SHA-256: `2006d0355889603008f9be6fd539f3427f792ab19dfebb5ba6a6b7018501f268`.
Intersected executable statements from `Coverage.analysis2` with added line
ranges from `git diff --unified=0 origin/main...bb14b88f -- src tools`.

| Changed package file | Changed statements | Missing locally |
| --- | ---: | ---: |
| capture.py | 12 | 0 |
| donor_parity.py | 118 | 0 |
| population_context.py | 53 | 0 |
| population_export.py | 79 | 0 |
| source_context_census.py | 83 | 0 |
| foi_candidate_cohort.py | 119 | 6 |
| foi_candidate_probe.py | 245 | 39 |
| foi_linked_assessment.py | 129 | 0 |

Cohort missing lines: 278-282, 290. Probe missing lines: 146, 157-158,
163-164, 166-167, 232-240, 359, 370, 397-398, 430, 433-435, 439-444,
475-476, 492-493, 503-505, 510-511.
The 86 changed executable statements in `tools/capture_health_resources.py`
have no measurements in this package-source coverage database. They are not
counted as covered or included in the package denominator; capture remains
parent-owned. No coverage configuration was changed to obtain this result.

## Independent focused proof

Using the parent's existing Python 3.14 environment, from this isolated tree:

```sh
PYTHONPATH=src python -m coverage run -m pytest -q -p no:cacheprovider \
  tests/test_foi_candidate_probe.py tests/test_foi_candidate_cohort.py \
  tests/test_foi_probe_failure_contracts.py
python -m coverage report \
  --include='*/foi_candidate_probe.py,*/foi_candidate_cohort.py'
```

Final: **126 passed in 1.53 seconds**, no warnings. Probe: 245 statements,
70 branches, zero missing/partial, **100%**. Cohort: 119 statements,
34 branches, zero missing/partial, **100%**. Combining these focused results
with the unchanged parent baseline covers all **938/938 changed package
statements**; this is a local evidence union, not a fresh full-harness result
or an external patch calculation.

New tests exercise DNS address selection, classified request failures without
exception leakage, redirects/errors without body reads, per-hop robots refusal,
redirect exhaustion, HTML versus plain metadata, missing robots policy,
parse rejection, duplicate accounting, exact baseline/collector digest bindings,
selection of outstanding candidates, and the real offline CLI entry point.
All HTTP/DNS behavior is synthetic and offline; no endpoints were contacted.

Ruff format/check, focused basedpyright (0 errors/warnings/notes), and
`git diff --check` passed. Test SHA-256:
`50a33938f7f0c80dd6f6d9dc148e4507ee161a799330dc3a741619a70256c975`.
Final ignored local `.coverage` SHA-256:
`ab4e392f916c7448af431fff44b6a6ae24d4781e3fd9843c4285efbd8966241f`.

Initial validation retained here: two Ruff compound-assert findings were
split without weakening assertions. First focused run passed 125 tests but
left the absent-robots branch uncovered and emitted a runpy module-reexecution
warning. Added the absent-robots contract and executed the entry point by path;
final result above is warning-free. No production behavior changed, so no
production RED/GREEN claim is made; baseline missing coverage is the repair's
starting evidence. No thresholds, exclusions, dependency or baseline changes.
No WARC/fsync, filenames, population parameter IDs, lifecycle files, remote
mutations, or full harness; those remain parent-owned.
