# Run Log

## 2026-08-26 — REQ-MUT-001 and REQ-MUT-002

- `./scripts/validate.sh` — failed at the fast formatting gate because
  `tools/run_gremlins.py` would be reformatted; downstream gates did not run.
- `uv run pytest --help` — confirmed the installed `pytest-gremlins` plugin
  exposes mutation targets, operators, reports, cache, parallelism, coverage
  filtering, and pardon-budget options.
- `uv run pytest tests/test_pytest_gremlins_config.py -q` — red phase observed:
  the dependency lacked its `<2` compatibility bound and no configuration
  contract was present.
- `uv lock` — resolved 104 packages and synchronized the `<2` bound.
- `uv run --locked ruff format --check tests/test_pytest_gremlins_config.py` —
  passed after import ordering was normalized.
- `uv run --locked ruff check tests/test_pytest_gremlins_config.py` — passed.
- `uv lock --check` — passed.
- `uv run --locked pytest tests/test_pytest_gremlins_config.py -q` — green
  phase passed, 1 test.
- `uv run --locked basedpyright tests/test_pytest_gremlins_config.py` — passed
  with 0 errors, warnings, or notes.
- `uv run --locked python tools/supply_chain.py audit` — passed; no known
  vulnerabilities found.
- `uv run --locked python tools/supply_chain.py licenses` — passed;
  `pytest-gremlins` 1.9.0 reported the MIT License.
- `uv run --locked python tools/supply_chain.py secrets` — stopped after the
  generated coverage tree made the repository-wide `--all-files` scan
  unbounded for this task.
- `uv run --locked detect-secrets scan --all-files --force-use-all-plugins
  pyproject.toml tests/test_pytest_gremlins_config.py
  conductor/tracks/testing_parallel_mutation_profiling_20260826` — bounded
  task-scope correction passed with zero findings.
- `./scripts/validate.sh` — lock passed; the repository gate stopped at format
  because the preserved later-task file `tools/run_gremlins.py` would be
  reformatted. The remaining 1171 files were formatted; downstream stages did
  not run.
- Functional commit: `ab4ed66` (`build(test): configure pytest-gremlins`).

## 2026-08-26 — REQ-MUT-003 runner

- `./scripts/validate.sh` — red checkpoint reproduced: lock passed and Ruff
  rejected the existing untracked `tools/run_gremlins.py`; downstream gates
  did not run.
- First bounded implementation hardened report validation, timeouts, atomic
  writes, and output redaction. Its five-file run emitted 242/242 but pytest
  exited 2; direct diagnosis showed clearing project `addopts` caused seven
  duplicate-module collection errors, so that report was rejected.
- Preserving project `--import-mode=importlib` resolved collection integrity.
  A fresh-cache five-file run then failed closed at the 300-second timeout,
  showing that target set was too broad for the repository stage budget.
- The target set was narrowed to the Medallion schema and NLP export boundary;
  existing repository-owned mutation runners retain broader module coverage.
- `uv run --locked ruff format --check tools/run_gremlins.py` — passed.
- `uv run --locked ruff check tools/run_gremlins.py` — passed.
- `uv run --locked basedpyright tools/run_gremlins.py` — passed with 0 errors,
  warnings, or notes.
- `uv run --locked python tools/run_gremlins.py --help` — passed without
  starting mutation execution.
- `uv run --locked python tools/run_gremlins.py --timeout-seconds 300
  --clear-cache` — passed within the bound: 42/42 mutants zapped, 100%, zero
  survivors, errors, timeouts, or pardons. Receipt and plugin-report outputs
  are local generated artefacts.
