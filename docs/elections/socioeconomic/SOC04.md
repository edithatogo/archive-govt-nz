# SOC04 — isolated implementation candidate

Plan: [SOC04-joins.md](https://github.com/edithatogo/archive-govt-nz/blob/95a51792c85e60ee85875c538c877974b40f26f3/conductor/tracks/election_platform_frontier_20261111/data_maximisation_20261116/socioeconomic_tranche_20261116/SOC04-joins.md).
Status: functional offline candidate; **draft / not adopted / not deployed**.

## Implemented

Outcome-left exact panels; declared area-context/population relationship; source-vintage digests; reference-age constraints; explicit prospective event instant; missing/unused geography receipts.

## Files and dependencies

- `src/archive_govt_nz/domains/elections/soc_joins.py`
- `tests/test_elections_soc04_joins.py`

SOC01 common records. Real panels require qualified SOC02/SOC03 input cohorts; exact join code has no converter/importer dependency.

## Executed diagnostic evidence

15 focused synthetic tests pass in the external isolated candidate under **CPython 3.13.5**; failing-before-implementation and passing-after evidence retained. Combined six-track candidate: 109 tests pass; branch-aware candidate coverage 98%. Independent standard-library correlations, direct leave-one-out recalculation and count conservation are included where applicable. This is author implementation/self-review, not an independent reviewer approval.

The canonical repository requires **repo-local CPython 3.15.1**, `./scripts/test-focused.sh`, `./scripts/validate.sh`, applicable release/mutation/security gates and exact-head hosted checks. Those native/full-repository gates are **not executed or satisfied by this diagnostic evidence**. No existing dependencies, CI, coverage floors, shared contracts, registry, native archive, Space or main branch changed.

## Remaining gates and implementation

No real electoral/socioeconomic panel or existing shared join-kernel adoption. Real inputs require accepted SOC02/SOC03 contracts and source admission; party identity must be carried in the declared single outcome metric.

- [ ] Existing election/shared owner accepts the proposed leaf interface and paths.
- [ ] Independently reviewed real source/rights/coverage cohort.
- [ ] Required CPython 3.15.1 environment and full candidate harness.
- [ ] Scoped format/lint/type and relevant mutation/security qualification.
- [ ] Independent resulting-head review and all applicable current-head checks.
- [ ] Sole coordinator acceptance/integration; public release requires a separate permitted operation and serving evidence.

## Reproduce the diagnostic candidate

Run `PYTHONPATH=src python -m pytest tests/test_elections_soc04_joins.py -q` in an isolated copy with its declared prerequisite modules. This standalone command is **not a substitute** for the repository wrappers or native full harness. All fixtures are synthetic, using `example.org`; no factual NZ socioeconomic observations or private original bytes are included.
