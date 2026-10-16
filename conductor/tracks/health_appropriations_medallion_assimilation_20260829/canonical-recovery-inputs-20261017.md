# Fresh canonical recovery inputs and supported products

M-03, M-10, M-14, M-16, M-18; AC-02, AC-08, AC-12, AC-14, AC-16.
Related issues: #205, #215.

The canonical Gold recovery input path now rebuilds two independent sets of
historical-2024/2025, Budget-2025/2026 expenditure, and Budget-2026 revenue
packages from five pinned Bronze originals. The source definitions are locked
in `canonical_input_recovery.py`; their digest, original hashes, exact observation
tokens and expected observation IDs are retained in a payload-free completion
receipt. Retained Silver/canonical packages are not runtime inputs to this path.

Preflight checks all original hashes and exact token identities before creating
an output directory, rejects overlap/overwrite, and rechecks originals after
building. Partial attempts are retained; a failed attempt is not a completed
receipt. The new receipt schema records bounded inventories and explicit
unassessed rights/unperformed publication states.

Each Gold run receives its corresponding fresh historical/Budget, Pharmac,
MoH, BEFU and HYEFU inputs. Fiscal Crown still comes directly from its pinned
original. The recovery report compares raw/canonical inventories, verifies
bounded named queries for all eight products against typed Arrow rows and
counts, and reconstructs the composite metadata from fresh canonical and
Fiscal/Budget Gold. Metadata v4/source-reference v2 are retained; full standards
conformance and other source/rights/track gates remain unasserted.

## Observation identity and provenance deltas

The earlier preflight copied normalized manifest timestamps, which changed
source observation IDs despite equal instants. Existing source command/pilot
records and the retained IDs establish the exact original input tokens. The
locked definitions replay those tokens without changing the identity algorithm
or historical records. `canonical-recovery-preflight-20261017.json` records the
bounded comparisons: all selected values, qualifiers, lineage and dispositions
match; historical 2024 is byte-identical, and the corrected exact-token 2025
historical replay is byte-identical in both raw and canonical outputs.

Current Budget extraction also records adapter-selection evidence that older
raw manifests omit. That new provenance is retained; it must not be stripped
or described as a source-value change to force older manifest hashes. This
metadata distinction is separate from the 30 source-backed donor retain-both
dispositions. No original, historical receipt, value or publication is replaced.
The preflight used retained context to diagnose the issue; it does not by itself
constitute the new independent runtime recovery contract.

## Verification

Twenty focused recovery tests pass, including changed/missing originals,
wrong timestamp-token identity, exclusive repeat outputs, interruption evidence,
correct second-run domain bindings, damaged Gold rejection, all eight query
readbacks and 13-recordset composite metadata reconstruction. Lint and focused
typing pass. The new machine receipt has a schema and representative fixture.
The integrated native run on implementation commit
`a8b8fcea74a8889c90fb68ddabf0012a68489f49` exited successfully. Both fresh
five-source input trees match all 47 files (46 raw/canonical files plus their
completion receipt); both Gold trees match 53 files. All eight named queries
repeat identically and return 645 exact typed rows from 800 product rows, with
explicit 200-row truncation for historical and Budget products. All 859 input
records have products and zero are unaccounted. Composite metadata v4 repeats
nine files across three packages, 13 recordsets and 1,184 rows. The full run
verifies Bronze objects unchanged. See
`canonical-recovery-validation-20261017.json` for pins and bounded inventories.

Validating the actual input receipts caught a new-schema filename omission:
Budget canonical outputs include `lineage_accounting.jsonl`, whereas the draft
inventory pattern allowed only JSON and Parquet. A native-shaped fixture first
reproduced the rejection, then the schema was corrected to include JSONL. Both
saved actual receipts validate with the correction and are byte-identical
(`db17e436e6a25ad3d48824642753cfe8342585e9e1dbe689cf0d49f0a6f4f371`).
Production implementation, inputs and output hashes remain unchanged; this
schema/test/fixture/documentation delta does not require repeating the native
rebuild. The focused recovery suite still passes. The full `./scripts/validate.sh`
harness passed on clean `7946b24392d1053b76d3ef77cbc49263a08b3f23`:
7,708 tests passed, ten skipped, 97.44% coverage against the agreed 80% floor;
60 schemas/50 representative documents, parity, all mutation lanes, hygiene,
audit, licences, secrets and SBOM gates passed. The SBOM contains 113 components;
external CDX validator execution was explicitly skipped, so no separate external
standards-validator success is claimed. This subsequent bookkeeping changes only
track documentation/evidence. Protected hosted delivery remains pending.

The overall Health receipt still reports partial recovery with broader source,
comparison, rights and standards gaps. This slice does not mark the track or
Phase 9 complete and does not repeat external collection/publication changes.

## PR #691 review correction in progress

The first native query receipt proves membership/count/repeat behavior but its
Counter subset oracle did not prove the exact ordered first-200 slice. The
original receipt is retained unchanged with this qualification. The corrected
oracle sorts typed table rows independently in physical column order, ASC NULLS
LAST, and compares the complete expected slice. Negative subset/reversed-order
fixtures reproduce the old gap; explicit numeric/null/list/duplicate fixtures
exercise ordering semantics. Targeted fresh native proof and updated full/hosted
validation are pending. No source values or producer outputs are changed.
