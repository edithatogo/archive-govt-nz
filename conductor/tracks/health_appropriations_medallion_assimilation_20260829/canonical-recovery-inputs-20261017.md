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
Native integrated recovery and the required full harness remain pending.

The overall Health receipt still reports partial recovery with broader source,
comparison, rights and standards gaps. This slice does not mark the track or
Phase 9 complete and does not repeat external collection/publication changes.
