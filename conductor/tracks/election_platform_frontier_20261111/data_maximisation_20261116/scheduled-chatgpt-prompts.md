# Scheduled ChatGPT implementation prompts and release gates

**Created 16 November 2026, Australia/Brisbane.** This pack contains copy-ready independent prompts for the sequential NZ electoral observatory programme. It belongs to the existing [orchestration plan](chatgpt-delivery-orchestration.md), [source register](source-register.md), [joining specification](outcomes-and-joins.md) and [Conductor execution plan](plan.md).

## Activated schedule and what it does

- **Single automation:** NZ Election Sequential Delivery (ID `6afa646d40848191bdf77031cf77a38c`).
- **Checkpoints:** Monday–Friday at approximately **08:30 and 16:30 Australia/Brisbane** (flexible scheduling may deliver within the following hour), first scheduled **16 November 2026 at 16:30**.
- **Principle:** one queued ChatGPT turn chooses the **earliest verified eligible** step, performs safe and authorised bounded work when available, or prepares the next actionable handoff. It does **not** automatically inject prompts into an already-running separate ChatGPT chat. Other workstream chats are started/resumed by their existing owners or through a subsequently authorised supported orchestration interface. It does not bypass the repo's single-integrator policy.
- **Progress is event-gated, not clock-gated.** A later scheduled run does not mean the prior step passed. Repeat/refine the current increment until the source, review, tests and merge receipts meet the stage gate. Stop duplicate work if another owner has claimed it.
- **Concurrency:** one sole existing integration coordinator, one existing shared elections/Conductor owner, at most **two** independent implementation owners initially (expand to three only if native resource/path isolation is established), and an independent **read-only** reviewer when needed. Do not assign every prompt to a new chat.
- **Scope:** scheduling this controller does not constitute consent to harvest restricted sources, activate new CI/source workflows, publish live Hugging Face releases, manage other chats, or bypass PR owner restrictions. Native CPython 3.15.1/full-repository test evidence and exact-head hosted checks remain mandatory.

## Shared preamble for every worker prompt

> Work in `edithatogo/archive-govt-nz`. First inspect actual `main`, all active PRs and exact-head hosted checks, coordination issue https://github.com/edithatogo/archive-govt-nz/issues/867, Conductor plan `conductor/tracks/election_platform_frontier_20261111/data_maximisation_20261116/`, `AGENTS.md`, `conductor/workflow.md`, source rights and named owner reservations. The **existing** ChatGPT coordinator in issue #867 is the sole PR integrator; existing shared elections/Conductor owner is `6af41384-bab8-8324-ae28-c6219d0c8177`. Do not duplicate open PR #866's repair owner, shared registry, owned native capture or publication objects. Accept only a distinct bounded lane and exact non-overlapping owned file paths. Reuse pinned original source bytes and existing Pydantic, Arrow, Polars, DuckDB and archive provenance. Start with failing focused tests and negative controls for behaviour changes; verify via repo-local CPython 3.15.1, `./scripts/test-focused.sh` and required `./scripts/validate.sh`, relevant mutation/security checks, exact-head CI and independent reference evidence. Report actual executed results or `not_run`; preserve source hashes/rights and unknowns. Open/update **one** scoped PR only when reviewable, do not merge or publish, and post a durable exact-SHA handoff to the sole coordinator on issue #867. No new workers, gate weakening, unauthorised source access, private political profiling, protected-donor de-anonymisation, or fabricated empirical/causal claims.

Copy the preamble together with the appropriate lane instruction below. The automation itself loads this pack and chooses one step **only** after preconditions are evidenced.

## Sequence and parallel launch windows

**Canonical stage identifiers for both the saved task and this document:** G0 baseline → G1 inventory → G2 contracts → G3 parallel pilots → G4 joining → G5 Gold → G6 dashboard → G7 expansion. P0–P10 identify prompts, not stage numbers. To advance a stage, require the previous stage's owner, source, exact-head, tests and acceptance receipt—not the elapsed schedule.

| Gate | Earliest eligible lane(s) | Can run concurrently? | Planned launch/check interval | Advance on |
| --- | --- | --- | --- | --- |
| **G0** baseline/owner admission | P0 existing coordinator and #866 owner | No competing integration or overlapping source edits | Every eligible checkpoint until admitted | #868 owner acknowledgement and independent acceptance; #866 protected restoration, exact 3.15.1 and current-head tests/checks |
| **G1** source/release inventory | P1 L00 source/rights/release integrity | Read-only independent audit only, no shared code writers | Next checkpoint after G0 accepted | Original source hashes/rights, dataset/Space discrepancy matrix, synthetic leakage negative controls |
| **G2** minimal contracts | P2 canonical source, finance, identity, geography and release interface | One acknowledged shared elections contract writer | Next checkpoint after G1 accepted | Versioned interface, explicit source and path owner reservations, independent negative admission controls |
| **G3** historical data pilots | P3 L10 finance and P4 L20 elections; P5 L30 read-only source assessment | **Yes:** separately claimed finance/elections worktrees and read-only external assessment | Next 1–2 eligible checkpoints after G2 acceptance, then on evidence changes | Independent reconciled first financial and electoral cohorts, source/rights and exact-head receipts |
| **G4** shared join spine | P6 L40 shared identity/finance/time/geography owner | **Serial shared writer**; isolated source extractors may continue | Next eligible checkpoint after accepted G3 inputs | Versioned referential integrity, join cardinality, temporal and source-total parity |
| **G5** verified Gold outcomes | P7 L50 electoral/turnout and P8 L60 finance | **Yes:** different admitted Gold namespaces, verified G4 interface | Next eligible checkpoint after G4 acceptance | Independently recomputed OID Gold, methods, source/coverage and uncertainty receipts |
| **G6** dashboard integration | P9 L80 existing dashboard/publication owner | One application/Space writer; publication independently authorised | Next eligible checkpoint after G5 acceptance | Actual served revision/source hashes, accessibility/exports, stale/rollback; or explicit no-publish hold |
| **G7** qualified expansion | P5 L30 admitted extra sources, P10 L70 research and expanded Gold | Source-specific lanes only after rights, schemas and owner/path admission | On accepted new 2026/2027 source/funding/filing evidence | Individually qualified O08–O15 outcomes; no broad release claim |

The fixed clock only **checks eligibility**; durations above are launch-window guidance, not promised finish dates. The published 27 November 2026 official results and 2027 finance filing dates are conditional acquisition opportunities, not permission to swap the active data vintage or republish automatically.

## P0 — Existing coordinator baseline and plan intake (G0)

> You are the pre-existing **sole integration/issue coordinator**, not a newly appointed coordinator. Inspect fresh main, #867, PR #868 and the separate owner-held CI repair PR #866 with their exact head SHAs, current checks, unresolved reviews and Conductor state. Determine whether #868's documentation-only plan is already admitted/merged, whether #866's existing fixes are accepted, and the repo-local CPython 3.15.1 validation/hosted requirements. Obtain durable acknowledgement from existing elections/Conductor owner before any overlapping shared edits. Merge *only* if you are that authorised existing coordinator and all current-head branch protection, independent review, security, provenance and required checks actually pass, using expected-head protection and receiving-main verification. Otherwise leave them open and publish the precise failing job/owner/gate with a bounded next action. Do not create a second queue, merge before checks, or repair #866 files from a competing chat.

**Done:** accepted/merged plan/baseline receipt with exact main SHA, or an explicit blocker; no inferred green status.

## P1 — L00 source-to-release integrity and inventory (G1)

> As the acknowledged shared election owner, or a separately assigned non-overlapping **inventory-only** worker, audit the current 2026 result vintage, Finance/Parquet `materialize_parquet.py` lineage, election app and live Hugging Face revision. Create a machine-readable expected/discovered/captured/extracted/reconciled/published source matrix by asset family and date/rights, storing source-original IDs/hashes and discrepancy reasons. Write negative regression fixtures exposing hard-coded 2026 results, model coefficients and synthetic campaign-finance samples **without modifying PR #866-owned files**. Separate source-published, captured, validated and deployed timestamps and stale/rollback states. If you lack ownership of shared code, limit changes to a newly reserved test/inventory namespace and hand interface requirements to the elections owner. Do not trigger live recapture or publication. Produce first verifiable inventory and downstream contract handoff.

**Done:** independent source and publication discrepancy receipt; all synthetic demonstrations explicitly isolated; no false historical finance claims.

## P2 — Canonical contracts and minimal source cohort (G2)

> You are the existing shared elections/Conductor owner. Freeze a minimal versioned source-asset/release, party/candidate identity, finance filing, result vintage, finance reporting scope, source rights and geography join contract for the first eligible 2023–2025 finance and 2017/2020/2023 voting-place cohorts. Reuse existing Pydantic/JSON Schema/Arrow/Polars/DuckDB contracts and preservation receipts, not a second pipeline. Explicitly represent source amendment, protected/aggregate unknowns, disclosed-donor thresholds, null vs zero, source publication date, canonical join key and historical party aliases. Add independent schema, mixed-vintage and duplicate/missing-hash negative tests. Get acceptance into main before the two downstream extraction lanes begin writing against this version.

**Done:** one accepted versioned interface plus independent conformance evidence and non-overlapping downstream path reservations.

## P3 — L10 historical political-finance extraction (G3; parallel with P4)

> You own **only** a newly approved finance extraction/test namespace (proposed `src/archive_govt_nz/domains/elections/finance_import/` and `tests/elections/finance_import/`). Select a bounded authorised original-source cohort: 2023–2025 annual party returns and available 2023 party/candidate/promoter finance. List original filenames, source publication URLs, rights, SHA-256, return period, party IDs and expected totals. Implement traceable structured extraction with page/cell locators, amounts and amended-source status; reconcile official declared totals independently. Preserve anonymous/protected donors and aggregate-only lower tail; no fabricated all-donor Gini. Distinguish loans, gifts, party/candidate/promoter spending and broadcasting allocations. Validate erroneous decimal, negative values, wrong period, duplicate annual/immediate declarations, unfiled vs zero and source-total mismatch controls. Send one owned PR and exact-head receipt; then extend only after first pilot accepted.

**Done:** one audited 2023–2025 pilot cohort, independently rechecked source totals, accepted interface handoff, documented uncovered records.

## P4 — L20 historical voting-place and geography backfill (G3; parallel with P3)

> You own only a separately assigned historical-source parsing/test namespace (proposed `src/archive_govt_nz/domains/elections/historical_import/` and `tests/elections/historical_import/`). Reuse already archived official 2017/2020/2023 raw-byte voting-place CSVs and source receipts before any new acquisition. Normalize election/vintage/party/candidate/vote-type/location keys and versioned electorate boundaries. Reconcile valid votes and seats against independently checked Commission totals, report missing/unmapped voting places and electorate coverage by year, and test many-to-many geographic bridge weights, aggregate conservation, ambiguous party aliases and boundary-vintage mismatch. Avoid claiming all-year completeness from partial derivatives. Do not edit shared dashboard, election core or finance namespace.

**Done:** independently accepted historical voting-place cohort and versioned geographic crosswalk with explicit missingness.

## P5 — L30 additional source and rights admission (G3 read-only, implementation later)

> Conduct a **read-only** eligibility and source-coverage review of 2026 large party donations, protected-donation quarterly aggregate/payouts, broadcasting allocation and actual expenditure, promoter register and returns, Meta/Google political advertising, corporate/NZBN/charity entities, parliamentary declarations and polling/NZES/local election sources. For each source record official URL, owner, available grain/time coverage, statutory filing-vs-publication date, licences/rights, access method, format, rate/ethical constraints, last-source update, legal disclosure thresholds, candidate canonical IDs, and expected joining value to O01–O15. Rank source cohorts by evidence yield and feasible refresh. Do not activate crawlers, access restricted sources, introduce credentials, infer protected donors or publish. Only after the existing source-rights authority admits a cohort may a separately reserved source-adapter namespace be implemented under standard test/PR evidence.

**Done:** source admission matrix with approved/pending/held statuses, no implied live harvesting.

## P6 — L40 canonical joining spine (G4; single shared writer)

> You are the existing **single shared elections owner** responsible for agreed canonical schema, not a parallel duplicate worker. Consume accepted finance and historical pilot output contracts. Implement or integrate versioned party/candidate identity aliases; donor/company/NZBN relationships only with reviewed evidence; financial annual-versus-immediate donation de-duplication; election-vintage and campaign-regulated-period joins; geography boundary concordances with weights; and immutable joins from election results to socioeconomic context. For each join measure input/output row counts, expected cardinality, unmatched/ambiguous/duplicate keys, temporal gaps and potential join inflation. Add discriminating negative tests for version mixing, falsely matched donors, de-anonymisation, mixed finance scope, advertising spend-range collapse and ecological-to-individual inference. Do not consume unqualified datasets or present joins as proof of influence. Freeze versioned read-only consumer contracts and publish exact-head independent acceptance.

**Done:** common join contract with independent referential/integrity evidence; no unowned shared schema writes.

## P7 — L50 electoral/turnout Gold products (G5; parallel with P8)

> You own only approved new election-result/turnout Gold outcome files and tests (proposed `src/archive_govt_nz/domains/elections/outcomes/results/`). Against accepted source vintages and joining interface, implement O01 coalition feasibility, O02 preliminary-to-official change tracking once official releases exist, O03 historical turnout and enrolment denominators, O04 party fragmentation and disproportionality, and O05 Māori roll/representation aggregates when source-validated. Start with the current verified preliminary cohort and published historic data; do not invent unavailable final results. Independently verify seat sum/majority and excluded parties, boundary-weighted turnout totals and party lineage, including zero-seat/nonqualifying parties. Produce deterministic Gold Parquet, audited CSV and machine-readable question receipts with source and code hashes. Do not modify the public Space; hand accepted published-input contract to dashboard owner.

**Done:** O01/O04 source-based Gold first, O02/O03/O05 on eligible source availability, with exact-head tests and limits.

## P8 — L60 political-finance Gold products (G5; parallel with P7)

> You own only a dedicated finance Gold outcomes/test namespace (proposed `src/archive_govt_nz/domains/elections/outcomes/finance/`). On the accepted financial Silver, duplicate control and join contract, produce O06 disclosed party/loan funding time series and donor concentration, O07 **filed** party/candidate/promoter spend per stated vote/seat/registered-elector denominator and real-vs-nominal CPI comparisons; O13 public cross-source organisation associations only after reviewed NZBN/legal identities and rights. Return unavailable for 2026 post-election spend until filings are actually published and validated. Treat small-donation lower tail as unknown and ad spend intervals as ranges; never label spending-vote association ROI or donor-policy causation. Independently validate cost numerator scope, denominators, source totals, entity matches, completeness, time bases and export parity.

**Done:** reproducible qualified historical financial Gold dataset with audited source attribution and visible holes.

## P9 — L80 integrate public dashboard and Hugging Face (G6; one owner)

> You are the **existing** shared elections/dashboard owner. Integrate only independently qualified Gold outputs for O01/O04, then O03 and O06/O07 as admitted, using a single versioned release manifest and immutable original snapshots. Build accessible Results Live, Historical Atlas and Political Finance sections, with source date, capture date, validation date, deployed date, preliminary/official status, coverage, unknowns, source and method links, downloadable CSV/Parquet and change history. Do not hard-code a second source of votes or substitute synthetic data in public views. Add browser mobile/keyboard/screen reader, stale/fail-closed, static data/chart parity and rollback tests. Verify required CI on the exact head, archive dataset hash, generated Gold hashes and **actual served Hugging Face revision** through a permitted owner-approved publication action. If permission/rights are missing, keep release unperformed with honest receipt. Only sole coordinator merges after acceptance.

**Done:** independently verified actual served release; not merely HTML or CI artifact created.

## P10 — L70 extended research, policy and institutional links (G7)

> After the relevant source/rights and identity/temporal joins are accepted, develop bounded O08 digital political advertising (spent amounts as intervals), O09 donation/lobbying transparency commitments, O10 dated economic context, O11 health/housing policy comparison, O12 frozen poll forecast accuracy, O14 local-versus-national electoral turnout and O15 dated coalition agreements/legislation/policy implementation with sourced claims. Use current [news issue register](news-issue-register.md) as question discovery only, not numeric authority. Build neutral, dated, party-symmetric source-linked topic comparisons, research-grade method cards and independently validated Gold result/coverage receipts; preserve `not_estimated` for invalid causal designs. Implement one source family/answerable question at a time in approved dedicated paths and publish through P9 owner only after gates. Keep experimental game/quantum/biological mechanisms outside empirical public claims.

**Done:** individually accepted additional OIDs and transparent source-date/method caveats; no blanket 'all joined' completion claim.

## Scheduled-controller checkpoint prompt (saved automation)

> Inspect the latest durable Conductor plan and issue #867. Identify the earliest unmet gated task P0–P10, check its exact evidence and owner reservation, and either perform one safe eligible in-scope increment or prepare the corresponding prompt/handoff to the **existing** authorised worker. Where two non-overlapping worker lanes can proceed in parallel (P3/P4; P7/P8), disclose both readiness states without automatically creating competing chats. Do not advance just because a calendar checkpoint elapsed. Publish one concise result with exact head/rights/verification status and next eligible stage. Never merge, publish, activate harvesting or create owner overlap.

## Checkpoint controls and expected outputs

1. **At every scheduled run:** inspect PR #868, issue #867, other active PRs, current main and previous wave receipts; avoid duplicate work if an implementation chat already owns the current gate.
2. **If blocked:** give one precise missing prerequisite and safe in-scope follow-up; do not invent a future completion date, auto-close the step or repeatedly perform identical checks.
3. **If eligible:** only one bounded action per run, with source identity, author/branch, exact input/commit hashes, tests and handoff; WIP limit remains binding.
4. **Merge:** only the existing sole integrator performs protected merges after current-base/current-head required checks and independent review; worker PRs remain open otherwise.
5. **Release:** only the existing dashboard/publication owner performs an authorised, independently verified Hugging Face write; the automation may report but not infer a successful deployment.
6. **Finishing:** report completed source-verified OIDs and outstanding optional research independently; stop repeated prompts for fully accepted work (the user can pause the recurring automation when the selected scope is finished).
