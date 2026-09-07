# BEFU86 persistence, 2026-09-07

Phase4.2/M-07 AC-03/05 bounded packaging, based on a65e484f in the isolated
HYEFU16 worker. Conductor implement/review used. No umbrella lifecycle edits.
Existing admission now returns its already-computed inventory. Shared writer
and verifier support befu-chart without changing orchestration v1/v2.

Preserves 86 exact records, 430 native field references, all raw context,
15 formula exclusions with native reason formula_cache_not_admitted, and one
preserved-only remainder per sheet. No formula cache admission, totals/netting,
new selectors, periods, currency, rights or promotion decisions.

TDD: 11 failed/one pre-existing pin rejection passed before implementation.
Final focused cold unfiltered mutation command used test_chart_packages,
test_hyefu_allowance_package, test_literal_packages, test_verified_coverage and
test_befu_chart_literals: 154 passed, 228/228 mutants killed, zero cache hits.
Targets: literal_packages.py, verified_coverage.py, befu_chart_literals.py;
options --gremlins --gremlin-clear-cache --gremlin-no-coverage-filter
--gremlin-workers=4. PYTHONPATH=src, shared archive-govt-nz/.venv interpreter.
Ruff and basedpyright checked changed Python files. No full harness.

Actual replay.py independently resolves source OOXML cells, validates 86 numeric
tokens and 15 formula nodes, compares all persisted native JSON fields, amounts
and field references. Two builds byte-identical under
/var/folders/m9/_g3wndrn04d80ys2382r700r0000gn/T/health-befu86-vcr5q3rv.
Source SHA256 cf98f5e21f60c76c7d05f788df7955fb45cfdd780c12cb18e26ff8e83615e168 unchanged.
Output SHA256:

- MANIFEST.json: 14088607bd4211104f69d1cf4553bea515705971cb47604feef8af709a2a26ea
- literal_facts.parquet: 38a9728ca4daf15a48eed360faea7f0ffc144e7d7528892f287e156746c38123
- field_lineage.parquet: fa377f7c881e098d2098ed9045e39acb9a4cd884ae3b89e0f5e132b3297843a3
- area_dispositions.parquet: c50ae4cb20626b5e087ec7cb2622eeadf46077aa6058c74e5e53eeaa7dd7f410

Two HYEFU16 regression builds under health16-regression-q3y8t3k_ in the same
temporary parent matched all four a65e484f replay.json file hashes exactly.
The replay timestamp remains explicit donor context, not a new capture claim.
Self-review: no parent, original-byte, rights, promotion, Gold or v1/v2 changes.
