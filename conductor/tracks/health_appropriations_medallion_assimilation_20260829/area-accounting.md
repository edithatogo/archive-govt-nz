# Detected donor structural-unit accounting

This is local metadata accounting infrastructure, not a Phase 1/4 completion
claim. It neither detects all data areas nor verifies semantic normalization.
Originals, source-specific packages and publication remain unchanged.

## Contract

`area_accounting.reconcile_areas` accepts immutable JSON bytes and explicit
SHA-256 pins for a donor manifest, format census and optional extraction
receipts. It opens no files and performs no network requests. Its fixity claim
applies only to supplied metadata bytes, not source objects or Parquet outputs.

The detected universe contains inventoried worksheets and named tables,
SQLite oracle tables and one PDF structural observation. A PDF's regex-derived
page count does not establish page or table identities. Charts, formulas and
other structural counts are not invented as analytical data areas.

Legacy census worksheets and current rich workbook-inventory/v1 worksheets
have distinct accepted shapes. Legacy absence of table ranges is retained as
unknown; no richer coordinates are synthesized. Unit identities include the
full source hash, donor path, exact structural selector and contract version.

Every unit defaults to unresolved. Explicit mappings are assertions only.
Partial mappings retain unresolved whole-unit coverage. Explicit exclusions
are scoped to one adapter receipt and never imply global irrelevance. An
adapter's passed status or absence from its exclusions never creates a mapping.
Mappings do not establish source authenticity, semantic correctness, rights or
publication approval. Stored source-cell values and SQLite SQL are not copied.

## Initial validation observations

The first focused run failed collection because the new module did not yet
exist (exit 2); implementation then passed the initial two contracts. Expanded
negative tests initially exposed a shared nested fixture object, so mutating
the receipt also changed the census. Deep-copying the fixture corrected that
test setup, without changing production behavior. The resulting 73 tests pass
at 100% line/branch coverage (157 statements, 34 branches); Ruff and strict
typing pass. Review, additional boundaries and heavier gates remain pending.

A read-only metadata pilot consumed six pinned retained JSON documents: donor
manifest, legacy census and the four manifests in the reviewed raw run. It
opened no original workbook/PDF/SQLite or derivative Parquet. It found 152
worksheets, five SQLite oracle tables and one PDF structural observation: 158
globally unresolved units with 17 explicit adapter-context exclusions. Input
metadata hashes remained unchanged, and reversing extraction-receipt order
gave the same result. No positive mapping assertions were supplied.

This exposes accounting gaps; it does not establish that 158 data tables need
extraction or that adapter exclusions satisfy the entire donor scope. The
three remaining donor workbooks and PDF are still preserved, not discarded.

## Independent review and critical assurance

Review found that unit names alone did not reject contradictory common
worksheet attributes or rich table ranges. Another finding required ordered
Excel/sheet-bounded range coordinates. Eleven red regressions reproduced these
gaps and the missing coordinate-only forecast selection output. The corrected
contract compares all shared legacy structural attributes and known rich
ranges, validates coordinates and retains forecast selections without resolving
whole-sheet coverage. Independent read-only re-review found no further issue.

All 107 focused tests pass at 100% line/branch coverage (198 statements,
48 branches), with Ruff and strict typing clean. A cold, unfiltered one-worker
mutation run killed all 144 mutants in 66.82 seconds: zero survivors, timeouts,
errors, pardons or cache hits. It used all 107 tests and the unchanged
30-second mutant deadline. The no-coverage mutation invocation emitted a
module-not-measured warning; separate critical coverage above passed.

Source SHA-256:
`4afc37f91a2969d7f3428dbc8c86bc957c2499b2aec4c7fa1e6343a1b12a694e`.
Test SHA-256:
`b7c5d21b5083841584097b5e1dea7f0f893295c9c3d3848f68c7c3fc210dad69`.
After the refinements, the same six-metadata pilot still reports 158 unresolved
units and 17 adapter exclusions, with receipt digest
`b1b16684838c403feb9678ad6d59eb688cffa8e0cc539220fb695d0b39823765`.
Originals and derivative data files were never opened by this pilot.
Native and hosted validation remain pending at this checkpoint.

## Complete native checkpoint

Functional commit `3564f2b` was integrated with main `6105a50` at
`c3c82b33f237e0c8c98c09ade20f891c914625ff`; no source/test changes occurred.
The required native harness exited zero: 3,531 tests in 87.68 seconds,
eight existing SQLite warnings, 97.23% overall coverage, 75 Conductor tracks,
42 schemas/32 sample documents, 9/9 differential parity, all native mutation
lanes, hygiene, audit, licences, secret scanning and validated 111-component
SBOM. CAS throughput was 330.98 MB/s. The SBOM tool's duplicate internal
validation warning does not replace its succeeding mandatory strict validator.
Only two harness-generated timestamp-only legislation receipts were restored
after completion; no source data or retained outputs changed.

Commands:

```sh
.venv/bin/pytest tests/domains/health_appropriations/test_area_accounting.py --cov=archive_govt_nz.domains.health_appropriations.area_accounting --cov-branch --cov-fail-under=100 --cov-report=term-missing -q
COVERAGE_CORE=ctrace PYTHON_JIT=0 .venv/bin/pytest tests/domains/health_appropriations/test_area_accounting.py -q --gremlins --gremlin-targets=src/archive_govt_nz/domains/health_appropriations/area_accounting.py --gremlin-report=json --gremlin-parallel --gremlin-workers=1 --gremlin-clear-cache --gremlin-no-coverage-filter --strict-pardons --gremlin-max-pardons-pct=0 --max-pardons=0 --no-cov
COVERAGE_CORE=ctrace PYTHON_JIT=0 PYTEST_XDIST_AUTO_NUM_WORKERS=4 ./scripts/validate.sh
```

Retained receipt hashes (SHA-256):

- Critical coverage: `632cd9270a4d02e306c03f88ea29eb069a482b6338ab9eb3710e42a07180853d`.
- Cold mutation: `df575e813b26d98404596796788141556989bb05501d8b6863392f099b3100d5`.
- Native log: `c4f627424ed88cbdb4617e54049d17f09b217e512003ca4e99c10d0a07dd4c99`.
- Native coverage: `a810d3f187090aac1595b6d15a769bed47de6c524a4bc7e7f0ce79c4b438c702`.

These are local software/accounting receipts. They do not establish complete
donor-area discovery, normalized coverage, source-file fixity, rights, publication
or completion of any umbrella phase. Exact-head hosted checks remain pending.

## Stacked integration checkpoint

Integrated reviewed, not-yet-merged PR #315 head
`10731ff4b37f41365eb35eeb49dd37e957c74647` (including PR #309) at merge
`5f45b3e`, preserving its complete 105-line evidence-ledger prefix and appending
the accounting receipt. Accounting production/test hashes above are unchanged.
The first focused command referenced a nonexistent forecast test filename and
exited 4 without running tests; corrected accounting/forecast-preflight selection
passed all 149 tests in 3.91 seconds, with 75 Conductor tracks and no errors.
Delivery order remains #309, #315, then #314. Hosted checks do not authorize an
out-of-order merge; ordinary merge commits preserve reviewed stack ancestry.
