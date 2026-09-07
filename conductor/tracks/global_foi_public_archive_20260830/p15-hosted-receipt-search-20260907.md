# P1.5 hosted receipt recovery — 2026-09-07

**Neither outstanding P1.5 proof gap is closed.** This read-only search recovered
useful fresh evidence: all nine post-repair sync artifacts remain available,
including September 5 and 6 runs newer than the earlier retained readback.
Every changes ledger has empty added/updated/removed arrays. Eight summaries
report verified=true; the first diagnostic run has verified=null and zero records.
No report field is upgraded into independent public restoration evidence.

The [machine receipt](p15-hosted-receipt-search-20260907.json) pins every selected
run/head, artifact ID/ZIP SHA-256, summary/change/execution-receipt digest and
source blob. Each execution receipt matches its run, head and summary digest;
each changes timestamp matches the corresponding summary. All downloaded ZIP
hashes match the GitHub artifact API digest.

## Post-repair sync artifacts

| Run | Head | Artifact | Added / updated / removed |
| --- | --- | --- | --- |
| 34047241453 | 7793293e488bd39d3fbb1e36ceb98820beb40313 | 9993472082 | 0 / 0 / 0 |
| 33979018048 | 7793293e488bd39d3fbb1e36ceb98820beb40313 | 9973183647 | 0 / 0 / 0 |
| 33901357761 | 7793293e488bd39d3fbb1e36ceb98820beb40313 | 9947761049 | 0 / 0 / 0 |
| 33786880797 | 7793293e488bd39d3fbb1e36ceb98820beb40313 | 9905763070 | 0 / 0 / 0 |
| 33663819472 | 7793293e488bd39d3fbb1e36ceb98820beb40313 | 9859749545 | 0 / 0 / 0 |
| 33539917839 | 7793293e488bd39d3fbb1e36ceb98820beb40313 | 9813174624 | 0 / 0 / 0 |
| 33433808727 | 7793293e488bd39d3fbb1e36ceb98820beb40313 | 9773623578 | 0 / 0 / 0 |
| 33326963683 | be992fe036d5a270e228b5277e5b5770b9950ad8 | 9736507335 | 0 / 0 / 0 |
| 33306106031 | b6e78703d871082433fb33f8fa610761c2eb4062 | 9730512147 | 0 / 0 / 0 |

Exact source at all three executed heads has SHA-256
`a08c69da972959763a7bc39c376b92fb69dc82a8a376c556bcd371b9d0398298`
(Git blob `7c3dd546cf4478577cf46e9d400ae6f23f8f5726`).
`changes_have_records` checks whether any of the three buckets is nonempty;
`run_sync` gates changed publication on that result (lines 364/368).
Thus the empty ledgers do not establish execution of the changed-sync branch.
Manifest digests differ across some dates, but this alone cannot establish
changed-record publication: unchanged sync can restore a different prior manifest.

## Historical no-skipped-work gap

- Run **33305989413**, head `b6e78703d871082433fb33f8fa610761c2eb4062`,
  artifact **9730497676**, covers start 17225 / batch size 1.
  ZIP SHA-256:
  `67bb806bd47854b9ae6af4357f9ec6206baa0c52a1f9633bdc493579db9b17f2`.
  Its fourteen members contain no raw-package manifest or raw-prefix members.
  The batch evidence lacks a raw-package digest. This is the existing
  17225–17226 retention gap, not a newly recovered original.
- Failed run **33307488567**, head
  `676461907887ace3f3a42a270b0b05ad0ed29ec6`, currently has **zero artifacts**.
- Latest listed backfill run **33307777685**, head
  `be992fe036d5a270e228b5277e5b5770b9950ad8`, artifact **9731030582**,
  remains the later 17226–17227 batch. ZIP SHA-256
  `c4404a60ef239274b1a6973be13ab2b07bad24e85fbd734af8c7f457868b9946`
  matches the earlier retained readback. Its raw inventory names seven files /
  49,405 bytes, with temporary-artifact storage and public verification false.
  The later range does not repair the preceding missing-originals range.

The monitor was observed disabled_manually (workflow 322525555). No workflow
or schedule was changed. Existing recovery-workflow runs remain dated August 30;
their success does not supply the absent raw batch.

## Exact remaining inputs

1. An existing hosted changed-sync run with nonempty changes, a source-bound
   execution/summary receipt at the repaired head, and matching immutable public
   manifest/card evidence. None was found in the bounded post-repair search.
2. Existing original-object retention evidence for 17225–17226 plus historical
   source-bound coverage reconciliation. Contiguous queue ranges are not raw
   retention proof. This search does not prove no copy exists elsewhere.

Neither gap can be closed by an owner rights decision alone. New publication or
capture is outside this request and cannot fabricate historical proof.

## Search and verification boundary

Read-only commands used `gh run list` (30 latest runs per named sync/backfill
workflow), `gh api .../actions/runs/RUN/artifacts`,
`gh api .../actions/artifacts/ID/zip`, and exact-ref Contents reads for sync.py.
The machine receipt retains both thirty-run listings. Nine sync ZIPs were checked
with two workers, 45-second command limits and a 180-second cohort-start guard;
advertised and received ZIP size was limited to 12 MB. Selected JSON members were
limited to 64 KiB and declared expanded archive size to 128 MB. The three selected
backfill artifact listings used 30-second limits, ZIPs below 1 MB and declared
expanded size below 2 MB. No archives were extracted or raw bodies committed.
Preliminary metadata/duplicate reads are not an exhaustive archive census.

Receipt invariants and the Conductor hash chain were checked offline. Conductor
implement/review guided this evidence-only update; no production code, plan
completion, global registry, publication gate or parent frozen tree was changed.
No full harness was run. P1.5 remains pending; parent owns lifecycle acceptance.
