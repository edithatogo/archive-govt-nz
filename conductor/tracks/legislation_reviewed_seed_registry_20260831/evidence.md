# Evidence

Target base `8ebbb69ddbf8268cd85c2df8885645943b0ab525`; donor archived at `b40587f1b1aec7356a0f623916fcc8212397d283`.

Seed verified against Prompt 03 package SHA and inventory entry before restoration. Original review provenance is donor PR #51; this is inherited review status, not a fresh approval.

## Focused evidence

- `evidence/seeds/historical-work-ids-0001/provenance-01.json`: exact original
  bytes, donor artifact/run/commit, original review merge and broader inventory.
- `evidence/seeds/historical-work-ids-0001/coverage-01.json`: critical validator
  54/54 executable lines and 6/6 branches; no exclusions.
- `evidence/seeds/historical-work-ids-0001/mutation-01.json`: 14/14 targeted
  integrity mutants killed, with per-attempt log hashes and exact code hash.
- Initial red test failed because the resolver did not yet exist; focused green
  tests now pass. A typing failure and accidentally overlapping validation run
  are retained in the run log and final validation attempt index.

## Reproduction

```sh
uv run pytest tests/tools/test_seed_registry.py -q
uv run python tests/tools/run_seed_registry_mutations.py /absolute/new/output-directory
./scripts/validate.sh
```

For critical coverage, run focused tests with `--cov=tools --cov-branch
--cov-report=json:coverage-seeds.json --cov-fail-under=0`, then inspect and require
zero missing lines and branches specifically for `tools/seed_registry.py`.
The zero global threshold here prevents unrelated, unexecuted tools diluting a
focused measurement; it does not replace the native 95% overall harness gate or
the 100% critical-module requirement. Full assurance and exact-head hosted
results are recorded separately, not inferred from this focused measurement.

## Final local validation

`evidence/seeds/historical-work-ids-0001/validation-01.json` binds the implementation revision, source hashes, native full run, failed/superseded attempts and security receipt hashes. Full attempt 03 passed 2,921 tests at 97.09% aggregate coverage after integration of target base `af427c2632239a8869684c849c0fcc1981277b02`. Exact-head hosted checks and delivery are still separately required.
