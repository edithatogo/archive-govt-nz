# Forecast source-validation preflight

The explicit `dry_run=True` option validates the pinned original, bounded
workbook structure, profile/vintage and source extraction without constructing
Arrow tables or calling the package writer. Only real booleans are accepted.
The existing default and explicit `False` both retain the writing contract.
All four existing profiles remain supported; Actual and Forecast observations
are not pooled or relabelled.

The JSON-compatible receipt reports `planned` only for a complete dry run;
rejected cells still produce `partial`. It omits output hashes and declares
`preflight_scope=source_validation_only`. This is not serialization assurance,
output-location validation, write readiness, rights approval or publication.
The unused output may already exist: this API does not inspect or mutate it.
The future CLI/MCP wrapper can impose a stricter output-location contract.

## Local evidence

- Initial red test: the API rejected the new keyword. First implementation
  passed 14 tests and failed four tuple/list receipt comparisons. A further
  red test required the explicit preflight scope. JSON normalization fixed
  those failures without changing the writing path.
- 42 new tests pass; the combined legacy, successor and preflight selection
  passes 92 tests with 100% coverage (131 statements, 52 branches). Ruff and
  basedpyright pass. Independent full source/test review found no actionable
  issue. Functional checkpoint: `a85ca41`.
- New tests prohibit both Arrow construction and package-writer calls during
  preflight, preserve partial/error/interrupt behavior, enforce strict flags,
  and check preservation of existing output files, directories and originals.
- A separate pre-change baseline and final-code run use the same synthetic
  workbook bytes for each profile. All four packages (16 output files) are
  byte-identical: 20,384; 20,252; 24,154; and 24,164 bytes respectively. Each
  original SHA is unchanged. New `after-final` directories preserve both the
  earlier `before` and intermediate `after` packages.
- One baseline-script invocation lacked `PYTHONPATH=.` and failed importing
  test helpers before creating outputs; the corrected invocation succeeded.
- Production SHA-256:
  `a69d91657ea7c0940504c34477759ca7397bef312ba1bf856c81a0962fcf426f`.
  Test SHA-256:
  `1f64756e3fd0e721f22143329d93e4284b79e01530c787b90be408934f00e904`.

- Cold unfiltered mutation passed all 66 generated mutants with one worker:
  zero survivors, timeouts, errors, pardons and cache hits; 92 tests, 77.93 s.
  Report SHA-256:
  `7968817bdd5390542decf564ba760e51108dad1a2c33dd9b56004f18ab344d43`.
  The report retains a coverage module-already-imported warning; it did not
  filter mutant selection or reduce the test selection.

Main `9032f8f` was integrated as `ce19d85`, retaining all incoming ledger
entries as an exact prefix and both run-log additions. Production and test
hashes are unchanged. All 92 focused tests pass again (6.51 s), and Conductor
validates 75 tracks. An initial guessed validator filename did not exist
(exit 2); the actual `tools.validate_conductor_state` module passed. The cold
mutation coverage fragment was retained outside the checkout, not deleted.

Full native assurance and exact-head hosted delivery are still pending.
No real original, retained package, candidate or Hugging Face bytes
were modified by these synthetic tests. Broader track phases remain open.
