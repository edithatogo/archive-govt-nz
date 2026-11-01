# Autonomous continuation route

This is a routing guide for the approved plan, not a replacement task registry
or new publication authority. Use `plan.md`, requirements and acceptance
criteria as the source of truth. Status is `in_progress`.

## Substantial milestones

1. **Finish characterization and reconcile evidence (Phases 1–2).** Map existing
   code/tests/receipts to unchecked tasks before rebuilding anything. Finish
   donor-script failure characterization and source-family/disposition coverage.
   Reconcile each phase issue individually; publication does not close them.
2. **Rebuild from originals (Phases 3–4).** Add source-specific workbook/PDF/CSV
   adapters with exact sheet/cell lineage, units, vintages and reason-coded
   exclusions. Current `normalize_donor_sqlite` preserves a donor derivative;
   it is not proof of raw-workbook extraction. Compare regenerated facts with
   the five-table/312-row oracle and record every justified difference.
3. **Normalize approved expansion (Phase 5).** Process Vote Health, Budget,
   BEFU/HYEFU, fiscal-history, Ministry and CPB sources plus exact contextual
   series. Retain originals, gaps and revisions; never splice incompatible
   periods, classifications or denominators silently.
4. **Complete derived products (Phases 6–7).** Build defensible nominal, real,
   per-capita and share measures with denominator provenance, then metadata,
   source-quality summaries and versioned federation mappings.
5. **Complete operation and recovery (Phases 8–9).** Exercise capture through
   inspection, normalization, reconciliation and clean-room rebuild using typed
   CLI/read-only MCP, resumable scheduling, failure receipts and original-byte
   fixity checks. Package a new candidate only after acceptance checks pass.
6. **Respect external gates (Phase 10).** Present any changed candidate's exact
   manifest and rights evidence for publication approval. Existing candidate
   approval does not cover new bytes. Verify remote bytes and collection state
   after an authorized upload. Donor retirement and Zenodo remain out of scope.

Optional survey linkage and graph/vector work must not delay Must requirements.
No task is complete just because code exists, an issue is closed, or CI is green.

## Execution loop

- [Remaining acceptance route](./remaining-acceptance.md) separates established
  preservation/raw replay from pending canonical consumers, metadata composition,
  exclusive resume execution and publication gates. Check newer evidence before
  repeating bounded helpers already delivered.

- Use `source-schema-gaps.md` for the reconciled remaining source/canonical
  route and `preservation-recheck.md` for the latest independent local
  CAS/WARC/candidate audit. Consult newer appended receipts and live PR state
  before deciding which active stream needs implementation versus delivery.
  The historical notes below record prior increments, not an instruction to
  repeat an already-merged task.
- `originals-product-replay.md` records two byte-identical fresh four-profile
  original-to-SQLite/Gold/plot replays and a separately diagnosed SQLite writer
  version difference against older artifacts. Do not repeat this as missing
  component work or call it complete Platinum/interruption recovery.
- Current raw-source increment: the Budget adapter extracts 215 Health facts
  directly from the pinned original, preserving 3,655 cell-lineage rows and
  all 6,504 input dispositions. Keep these outputs separate from the published
  SQLite-derived products. See `raw-budget.md` and the current evidence.
- BEFU/HYEFU literal summaries now reconcile all 20 oracle rows from originals,
  with 120 field-lineage records and 4,665 cell dispositions. See
  `raw-forecast.md`; these are separate local derivatives, not HF updates.
- Historical Health/GDP now retains 106 original observations, including 29
  annotated years absent from the donor and one exact-token precision
  difference. See `raw-historical.md`; no original or HF bytes changed.
- Original-workbook orchestration now rebuilds all four adapters into a
  separate verified 341-fact local run. Complete reuse checks every stage;
  incomplete attempts are retained and require a new output directory.
- Pure read-only raw-run verification now has matching CLI/MCP receipts and
  cannot create missing state. Typed workbook inspection now replaces donor
  sheet listing/head printing with bounded structured previews (Phase 4.3).
  The pure five-table projection is validated locally (`42cee7d`): all 341
  facts retained, 15 decimal-to-binary representation differences flagged.
  Persistent export now has capped verified snapshots, exclusive SQLite output,
  exact-value/context and lineage sidecars, plus a completion manifest. Live
  independent builds match and retain all donor rows plus 29 historical facts.
  Pure historical and Budget analytical computations now have explicit
  period/basis/gap/denominator guards and exact source-vintage aggregates.
  See `raw-analytics.md`. The shared verified reader and exclusive Gold
  tables/manifest/CLI now have live independent rebuild and legacy comparison
  evidence in `raw-gold.md`. Gold PR #261 merged after seven exact-head checks
  passed; whole-suite local timing failures remain recorded. Six source-derived
  plots now have pure contracts, a pinned Gold reader, typed CLI, independent
  byte-identical builds and visual QA corrections. See `raw-plots.md`.
  Final local plot assurance passes (1,906 tests, 128 current mutant kills).
  Donor failure characterization and four-profile raw-pipeline conformance now
  pass 253 focused and 1,907 full-suite tests (`4454d75`).
  Plot PR #269 is merged after seven exact-head checks. Next: finish
  exact-head hosted conformance delivery, then successor
  Budget normalization and remaining source-area/contextual coverage.
  A fresh read of the canonical historical facts identifies period/basis
  transitions at 1990, 1994, 1997 and 2005, with no year gaps. Growth across
  those transitions must remain explicitly unavailable or separately qualified;
  matching year labels alone do not establish comparability.
  Continue partial-stage resume/scheduling and remaining
  workbook areas and official/contextual sources. Published state stays separate.
- Resume this exact track, inspect dirty work and live PR state, then choose the
  next unblocked task. Do not restart completed preservation or publication.
- Work through the red/green, review, evidence and exact-head CI/merge cycle.
  Continue to the next task rather than treating every PR as a user handoff.
- Run coverage-producing commands sequentially or with separate coverage stores.
  Do not edit code under a baseline test run. Keep CI validation authoritative.
- Record remaining acceptance criteria and the next executable action in the
  track receipts so another execution can resume without a new scope prompt.
- On a gate, record the exact blocked branch and continue independent approved
  work. Ask only for a necessary credential, rights/scope decision, publication
  approval or destructive authority. Never weaken Must requirements to finish.

## Unattended continuation

Repository policy grants implementation authority; it does not itself wake an
idle Codex task. A thread heartbeat can resume this loop after a response ends.
An hourly cadence is a proposed default, subject to one-time activation in the
app. Use one continuation stream, inspect existing automations first, and avoid
duplicate runs or overlapping worktrees. Follow current app availability and
usage limits; scheduled execution is not a guarantee of uninterrupted work.

This file does not create or enable an automation. A future heartbeat should
use the route above, reconcile receipts on every run, report meaningful progress
or actionable blockers, and pause when all approved work is genuinely complete
or only explicit human/external gates remain.
