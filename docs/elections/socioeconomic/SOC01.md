# SOC01 — isolated implementation candidate

Plan: [SOC01-inventory.md](https://github.com/edithatogo/archive-govt-nz/blob/95a51792c85e60ee85875c538c877974b40f26f3/conductor/tracks/election_platform_frontier_20261111/data_maximisation_20261116/socioeconomic_tranche_20261116/SOC01-inventory.md).
Status: functional offline candidate; **draft / not adopted / not deployed**.

## Implemented

Validated immutable source/cell/series records; pinned pagination coverage; retained-byte verification; rights, conflicting revision and exact-query reuse decisions.

## Files and dependencies

- `src/archive_govt_nz/domains/elections/soc_contracts.py`
- `src/archive_govt_nz/domains/elections/soc_inventory.py`
- `tests/test_elections_soc01_inventory.py`

Pinned main cf64faca56eb50db14b97f534def3a17a89555f9; no changes to pre-existing files.

## Executed diagnostic evidence

23 focused synthetic tests pass in the external isolated candidate under **CPython 3.13.5**; failing-before-implementation and passing-after evidence retained. Combined six-track candidate: 109 tests pass; branch-aware candidate coverage 98%. Independent standard-library correlations, direct leave-one-out recalculation and count conservation are included where applicable. This is author implementation/self-review, not an independent reviewer approval.

The canonical repository requires **repo-local CPython 3.15.1**, `./scripts/test-focused.sh`, `./scripts/validate.sh`, applicable release/mutation/security gates and exact-head hosted checks. Those native/full-repository gates are **not executed or satisfied by this diagnostic evidence**. No existing dependencies, CI, coverage floors, shared contracts, registry, native archive, Space or main branch changed.

## Remaining gates and implementation

No exhaustive GitHub/HF/CAS inventory or real-source/rights admission. Caller-supplied source-rights receipts require independent approval.

- [ ] Existing election/shared owner accepts the proposed leaf interface and paths.
- [ ] Independently reviewed real source/rights/coverage cohort.
- [ ] Required CPython 3.15.1 environment and full candidate harness.
- [ ] Scoped format/lint/type and relevant mutation/security qualification.
- [ ] Independent resulting-head review and all applicable current-head checks.
- [ ] Sole coordinator acceptance/integration; public release requires a separate permitted operation and serving evidence.

## Reproduce the diagnostic candidate

Run `PYTHONPATH=src python -m pytest tests/test_elections_soc01_inventory.py -q` in an isolated copy with its declared prerequisite modules. This standalone command is **not a substitute** for the repository wrappers or native full harness. All fixtures are synthetic, using `example.org`; no factual NZ socioeconomic observations or private original bytes are included.
