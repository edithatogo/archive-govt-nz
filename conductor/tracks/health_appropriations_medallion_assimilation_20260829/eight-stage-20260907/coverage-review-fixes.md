# Persisted coverage review findings 2/3

Scope: follow-up to 3801a0a803aefdd50fca878618ae70f501d2943e,
limited to verified_coverage.py and its tests. Conductor implement/review
workflow used with the user's focused-validation and dedicated-evidence limits.
Finding 1 (independently pinned Crown observation receipt) is assigned separately
to Meitner; no rebuild_eight, CLI, or orchestration tests changed here.

Nested admission coordinates, source hashes, vintage, identity and observation
fields must agree with the persisted envelope. All duplicated envelope fields
are checked; Decimal amounts compare exactly by value, preserving harmless Arrow
scale padding. Detail sheet/cell and source_sha256 aliases are joined explicitly;
Crown's native identity/source/observation fields are required.

Excluded formula rows require empty record IDs and exceptions, the exact profile
sheet, and the pre-existing exact range/reason contract. Admitted areas require
the literal-context reason and no exceptions. Existing preserved-only contracts
remain enforced. No Gold, rights, or whole-source closure claim is added.

## Validation, 2026-09-07

- Initial tests-first nested/excluded-ID matrix: 14 unexpected acceptances;
  one Crown preserved-only case already rejected. Negative tests rewrite Parquet
  and repin its output hash in MANIFEST.json before verification.
- Final coverage test file: 94 passed; module coverage 111/111 statements and
  30/30 branches, 100%, no coverage exclusions.
- Combined coverage and unchanged eight-stage orchestration tests: 108 passed.
- Cold unfiltered mutation run targeting verified_coverage.py: 118 killed,
  zero survivors, zero cache hits (94 baseline tests passed).
- Ruff check/format, basedpyright on both changed Python files, and diff check
  passed. Self-review confirmed no writer/adapter/v1 changes.
- No full gate or publication performed.

Commands use PYTHONPATH=src and the existing archive-govt-nz/.venv interpreter:
`pytest tests/domains/health_appropriations/test_verified_coverage.py -q`
with `--cov=archive_govt_nz.domains.health_appropriations.verified_coverage
--cov-branch --cov-report=term-missing` for coverage; mutation uses
`--gremlins --gremlin-targets=src/archive_govt_nz/domains/health_appropriations/verified_coverage.py
--gremlin-clear-cache --gremlin-no-coverage-filter --gremlin-workers=4`.

## Retained replay

Existing replay_eight.py replay() executed twice against retained archive bytes,
without changing the recipe or source files. New exclusive output root:
`/var/folders/m9/_g3wndrn04d80ys2382r700r0000gn/T/health-coverage-p2-82dwxag4`.
Both first/second builds verified; all output file hashes and receipts identical.
MANIFEST.json SHA256:
`a2dc3fb25cbe2e3cbd5d137f458cb6b5f02d5dad4d245011f460451048119d7b`.
Counts: budget 215, BEFU 10, HYEFU 10, historical 106, revenue 69,
BEFU detail 80, HYEFU detail 80, Crown 61; additional observations 290.
This validates the nested/area corrections against actual admissions, not the
separately pending Crown receipt join. Rights remain not_evaluated and Gold
selection not_performed. Parent integrated full gate and independent review
remain external to this focused result.
