# Election Explorer — decision-question coverage and evidence gates

**Selected 18 November 2026; planned scope, not an implemented product.** Parent:
[NZ Election Explorer programme](index.md). Read with the [existing release
requirements](requirements.md), the [data-maximisation question matrix in draft
PR #868](https://github.com/edithatogo/archive-govt-nz/pull/868), and the
[sole integration queue #867](https://github.com/edithatogo/archive-govt-nz/issues/867).
This document is the **question-led delivery crosswalk**, not a second ETL, a
second PR coordinator, or a replacement for outcome IDs O01–O15. The latter are
proposed on #868 and have **not been merged into main**.

## Current baseline and authority (inspected 18 November 2026)

- `main` is `cf64faca56eb50db14b97f534def3a17a89555f9`.
  The earlier source-driven result repair **PR #861 is merged**, but the
  existing publicly served Hugging Face Space still reflects an older,
  experimental page. **Merged source, published source and served parity are
  three distinct states.**
- [PR #880](https://github.com/edithatogo/archive-govt-nz/pull/880)
  proposes a provisional-results landing page plus a zero-based 1996–2026
  overhang series: **66 focused election tests passed**, but full Linux,
  macOS and Windows assurances failed. Do not call this live or merge-ready.
  Its 2023 +2 overhang and later Port Waikato by-election distinction must
  be preserved. Source-linked historical years lacking verified captured
  bytes/hashes remain *unqualified*, not "source-verified".
- [PR #866](https://github.com/edithatogo/archive-govt-nz/pull/866)
  addresses six pre-existing Ruff defects but includes **held Parliament
  runtime and Tobac provenance changes**. Do not merge/cherry-pick unqualified
  held changes, or duplicate the reserved repair lane. Keep exact local
  CPython **3.15.1** and current validation gates.
- [PR #868](https://github.com/edithatogo/archive-govt-nz/pull/868)
  is a **draft planning-only** subprogramme. SOC01–SOC06 are separately
  stacked draft candidates [#872](https://github.com/edithatogo/archive-govt-nz/pull/872)–[#877](https://github.com/edithatogo/archive-govt-nz/pull/877),
  not source/rights/CI-qualified production. The sole coordinator #867
  controls serial admission and existing shared election/Conductor ownership;
  no automatic PR merges or source/workflow activations follow from this plan.
- The **7 November 2026** general-election preliminary source is a distinct
  vintage. An anticipated **27 November 2026** official release is a
  *dependency*, not a present data asset. Modelled probabilities, campaign
  spending and social-demographic claims require independent qualification.

## Question-to-product backlog

`EQ` identifies the *reader's question* without renumbering or claiming
completion of the proposed `O01–O15` outcome IDs. Priority orders delivery,
not evidence strength. `Now` means a deterministic implementation can be
developed against the 7 November pinned provisional **fixture**, *after*
release/source verification; it does not mean already deployed.

| EQ | Priority and reader question | Existing outcome(s) | Existing owner track | Earliest evidence / admission |
| --- | --- | --- | --- | --- |
| EQ01 | **P0** Which party combinations reach a majority; which are minimal winning or pivotal? | O01, O04 | 02 + 04 | Now; exact vintage seat table, majority threshold, exhaustive combination oracle; political compatibility separately sourced |
| EQ02 | **P0** How many party votes or electorate changes would alter the next list seat or eligibility threshold? | O04 (+ new sensitivity view) | 02 | Now; statutory Sainte-Laguë, 5%/electorate qualification, integer tie handling, vote conservation and scenarios |
| EQ03 | **P0** Why did overhang arise, by party, and how exceptional is it over 11 MMP elections? | O04 (+ overhang detail) | 01 + 02 + 03 | Now; party entitlements vs electorate seats, overhang and House waterfall; historical capture qualification and by-election separation |
| EQ04 | **P0** Which electorate margins are narrowest and how many candidate votes could reverse a seat? | O02 (+ margins view) | 02 + 03 | Now; authoritative same-vintage candidate/electorate totals and two-candidate margin definitions; no fabricated flip probability |
| EQ05 | **P0** Under which **conditional** special-vote allocations could the coalition majority or overhang change? | O01, O02 | 02 + 04 | Now as bounded scenarios; coherent party/electorate vote allocation, fixed random seed if used; probabilities only after independent calibration |
| EQ06 | **P0** Who is over-/under-represented by party vote versus seats? | O04 | 02 + 03 | Now; all valid party votes including zero-seat parties, correct house-size denominator, Gallagher/Loosemore–Hanby independent oracle |
| EQ07 | **P0, release-dependent** What changed from preliminary to official results, and did coalition/overhang conclusions change? | O02 | 01 + 04 + 05 | Official count once published/captured/verified; immutable side-by-side snapshots, per-party/per-electorate deltas, reconciliation |
| EQ08 | **P1** Where was the largest swing or party fragmentation since 2023? | O03, O04 | 03 | Historical electorate/voting-place captures, party aliases, geography crosswalk, comparable totals and boundaries |
| EQ09 | **P1** Where did candidate and party votes diverge, and how did that relate to electorate seats? | O04, O05 | 03 + 06 | Paired candidate/party aggregate facts, same roll/vintage/geography; cannot infer individual split-ticket choices |
| EQ10 | **P1** Who enrolled/voted less, by age, area and roll, and what changed over time? | O03, O05 | 03 + 06; proposed SOC01–06 | Enrolled-eligible population and voting denominators by date/universe; coverage, suppressed cells, age standardisation where justified |
| EQ11 | **P1** How did advance-voting totals and party shares differ from election-day voting? | O02, O03 | 03 | Verified mode-of-vote counts, mutually exclusive denominators, reporting cutoffs; do not call composition differences causal |
| EQ12 | **P1** How have Māori-roll enrolment, Māori electorates and representation changed? | O05 | 03 + 06 | Official public aggregate roll/seat records and boundary versions; no inference of a person's ethnicity or vote |
| EQ13 | **P1, official-dependent** How accurate were polls and prior special-vote forecasts? | O12 | 04 + 06 | Frozen timestamped predictions, fieldwork dates, methodology and official outcomes; backtesting and proper scoring |
| EQ14 | **P2** How would alternative MMP thresholds, coat-tail rules or compensatory overhang change seats? | O04 (+ scenario lab) | 02 | Statutory baseline plus explicitly hypothetical rules; independent fixture and counterfactual semantics |
| EQ15 | **P2** How do documented financing, advertising and campaigning costs compare per vote, seat and year? | O06–O08 | 06; proposed finance work in #868 | Audited filed return/advertising coverage and CPI; no fabricated 2026 completed expenditure, anonymous tail or donor-policy causality |
| EQ16 | **P2** Which promises entered coalition agreements, legislation, budgets and delivery outcomes? | O09, O11, O15 | 06 + 05 | Dated, human-reviewed manifestos, public agreements, acts and appropriations; descriptive trace not automatic impact attribution |
| EQ17 | **P2** How do economic/housing/health measures correlate with regional voting patterns? | O10 | 03 + 06; proposed SOC01–06 | Period- and boundary-aligned public aggregates; ecological descriptive associations only until a credible causal design is independently qualified |
| EQ18 | **P2/conditional** Can verified donor organisation identities also be found in public interests or procurement records? | O13 | 06 | Reviewed legal-entity matching, public-record rights, time bounds, privacy and false-positive audits; **no suspicion/risk scoring** |
| EQ19 | **P2/conditional** How does local-government participation compare with general elections? | O14 | 03 | DIA source identity, system-specific eligible denominators and election rules; never equate FPP/STV local ballots with MMP party votes |

## Release sequence and finite acceptance

**G0 — restore trusted results before expansion (Must; 01/05/07).**
Reconcile #866 source/preservation holds without duplicating ownership; confirm
exact-head green full harness before merge of #880 or another public-source
repair. Source-to-Gold-to-static fixture parity, exact HF served SHA/readback,
rollback and last-good behaviour must be verified before calling the public
result authoritative. Dates/hashes must reflect source published, captured,
validated, generated and served states separately. No old synthetic page
published as a preliminary result.

**G1 — deterministic public analyses against a pinned *preliminary* baseline
(Must for the selected reader answers; 02/03/04).** Batch EQ01–06 in this
order: (a) statutory seat/overhang and party-vote parity; (b) minimal winning
coalition enumerator, no political-feasibility claims; (c) quotient/threshold
sensitivity and smallest vote changes with vote conservation; (d) narrow
candidate margins; (e) counterfactual special-vote *bounds*, not predictive
odds; (f) disproportionality. Validate with independent statutory fixtures,
ties, no negative votes, zero-seat parties and exhaustive small-space oracles.
No new analytics belong in verified-results panes before source and publication
qualification.

**G2 — official-count reconciliation (date-gated; 01/04/05).** Do not treat the
expected 27 November release as completed. On verified official capture,
build a *new* immutable release and answer EQ07: changed seats, parties,
thresholds, electorates, overhang and coalition arithmetic; retain the
7 November preliminary revision unchanged. Recompute dependent Gold artifacts
atomically and publish only with independent source/head/served parity.

**G3 — spatial and participation intelligence (Should; 03/06).** EQ08–12,
including 2017/2020/2023 harmonisation and age/roll denominators; integrate
only separately admitted SOC source outputs and do not claim SOC draft PR
completion. Preserve boundary vintage, missingness, uncertain crosswalks,
privacy suppression and the difference between aggregate association and
individual motivation. Use a validated voting-place and electorate map, and
accessible tabular comparisons.

**G4 — contingent research (Should/Could; 02/04/06).** EQ13–19 require
relevant official outcomes, independently filed finance/policy data or
calibrated models. Source/rights and model-specific acceptance precede
publication. Inference must provide pre-specified estimand, falsification,
uncertainty and external replication; otherwise label `research_only`,
`source_pending` or `not_estimated`.

**G5 — publication and usability (Must for every admitted question; 05/07).**
Each answer needs an `ElectionAnalyticalResult` / `QuestionEvidenceReceipt`
(or existing equivalent, not a second result registry), statement of grain,
denominator, versioned source URI/hash/rights, transformed code SHA, scenario
assumptions, result kind, coverage, independent arithmetic checks, citations,
uncertainty where appropriate, exact-head CI, served HF SHA and rollback.
When source hashes are absent, **display the gap**, not a verified badge.
Provide both accessible chart and data table/download; browser keyboard/mobile
checks, source provenance and downstream title/caption parity are necessary.
Source-linked but unverified research belongs behind research-only status, not
a verified result headline.

## Handoff and integration discipline

- Existing **01–08 tracks are the implementation owners**; this file does not
  authorise a separate shared-source writer or a new top-level track. The
  [data-maximisation/SOC plan in #868](https://github.com/edithatogo/archive-govt-nz/pull/868)
  provides detailed finance and join contracts; link proposed `O` IDs but
  do not copy its unsettled sources or its unaccepted draft code into main.
- Issue [#867](https://github.com/edithatogo/archive-govt-nz/issues/867)
  retains the sole serial integration queue. Check live PR heads, shared-owner
  acknowledgements and protected paths before any merge. Current exact
  local runtime contract is CPython **3.15.1**; a hosted 3.15.2 pass does not
  substitute for required native acceptance. Preserve existing CI/security,
  coverage, versioned captures and rights.
- For each bounded implementation PR: frozen input/source SHA and vintage,
  focused failing/regression case, independent oracle, required full release
  harness, exact-head hosted checks, no unacknowledged overlaps, and validated
  receiving main. Branch/PR "green" is not proof of deployed HF result.
- **No open existing PR met all merge prerequisites at this inspection.**
  Documentation adoption is independent of future release, model or source
  qualification. Never force an unreviewed merge just to clear the queue.
