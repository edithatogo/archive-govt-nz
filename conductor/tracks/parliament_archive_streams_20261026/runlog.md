# Run log

## 2026-10-26 — planning registration

User requested Conductor update for the agreed Parliament archival plan. Inspected native workflow, autonomy policy, registry and track conventions. Used isolated codex/parliament-archive-plan-20261026 branch because the original checkout contains unrelated active health-archive work. Retained the assessment, created parent #778 and five nested phase issues, and registered requirements/design/pending tasks. No runtime, schedule, credentials or publication changes.

Validation results are recorded in evidence.md.

### Public destination requirement

User explicitly required all NZ Parliament archive data to use public Hugging Face storage. Anonymous native readback confirms `edithatogo/archive-govt-nz-global` has `private=false`. The publisher requires public visibility and does not create repositories or change visibility. Source eligibility is still distinct.

## Implementation and review checkpoint

Implemented report API discovery, durable SQLite/CAS state, original API metadata, streamed report capture, immutable per-version provenance, staged additive public batches, unknown-upload-outcome recovery and anonymous pinned remote verification. Initial failing synthetic tests preceded implementation. Focused suite: 74 passed; additional old-metadata regression passed. Public ten-report manual run and metadata-only tail batch verified (evidence.md). Full repository gate running. Parent remains active because source rights/access, mixed pilot, reconciliation and natural schedule acceptance remain incomplete.

Full suite: 8,423 passed, 14 capability skips, 97% aggregate coverage; schema gate and differential parity passed. Two-hour continuation heartbeat configured; first scheduled execution remains pending and acquisition stays gated on remaining assurance.

The full harness stopped at one fictional basic-auth URL in a negative test. Added an exact synthetic-fixture allowlist comment (no scanner scope reduction); affected regression passed. Initial direct supply-chain reruns lacked executable PATH; reran through the harness-equivalent `uv run --locked` environment. Strict SBOM validation passed for 118 components. Secret-scan rerun passed. All required stages now have passing evidence; original full command stopped at the corrected synthetic fixture.

Implementation PR: https://github.com/edithatogo/archive-govt-nz/pull/787. Hosted CI queued; no merge claimed. Parent remains active.

## User follow-up: Hub estate hardening

44 dataset cards validated then committed against observed parents; 42 anonymously downloaded/hash-verified, two pre-existing gated cards byte-verified with retained authentication and public metadata readback. Four public collections completed and anonymously read back (8 legal, 9 public-web, 5 HathiTrust, 24 FOI). Exact receipts: evidence/huggingface-hardening/20261026. Original file sizes, public visibility and existing gates preserved. Parliament catalogue: 4 batches, 21 rows, 10 distinct payload hashes; every manifest/object independently checked; first-rows HTTP200 all21.

Source prevention fixes: default publisher preserves maintained cards; missing explicit card fails before native writes; fallback counts unknown rather than zero; no invented dataset size/task/schema and no blanket mixed-source rights. Full harness: format/lint/types passed; 8424 tests passed with one intentional snapshot mismatch, corrected after review; affected11 tests passed. Remaining schema/parity/mutation/audit/licence/secret/SBOM stages passed by resumed harness. Snapshot whitespace repair required removing one extra paragraph break; exact snapshot rerun passed. No hosted viewer-completeness claim for pending/busy conversions.

P6 native follow-up: 40 hosted first-row probes across13 datasets passed. Historical backend conversion remains pending; Python3.15.1 isolated reader streamed101 rows with the corrected agency list feature. Initial JSON feature encoding passed card validation but failed the datasets metadata parser; corrected to its YAML list encoding and verified. RNZ mixed-format viewer now uses a74-row source-linked CSV derivative with original manifests retained; all74 rows stream directly. FYI probe corrected from train to requests. Public registry's44 relevant entries reconciled and validated; unrelated entries retained. Issue789 is a native nested subissue of778. Existing continuation updated for pending viewer acceptance and PR delivery, without repeating mutations for queued conversions.

P6 final native acceptance: all14 tabular repos, all41 first-row probes HTTP200; historical viewer returns17 first rows and isolated reader streams101. Registry refreshed at verified pinned revision. Estate landing collection additionally verified public with authoritative registry and relevant links. Final secret scan found two public collection-ID entropy false positives; exact reviewed receipt bytes are bound in the existing public-assurance adjudication, with a regression requiring changed/unrelated documents to fail. No scanner scope or credential rule relaxed.

Final source assurance after metadata follow-up: 27 supply-chain tests and strict selected types pass. The full harness and resumed stages plus affected11 tests cover the delivered source changes; no hosted-CI success is inferred for the new branch head. P6 native acceptance is complete; its issue closes with the reviewed implementation PR.

## Natural heartbeat — Windows CI diagnosis

The first scheduled gate check verified Python3.15.1 and queued one targeted Windows rerun after cancellation. That rerun also cancelled. Native check annotations now identify the 30-minute aggregate job ceiling; both attempts terminate at35 minutes including cancellation grace. Job-log API returns BlobNotFound and no Windows test artifact exists. Linux, macOS, CodeQL and workflow lint passed at the previous head. No new acquisition ran while required Windows acceptance was missing.

Applied a Windows-only60-minute aggregate job allowance, retaining Linux/macOS30-minute and per-command1200-second bounds and every required gate. Added a55-minute locked-gate step bound plus pipefail-preserving log capture and always-upload Windows diagnostics, leaving reserve before job cancellation. This is bounded remediation and observability, not proof of Windows success or a measured runtime estimate. Actionlint/Ruff and21 focused workflow/harness tests passed; reviewed full two-file diff. Receipt: evidence/parliament-assurance/20261026/windows-job-timeout.json. New hosted checks required before merge/scaling.

## Natural heartbeat — aggregate allowance insufficient

The new Windows job also exceeded its60-minute aggregate limit; its locked-gate step remained in progress, no Windows diagnostics artifact executed, and job-log storage returns BlobNotFound. Linux/macOS and other checks passed at0222bf4a. Increasing the allowance did not fix the stall. No further blind rerun or allowance increase; archive acquisition remains gated. Precise internal stage remains unobserved.

Source review identified that Windows stage timeout killed only uv, leaving child processes/output handles possible. Applied bounded owned-tree termination via the absolute Windows system taskkill.exe (/PID /T /F,30-second cleanup bound) before launcher reaping. The Windows job now invokes the identical locked harness under native PowerShell with a persistent transcript, finalization and native exit-status propagation; Linux/macOS retain their existing Bash route. Required stages,1200-second command bound,55-minute step and60-minute Windows job caps remain. This is a process-tree/output-handling hypothesis pending native proof, not an established root-cause claim. Actionlint, PowerShell AST parse, Ruff, selected strict types and21 focused workflow/harness tests passed. No other local writers were active.

## P7 implementation candidate — 27 October 2026

Authoritative SSD capture is frozen; no acquisition or publication was launched.
Actual repo-local CPython3.15.1 and editable binding were retained. Added typed
report projection, immutable public checkpoints, independent pinned acceptance,
fenced continuation, lazy cold restore and qualified hosted scratch retirement.
Added trusted-main finite workflow, operator pause and checkpoint-linked native
interruption proof requirements. Initial focused tests failed for the missing
implementation, then passed. Review added prepared-publication cold restore,
legacy source/publication fencing and exact cancelled-attempt proof tests.

Focused integrated milestone:105 tests passed before the additional fencing test;
that exact test file subsequently passed5 tests. Strict selected typing passed.
The first bare basedpyright launcher had a stale shebang after worktree relocation;
repo-local `python -m basedpyright` succeeded without changing the environment.
No rights gates, archive card, remote objects or authoritative SSD originals changed.
Full candidate assurance and hosted/native acceptance remain pending.

P7 full first candidate passed every local stage:8564 tests passed,14 capability
skips,96% repository coverage, schema/parity, mutation, supply-chain and SBOM
gates. That run identified SQLite connection warnings in new continuation paths;
review fixed deterministic connection closure and added initial-pointer unknown
outcome recovery plus explicit operator resume that preserves existing enable
authority. Verification remains available while paused, without source traffic.
A failed report remains held after resume. Added SDK/public-namespace and native
run/artifact fixtures, source capture/one-transient-retry, lane separation and
adversarial projection checks. The35 new hosted tests pass with84.67% branch-aware
coverage of the four new hosted modules; this is scoped evidence, not full-project
acceptance. Selected strict typing and Actionlint pass. P7 is nested issue794.
A fresh complete candidate gate follows these review changes.

The reviewed full candidate passed all required local stages:8581 tests,14
capability skips,96.50% repository coverage, schemas/parity, every mutation lane,
audit, licences, source scan and118-component SBOM validation. No vulnerabilities
were reported by that audit. Offline projection of the frozen SSD validates799
report records,957 qualified objects (80 new request receipts),99 candidate
shards and an822290-byte compressed snapshot. All119 unreferenced objects remain
excluded. Receipt: `build/parliament/hosted-handoff-20261027/implementation-preflight.json`.

Final startup review found a disabled scheduler could encounter the initial
bootstrap pointer before its snapshot existed. An exact red test reproduced
checkpoint_missing; the controller now checks disabled/paused control before
loading a snapshot, preserving a harmless no-op during bootstrap. The cached
failure-only rerun and affected strict typing pass. A fresh full gate runs on
the delivery commit; hosted checks and native acceptance remain pending.

## P7 hosted review, PR795

All local stages passed at658dcbc3 (8581 tests,14 capability skips,96.50%
coverage). Native Ubuntu assurance, workflow lint and CodeQL passed; macOS and
Windows were still running when review identified three valid P2 findings.
Exact isolated red tests reproduced stale-owner proof transfer, discovery
without a total deadline, and bootstrap proceeding while a local writer held
its lock. Fixed all three: identity-bound terminal proof, remaining-budget
async deadline, and the existing process-lifetime writer lock held through
bootstrap acceptance. Each exact red regression now passes.

Codecov reported79.50% patch coverage against the unchanged80% target. Moved
the operational CLI into a measured package module with a thin checkout entry
point and tested cold verify, pause/resume/enable authority, explicit index,
sanitized errors and cancellation. No coverage rule or exemption changed.
Forty-four hosted tests passed with86% branch-aware coverage across the five
hosted modules; added two further live-owner/card-drift resume guard cases.
Selected strict types and Ruff pass. Corrected-head complete local and hosted
checks are required; source acquisition and native handover remain disabled.
