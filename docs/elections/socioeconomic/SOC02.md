# SOC02 — isolated implementation candidate

Plan: [SOC02-ingestion.md](https://github.com/edithatogo/archive-govt-nz/blob/95a51792c85e60ee85875c538c877974b40f26f3/conductor/tracks/election_platform_frontier_20261111/data_maximisation_20261116/socioeconomic_tranche_20261116/SOC02-ingestion.md).
Status: functional offline candidate; **draft / not adopted / not deployed**.

## Implemented

Strict retained-CSV profile adapter with exhaustive dimension selection, source/profile hashes, unit scaling, missingness/confidentiality, original row locators and resource limits.

## Files and dependencies

- `src/archive_govt_nz/domains/elections/soc_ingestion.py`
- `tests/test_elections_soc02_ingestion.py`

SOC01 common records. Develop/review in parallel with SOC03 after the shared interface is admitted.

## Executed diagnostic evidence

22 focused synthetic tests pass in the external isolated candidate under **CPython 3.13.5**; failing-before-implementation and passing-after evidence retained. Combined six-track candidate: 109 tests pass; branch-aware candidate coverage 98%. Independent standard-library correlations, direct leave-one-out recalculation and count conservation are included where applicable. This is author implementation/self-review, not an independent reviewer approval.

The canonical repository requires **repo-local CPython 3.15.1**, `./scripts/test-focused.sh`, `./scripts/validate.sh`, applicable release/mutation/security gates and exact-head hosted checks. Those native/full-repository gates are **not executed or satisfied by this diagnostic evidence**. No existing dependencies, CI, coverage floors, shared contracts, registry, native archive, Space or main branch changed.

## Remaining gates and implementation

No Stats NZ production profile or real source cells admitted. ADE/SDMX discovery and existing Arrow/Polars output wiring remain with the existing owner.

- [ ] Existing election/shared owner accepts the proposed leaf interface and paths.
- [ ] Independently reviewed real source/rights/coverage cohort.
- [ ] Required CPython 3.15.1 environment and full candidate harness.
- [ ] Scoped format/lint/type and relevant mutation/security qualification.
- [ ] Independent resulting-head review and all applicable current-head checks.
- [ ] Sole coordinator acceptance/integration; public release requires a separate permitted operation and serving evidence.

## Reproduce the diagnostic candidate

Run `PYTHONPATH=src python -m pytest tests/test_elections_soc02_ingestion.py -q` in an isolated copy with its declared prerequisite modules. This standalone command is **not a substitute** for the repository wrappers or native full harness. All fixtures are synthetic, using `example.org`; no factual NZ socioeconomic observations or private original bytes are included.
