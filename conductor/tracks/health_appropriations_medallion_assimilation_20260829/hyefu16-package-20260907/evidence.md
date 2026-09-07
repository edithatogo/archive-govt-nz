# HYEFU16 local persistence and verification

Base: parent G `1521071388394ad14bec9e5967e3e46e659a8ee4`.
Branch: `codex/health-hyefu16-package-20260907`, isolated worktree
`/Volumes/PortableSSD/GitHub/archive-govt-nz-health-hyefu16-package-20260907`.
Date: 2026-09-07. Conductor implement/review used; the parent assignment scoped
this worker slice to focused validation and dedicated evidence, with no umbrella
lifecycle edits. The parent owns combined full validation and delivery.

## Contract and implementation

Phase4.2/M-07, AC-03/AC-05: persist the existing hash-bound HYEFU allowance
admission, not a new source reader or whole-donor closure. The existing
`package_admitted_source(..., profile="hyefu-allowance", context=...)` API now
uses the existing admission and writer. `verify_stage_coverage` verifies the
persisted profile. No CLI or orchestration expansion is included.

Exactly Table 2.4 C6:F8 and C10:F10: 16 source observations. Preserve native
numeric tokens, number formats, labels, Budget columns, raw context and all
six native field-coordinate links per record. Typed lineage additionally
retains the writer's generic context links; 96 is the **native reference**
count, not the total physical lineage-row count. All original record fields
remain in source_record_json. Amounts remain exact Decimal values.

The adapter returns its already-computed bounded workbook inventory; there is
no second workbook semantics reader. Every worksheet receives a preserved-only
remainder, subtracting only admitted cells. This profile has no formula-total
exclusion. No other chart table or sheet is declared normalized.

Verification checks exact selected coordinates/counts, stable IDs, duplicated
source/identity fields, native lineage, fixed reviewed context anchors, unit,
label and Budget-column meanings, unknown currency, and non-annual-total period
interpretation. Existing fixity/schema/output closure, no-orphan lineage and
state-specific area/remainder contracts remain active.

## TDD and focused checks

Initial 13 tests failed because the profile was unsupported. Final new test
file has 18 cases including repinned Parquet mutations and wrong source pin,
locator/vintage, symlink and interrupted-write boundaries. Existing destination
bytes are never overwritten; failed writes have no successful MANIFEST.

Runtime: `/Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python`,
`PYTHONPATH=src`. Commands ran in the isolated worktree.

- 205 affected tests passed: test_hyefu_allowance_package.py,
  test_literal_packages.py, test_verified_coverage.py,
  test_hyefu_allowance_literals.py, test_rebuild.py and test_rebuild_eight.py.
- Scoped coverage: hyefu_allowance_literals 37 statements/4 branches;
  literal_packages 66/22; verified_coverage 125/34. All 100%, no exclusions.
- Cold unfiltered mutations on the three touched modules, first four test
  files: 175 killed, zero survivors, zero cache hits; 135 baseline tests passed.
  Options: `--gremlins --gremlin-clear-cache --gremlin-no-coverage-filter
  --gremlin-workers=4`, with comma-separated module paths in `--gremlin-targets`.
- Ruff check/format and basedpyright passed on all changed Python files,
  including replay.py. Git diff whitespace check passed.
- Self-review: existing four-stage v1 PROFILES, eight-stage v2 STAGES, resume,
  Gold and CLI source files are unchanged. No source payload or generated
  derivative is tracked. No full harness or parent edits performed.

## Actual retained replay

`replay.py` invokes existing admission/persistence/verification twice into new
exclusive directories. It independently resolves the retained workbook's XML
relationships and checks all 16 numeric tokens and absence of selected formulas;
then compares every nested admission field, exact amount and native lineage
reference. All four output files are byte-identical between builds. See
replay.json for exact hashes and external output location.

The source is donor path `data/raw/hyefu24-charts-data.xlsx`, SHA256
`f77bdab5ef808b0e451a52b9b448a52b07899bc4523da3c02aa5725325d6203c`.
Original bytes are unchanged. Replay uses the existing donor replay context
timestamp, not execution time; caller-supplied donor context is not an
independently verified HTTP observation attestation.

`$millions (average per annum)` remains literal, not annual spending or a
derived total. Currency remains null. Rights remain not_evaluated, promotion
not_performed. No repair approval, denominator decision, source rights,
publication, whole-area closure or integrated full-gate acceptance is claimed.

## Parent replay refresh after full-gate finding

The parent gate at `acf06c153c1f6900262da588c0308a57bb5dd985` passed all
6,490 tests and subsequent checks through licensing, then stopped at a secret
scanner entropy finding on the non-secret macOS temporary output path in
`replay.json`. The original recorded path was
`/var/folders/m9/_g3wndrn04d80ys2382r700r0000gn/T/health-hyefu16-_buvf5qi`.
Its original receipt remains in commit `8160cad0`; neither those builds nor any
source original was removed or changed.

The parent reran this existing replay script into a fresh `/tmp` directory:
`/tmp/health-hyefu16-review.kx0oFh`. Both new builds passed native XML/value/lineage
comparison and verification. Every output hash is identical to the first receipt;
only `replay.json`'s local output location now identifies this new verified replay.
No scanner configuration, threshold, blanket exemption or production code changed.
