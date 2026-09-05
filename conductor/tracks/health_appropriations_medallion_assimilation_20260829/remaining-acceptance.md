# Remaining acceptance route after archival replay

This is a bounded checkpoint, not a new acceptance registry or approval. Read
`spec.md`, `requirements.md`, `plan.md` and subsequent appended evidence first.
The track remains `in_progress`. A merged helper is not whole-phase completion.

## What the latest evidence establishes

The independent preservation audit rehashed all 23 donor CAS objects, all 73
official-capture CAS objects and their WARC response payloads, and the 94 files
listed by the existing v4 candidate. The donor Git blob/tree reconstruction
matched its pinned tree. These overlapping inventories are not additive unique
bytes, and local fixity does not establish redistribution rights or remote
publication state. See `preservation-recheck.md`.

Two new empty-directory replays rebuilt 341 raw facts from the four selected
donor originals, then compatibility SQLite, Gold tables and six plots. All 38
files were byte-identical between those two runs. Comparison with older retained
artifacts isolated a SQLite writer-version header difference; schemas, all rows
and integrity checks agreed. No existing bytes were patched or replaced. This
replay did not produce Platinum or prove interruption recovery. See
`originals-product-replay.md` for exact pins and limitations.

The subsequent controlled-interruption pilot did prove its narrower recovery
case: two verified stages reused, two stages re-extracted, two byte-identical
fresh envelopes and all 18 raw files matching the uninterrupted baseline. All
23 originals and the failed attempt remained unchanged. This is not power-loss
or hostile-filesystem recovery. Separately, two four-package raw-to-canonical
and local-inventory replays matched all retained canonical bytes; no standards
processor or publication was invoked. See `resume-execution.md` and the local
provenance reader receipt for exact scope; hosted delivery is recorded separately.

## Acceptance boundaries and next executable work

| Criterion | Evidence already available | Remaining boundary / next action |
| --- | --- | --- |
| AC-01 donor preservation | 23 original CAS objects and pinned Git tree independently reverified | Keep the separately recorded archive digest and snapshot evidence joined; do not describe a tree reconstruction as full Git-history reconstruction. |
| AC-02 no original loss | CAS/WARC/candidate audit; new outputs remain separate | Continue exact per-item disposition accounting as new resources or versions are admitted. |
| AC-03 census | Complete donor inventory and explicit unresolved-area accounting | Resolve or reason-code the 158 structural units; a PDF structural unit is not proof of table/page extraction. Adapter-specific exclusions are not global irrelevance decisions. |
| AC-04 provenance/fixity | Source-specific manifests and cell lineage; local fixity readers | Complete resource-specific rights and observation joins across new derivatives; do not upgrade a pure metadata assertion to verified bytes. |
| AC-05 Silver | Canonical structural schemas, historical projection/export, Budget appropriation projection (#322), exclusive deterministic local Budget export, and unmapped label occurrences | Add remaining source-native-to-canonical adapters, preserving exact period/unit/Decimal semantics. |
| AC-06 donor database parity | Five-table compatibility and documented additional historical observations/precision differences | Keep row-level difference receipts attached; neither total-row equality nor a successful export proves all semantic repair approvals. |
| AC-07 functional parity | Inspection, source processing, analytical/plot contracts and original-driven replay | Reconcile full donor utility/analysis scope against fixtures; do not treat unnormalized workbook areas as covered by six plots. |
| AC-08 rebuildable compatibility | Verified raw-Parquet-to-SQLite/Gold/plots pipeline plus verified canonical Budget aggregation and historical identity queries with exact input-ID closure | Extend the canonical-recordset consumer bridge to contextual/derived measures and downstream SQLite/plots/reports; these nominal queries do not complete the full bridge. |
| AC-09 longitudinal coverage | Bounded successor Budget/forecast/fiscal and contextual source profiles | Enumerate all target editions/source families with explicit unavailable/restricted/superseded dispositions; no silent backfill or cross-vintage pooling. |
| AC-10 contextual measures | Guarded source-specific analytical inputs | Exact population denominator and reviewed Crown expense cells remain unresolved; CPI basis and other unknown semantics must stay unknown. No inferred per-capita/Crown-share values. |
| AC-11 quality | Deterministic source/lineage/count/layout and analytical guards | Compose coverage, cross-source variance and classification-drift reports without treating unmapped labels as authoritative mappings. |
| AC-12 recovery | Two original-to-raw/SQLite/Gold/plot builds plus retained controlled-interruption/exclusive-resume pilot | Compose canonical consumers and validated Platinum output into the same clean-room recovery chain. The bounded raw resume pilot does not close the full criterion. |
| AC-13 operability | Typed source CLI and forced-read-only MCP for eight explicit profiles | Wire reviewed recovery APIs into typed operations, then bounded scheduling/failure evidence; configured schedules are not observed successful captures. |
| AC-14 Platinum | Pure inventory, scoped pinned-package verifier/replay and bounded asserted PROV entity projection | Extend package coverage, compose observed fixity separately from assertions, then validate DCAT/Croissant/RO-Crate/PROV projections with explicit mandatory inputs. No full standards completion is claimed. |
| AC-15 publication | Historical v4 publication evidence remains distinct | Any changed candidate needs its own exact manifest, rights join and approval before upload, then independent remote readback/collection verification. No current execution HF claim. |
| AC-16 assurance | Per-slice focused/mutation/native and exact-head hosted receipts | Repeat appropriate gates for changed code and distinguish pre-integration local validation from final hosted head; retain failures and scope limits. |

## Continue without repeated scope requests

1. Complete exact-head hosted delivery of the provenance reader and bounded PROV
   projection; keep their already-passed local/pilot evidence distinct. Executor
   #323 merged as `1edd022c6cb0233a7807ebddd46c8b6d3fbf7394` at
   2026-08-31T18:17:38Z after seven successful checks at `f866da40`.
2. Complete the canonical consumer/metadata/recovery bridge before considering a
   changed candidate. Keep contextual sources with unresolved identity, access,
   units or rights out of analytical promotion while working other sources.
3. Reconcile the remaining criteria against exact evidence before opening a
   publication gate. The existing candidate approval covers only its existing
   bytes. Donor retirement and Zenodo remain outside this approved track.

The population original has already been requested; do not repeatedly request
it or retry a restricted route. A missing configured spreadsheet runtime affects
the separately proposed exact-cell Crown inspection, not already-tested source
adapters or metadata-only work. Preserve each blocked branch and continue other
approved work. No automation is activated by this document.
