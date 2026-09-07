# Phase 3.1 broad fixture task — local completion

The original task, “Add failing JSON Schema/Arrow/Parquet fixtures … versioning,
stable IDs, fixed-precision money, null reasons, units, vintages, bitemporal
fields, rights and lineage”, is locally complete. This closes that task under
M-05/M-06/M-18, with fixture evidence for AC-05/AC-16. It does not close Phase 3,
whole-track AC-05, or the full AC-16 repository checkpoint. The parent explicitly
owns integrated assurance; no full harness ran in this worktree.

This corrects the first assessment in `eight-recordset-fixture-acceptance.md`
and its historical receipt. That assessment conflated proving fixture contracts
with introducing a universal production validator and acquiring/qualifying live
sources. Those are not requirements of the quoted fixture task. The correction
does not weaken any Must: source-specific projections, normalization and
publication retain their own plan tasks and acceptance gates.

## Concrete missing assertions now implemented

`tests/schemas/test_health_recordset_linked_fixtures.py` adds 24 cases:

- A linked eight-recordset dataset uses a separately declared `source_cells`
  object as synthetic Bronze bytes. Its SHA-256, exact coordinates, raw values,
  normalized values, target IDs, lineage groups and classification references
  are checked before and after JSON Schema/Arrow/Parquet replay. All 40 declared
  field observations across the two vintages must occur exactly once.
- Nine deliberate corruptions demonstrate that the fixture oracle catches
  missing/duplicate links, bad targets/coordinates/hash/value/vintage/rights,
  and dangling classification references. This is a fixture oracle, not a
  production validator masquerading as one.
- Approved `SourceInventoryRecord` IDs are checked against their independently
  encoded hash preimage, replayed, and distinguished across vintages. The
  existing predecessor contract rejects a missing source predecessor. That
  source relationship remains in the census evidence; no new `supersedes`
  column is silently added to the immutable v1 transport schema.
- Actual Budget and historical health/GDP canonical projections cross all
  three formats, including nonempty fiscal-context facts. Every output lineage
  target resolves and matches a source object/cell/raw value. Receipt accounting
  covers every emitted link. Reordered inputs retain IDs; changed manifest pins
  produce disjoint IDs. Budget's canonical ID preimage is independently checked.
- Eight corrupted Budget/historical source-lineage inputs are rejected by the
  existing approved adapters. These test production rejection, independently
  of the test-only linked-fixture oracle.
- CPI and Pharmac adapters run against synthetic originals. Their source IDs
  are checked against independent source-coordinate hash preimages; exact
  amounts, raw amount cells, lineage IDs and original-byte fixity survive a
  test-only mapping into the generic fixture shapes and three-format replay.
  This mapping exercises supplied source IDs; it is not a production canonical
  projection or an assertion that all source-specific fields were projected.

No production behavior was missing for these assertions. All reuse existing
normalization, inventory and adapter contracts. No source, dependency or global
registry edits were necessary.

## Final requirement matrix

| Fixture dimension | Evidence |
| --- | --- |
| Eight sets and versioning | Exact eight-name fixture census; independent typed expected values for all fields; JSON constants, unknown versions, Arrow metadata and Parquet replay |
| Stable IDs | Replay/order/duplicate tests on all eight; source census preimages; actual canonical Budget/historical pin and vintage contracts; actual CPI/Pharmac source-coordinate IDs |
| Fixed-precision money | All five fact types; exact Decimal and lexical token retention, scale/overflow rejection; existing adapter boundary/property tests |
| Null reasons | All five specified categories across all five fact types; null/reason contradictions fail; CPI source missingness contracts distinguish missing from zero |
| Units | Exact NZD millions/thousands and index units through fixtures and adapters; source/lineage unit mismatch rejected by historical projection tests; unknown unit remains explicitly null |
| Vintages | Two retained observations; linked rows cannot change vintage unnoticed; adapter pin/vintage changes do not pool identities |
| Bitemporal fields | Explicit and unknown valid endpoints remain distinct from UTC observation timestamps; reversed intervals rejected; Budget unknown fiscal dates, historical end-known dates and CPI/Pharmac dates exercised |
| Rights | Unevaluated/restricted labels preserved; link rights corruption detected; approved adapter manifest/fact rights drift rejected by existing tests; no fixture grants publication approval |
| Lineage | Exact synthetic hash/cell/raw/normalized/target closure and corruption tests; actual adapter target/source-cell joins and complete receipt accounting; required absent/null lineage rejected |
| AC-16 test obligations | Fixture red before adding source cells; focused schema/adapter/property suite, lint, format, type and self-review; full repository checkpoint delegated to parent |

AC-05 says: “all required record sets validate, preserve units/vintages, and
expose field/cell lineage to Bronze.” The fixture demonstrates these properties
with synthetic Bronze and approved adapter examples; it does not require a live
rights decision. AC-16 requires full assurance “at the required checkpoints”.
This task adds tests, not critical production logic; no new critical branches
require mutation/coverage qualification. The parent must still run the full
integrated checkpoint, including existing coverage/mutation/security/supply-chain
gates. No remaining specification clause blocks fixture implementation completion.

## Validation and self-review

First linked-fixture run failed with `KeyError: source_cells` (one failed, one
passed before maxfail). After adding independent cells: 20 passed; source-adapter,
GDP and census additions subsequently reached 24 passed. All characterize
existing production behavior; no fabricated production red/green claim.
Ruff caught an unused typing import and type-only Path import; corrected.

Final focused command (673 passed):

```sh
PYTHONPATH=src /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m pytest tests/schemas/test_health_recordset_fixture_acceptance.py tests/schemas/test_health_recordset_linked_fixtures.py tests/schemas/test_health_recordset_normalization.py tests/schemas/test_health_recordset_json.py tests/schemas/test_health_recordsets.py tests/domains/health_appropriations/test_budget_projection.py tests/domains/health_appropriations/test_budget_classification.py tests/domains/health_appropriations/test_historical_projection.py tests/domains/health_appropriations/test_cpi.py tests/domains/health_appropriations/test_pharmac.py -q
```

Ruff check/format-check and basedpyright pass for both new fixture test modules;
`git diff --check` passes. Interpreter is read-only from the existing environment;
`PYTHONPATH=src` selects this isolated checkout. The parent integrates commits
separately; no concurrent full harness, push, merge or publication.

Review confirms distinct test-only fixture expansion, source adapter validation
and transport validation. The 40-cell fixture scope is explicit, not asserted
as complete original-workbook extraction (M-07). No fixtures contain restricted
or personal data. General/Python guides pass; no platform guide applies. No
remaining in-scope finding or production change. The previous permissive-transport
characterization remains useful boundary coverage, not a task-completion blocker.
