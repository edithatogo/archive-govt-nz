# Crown independent receipt/CAS join — finding 1 only

Base `1f541c107eb1693fcb41f4aa19da7a883526c5cc`; isolated branch
`codex/health-crown-receipt-binding-20260907`. No verified_coverage, Popper tests,
shared lifecycle, original source, capture receipt or v1 registry changes.

## Contract

Eight-stage planning now requires `crown_receipt: Path` and
`crown_receipt_sha256: str` keyword arguments as well as the explicit Crown
object hash. The CLI requires `--crown-receipt` and `--crown-receipt-sha256`
alongside `--eight-stage --crown-source-sha256`. Default dry-run and four-stage
v1 remain unchanged; stray Crown receipt options in v1 fail rather than being
ignored. Earlier unbound v2 plans are not silently accepted or migrated.

The new parser takes a capped 1 MiB snapshot, rejects symlink receipt paths and
duplicate JSON members, checks exact digest/schema/count, and requires exactly
one matching object/URL/source-ID candidate. That row must agree on all three
identities, captured disposition, fiscal family and exact 1972–2025 title.
The fixed title/family/URL selects the existing Fiscal-Time-Series-1972-2025
vintage: the census has no literal `source_vintage` field, and none is invented.

The time is read from that row and must agree with the already supported Crown
admission observation. It is not replaced by run time or a code-only default.
An incompatible observation fails before output creation instead of being
silently coerced by the unchanged admission adapter. The receipt's timestamp
spelling survives in the plan/source context, and the existing Crown package's
observation time/ID remain byte-identical. This is a fixed historical profile,
not a generic mechanism for relabelling the same workbook with arbitrary times.

Exact UTF-8 receipt bytes and the independent SHA-256 are embedded in PLAN.json.
Execution and completed-run verification reparse and rejoin those bytes to the
selected source and freshly verified CAS object. Complete verification remains
portable without requiring the original receipt path to exist. The receipt
path is an explicit input, not a machine-specific dependency saved into PLAN.

## Actual evidence and limitations

The independently pinned retained receipt is existing `source-census.json`:
`4bea6001b0a1af4a362075508c521befe5bd6e04d20b2dd2f7c23ef8c6256964`.
It records observation `2026-08-29T09:00:17Z`, source `fiscal_time_series-007`,
and Crown object
`de59f9028a81a697ee66eea04861edfd8e2c3a7e472b3b8798d976951964f70f`.

This is **retained census observation/CAS consistency**, not independent HTTP
capture-time attestation, authentication, rights approval or WARC verification.
The older official-capture manifests do not contain an observation timestamp;
they were not rewritten, embellished or substituted as timestamp evidence.
The parser does not claim verification of all census rows or all donor objects.

Two actual retained-source builds under `/tmp/health-crown-receipt-replay.iNn9fa`
are byte-identical across 34 files, with 215/10/10/106 legacy facts and
69/80/80/61 additional observations. All 32 stage files match the preceding
orchestration replay; only the plan and its completion binding change.
Completion SHA-256:
`f0b0b08790f52caed502efac23de5967718446fec30f007e7d30a67d4f805d97`.
Every file hash and exact input pins are retained in `replay-result.json`.
The real CLI default dry-run matches the API plan and creates no output root.

## Focused verification

Tests first: new parser collection failed before implementation; existing
orchestration tests with required receipt inputs then produced 11 failures and
3 passes. First green: 29 passed. Expanded focused suite: **197 passed in 3.57s**,
parser 31/31 statements and 2/2 branches, orchestrator 104/104 statements and
22/22 branches, all 100%. No threshold/exclusion/assertion weakening.

Fault cases include stale/re-pinned receipts, missing/duplicate selection,
object/URL/vintage-title/family/state/time mismatches, malformed counts and rows,
duplicate JSON keys, input caps, symlinks and incomplete CLI argument pairs.
Execution negatives assert no output directory exists. Existing transaction,
partial preservation, source join, default-v1 and read-only tests remain active.

Initial static findings (formatting, import/annotation issues and test kwargs
typing) were corrected. Final Ruff check/format and BasedPyright passed on the
three changed/new production files, two owned tests and replay recipe.
Full harness and new mutation run were not performed; parent owns integration
and full gates, Banach owns independent review. Findings 2/3 are deliberately
outside this commit and this base retains their pre-fix verifier.

## Reproduce

Use the existing locked environment (this run: sibling health-foi `.venv`,
Python 3.14.6), with `PYTHONPATH=src` from this checkout.

```sh
python -m pytest -q \
  tests/domains/health_appropriations/test_crown_receipt.py \
  tests/domains/health_appropriations/test_rebuild_eight.py \
  tests/domains/health_appropriations/test_rebuild.py \
  tests/domains/health_appropriations/test_rebuild_resume.py \
  tests/domains/health_appropriations/test_rebuild_completion.py \
  --cov=archive_govt_nz.domains.health_appropriations.crown_receipt \
  --cov=archive_govt_nz.domains.health_appropriations.rebuild_eight \
  --cov-branch --cov-report=term-missing
python evidence/assurance/health-crown-receipt-20260907/replay.py \
  /Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations \
  /tmp/NEW-EXCLUSIVE-CROWN-REPLAY \
  conductor/tracks/health_appropriations_medallion_assimilation_20260829/source-census.json
```

Choose a fresh replay destination; existing/partial outputs are never replaced.
The previous eight-stage replay recipe is preserved as historical commit-specific
evidence; use this new recipe for the now-required receipt arguments.
