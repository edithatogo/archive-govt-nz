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

Additional ingress/accounting review reproduced two more safety cases before
native deployment: a non-PDF report attachment could enter a public checkpoint
before the existing package PDF gate rejected it, and a failed read could lose
its elapsed time when checkpoint transport reset the timer before retry.
Both exact tests failed red. Report bodies now pass the inherited PDF gate
before public staging; rejected bytes stay in the private working CAS, with only
an exact hash/failure receipt admitted to the public checkpoint. Failed/deferred
reads now charge elapsed acquisition time before checkpoint/retry. Both red
regressions and all ten affected qualification/checkpoint tests pass; selected
strict types and Ruff pass. No rights policy or body-format acceptance expanded.
The previous corrected head b26a3e53 passes full local assurance and hosted
Ubuntu/Windows/Codecov; these additional fixes require their own final-head gates.

SDK-output boundary: direct stdout/stderr diagnostics are now captured in unique
mode600 files inside the spool-accounted working root, excluded from projection
and artifacts. Two red cases reproduced direct diagnostic leakage for failure
and cancellation; both now pass, including private-file permission/readback.
Only the sanitized result reaches console/receipt. All48 hosted integration
tests pass and selected strict typing/Ruff pass. No SDK log or unqualified body
has been published. The final delivery commit requires complete local/hosted
checks; there are still no native checkpoint writes or archive acquisitions.

## Native handover checkpoint — 27 October 2026

PR795 mergedf4bfaa5c at13:43:45UTC after all required Ubuntu/macOS/Windows,
workflow lint, CodeQL and patch-coverage checks passed at23739145. Integrated
local assurance passed8600 tests,14 capability skips,96.53% coverage and every
required stage. Actual PortableSSD CPython3.15.1 and editable binding were verified.

The first native bootstrap created only the initial public control pointer, then
stopped on public_checkpoint_unavailable before a snapshot was committed. Its
failed receipt is retained as bootstrap-native.json. Later exact same-client
anonymous read succeeded; no client/authentication fallback was used. Readback
at342e6ac45e0225cfa6b97546de7c7e76d2e78019 shows checkpoint=null, enabled=false,
matching frozen local marker/owner,798 originals+1metadata-only locally, no pending
publication and the unchanged maintained card. No report acquisition occurred.

After the desktop interruption, the initial lease had expired at18:44:53UTC. An
exact red regression reproduced that the locked bootstrap recovery did not renew
its own matching marker owner. The fix renews that exact owner only after the
existing local lock and identity checks. Metadata reads now use the supported
SDK20-second timeout and only sha/private/gated fields, with missing flags rejected.
Installed SDK signature and one bounded native exact-target read qualified these
parameters; no custom HTTP client was injected. Native cloud binding/activation
remain pending until this runtime fix passes delivery and initialization recovers.

The first runtime-fix full gate passed8604 tests but exposed one fictional cursor
test consulting the now-existing live shared HF pointer. The production guard
correctly blocked it. Isolated that test's coordinator alongside its existing
mock catalogue/client; no production guard was removed. Its cached failure-only
rerun passes. Retained the first failure; the candidate full gate is rerun after
this test-input correction.

All8605 tests now pass. The Medallion mutation stage then detected its old
visibility-condition text anchor no longer matched the stricter fail-closed
condition. Updated that anchor while retaining the same private-check-removal
mutation and test selector. No mutation was removed or waived. Reuse completed
gates and rerun the affected mutation plus the not-yet-completed remaining stages.

## P7 enabled — native acceptance

Runtime PR797 merged5d0cf00f after all required checks, including all three OS
assurance jobs and patch coverage, were green. Recovered the exact frozen
bootstrap owner under the local writer lock;957 qualified object references
accepted and the disabled pointer released. No new discovery during bootstrap.

Cold Actions run40601930474 freshly anonymously verified all957 objects.
Cancelled run40603023729 after the accepted ten-entry recent discovery barrier.
Recovery40603567130 succeeded and bound its interrupted work to that exact
cancelled run/attempt; the old budget closed conservatively with no new discovery.
Actual historical pilot40603905138 then captured ten new originals from page80
within2465266 charged bytes and157.78088833 acquisition seconds. Batch626917401502927cdf2e2f25c2fa3a4f595b6efdd250e28d2f61d00df01d788c
at81e0ae56e58c8e866f0ab9cde6cf3b7fe3052036 passed native anonymous verification,
then a separate verifier passed13 pinned downloads (manifest,11unique objects,
maintained card). Current qualification observation:808 originals+1metadata-only,
20verified report batches,0pending/failed. Root card/YAML remain byte-identical.

Enabled the public pointer only after all native proofs. It now authorizes
hosted serial continuation; the original SSD remains frozen/retained. The
heartbeat was updated to monitor/review only, with no competing local capture.
Main subsequently merged unrelated Health PR798 at0fbaaeb4; Parliament production
code, workflow and locked runtime inputs are byte-unchanged from the qualified
head. All four native runs were manual dispatch proofs. Natural trigger/start/end,
recurrence and source completeness remain separate acceptance; parent stays active.

### P7 scheduled invocation parameter correction

Native job122519908295 (schedule40598353582) retained privately; bounded extraction
confirmed `--hold-seconds: invalid int value: ''`. Added workflow regression and
observed its expected red result before changing the expression to the explicit
string fallback. Full workflow policy tests/actionlint and corrected-head assurance
follow. Enabled production dispatch40606566606 is manual, not recurrence evidence.

### P7 first continuous-run checkpoint recovery

PR799 merged01ffe237 after every required check passed. Enabled manual hosted
run40606566606 published ten additional originals (818total+1metadata-only,
21verified report batches); an independent verifier freshly checked the manifest,
all11 unique objects and maintained card at97e904f5a07e25eb82e2ec03b6a939e5d9d7f205.
It then failed with checkpoint_commit_outcome_unknown; exact recovery verify run
40608984002 failed with the same sanitized code. Current immutable uploaded
snapshotafc0ab46c8d49b595125dd4ca2a5dda5b14eb8239c39f44938b71ee46076052d
retains cycle5 historicalpage82 discovery, zero observed/captured and a4194304-byte
reservation. No source acquisition may precede recovery. Original failed receipts
are retained. Do not infer quota, permission or successful commit from that code.
Added a failing sanitized-diagnostic regression, then bounded HTTP status and
numeric Retry-After fields; one native mutation attempt only, no response bodies,
URLs or arbitrary headers. Native operator cold verification uses the existing
qualified cached SDK credential and no source acquisition. Actions and operator
bindings remain separate evidence.

PR800's first Ubuntu/macOS runs exposed an in-process fixture leaking the CLI's
intentional process-global logging suppression into a later logging test. Windows
and the full initial local harness passed, showing order sensitivity rather than
an OS capability gap. Both hosted failures and the deterministic two-node red
reproduction are retained. The diagnostic fixture now follows the existing CLI
fixture convention and stubs logging.disable; the production CLI remains unchanged.
The ordered pair is green, and27 affected native/CLI/logging tests pass. Complete
corrected-candidate assurance is required; no check is waived or blindly retried.

### 28 October 2026: corrected recovery delivery and terminal-verifier reconciliation

PR800 mergedf9f65812216e096a615fb55d128d6ed39a7586cf after every required
Ubuntu/macOS/Windows, lint, CodeQL and patch-coverage check passed at24afe803.
The corrected local suite passed8618tests with14capability skips; all other stages
passed across the retained initial segment and terminal-interruption resumption
from mutation-legislation-checkpoint-root onward. No gate input changed between
those segments. No first failure or validation log was replaced.

A local network outage interrupted the operator's cold verification and its owner
release readback. Exact failed-receipt hash, terminal PID12077, owner identity and
uploaded snapshot were reconciled after connectivity returned. The same existing
verifier identity accepted snapshotafc0ab46c8d49b595125dd4ca2a5dda5b14eb8239c39f44938b71ee46076052d
at pinned revisionda502dc426fd0b960c766cf076d4759f9485bc65, then released itself.
981unchanged qualified references; zero new unqualified references. No takeover,
renewal, credential transfer, acquisition or replayed publication occurred. Native
readback confirmed enabled=true,paused=null,owner=null and verified snapshot.
Retained helper and intent/accepted/result receipts are under
build/parliament/hosted-handoff-20261027/terminal-verifier-recovery-20261028T0133;
the actual intent timestamp02:24UTC is authoritative; suffix is only a unique ID.
Original failed operator and Actions receipts remain immutable.

Native Actions recovery40620940956 was dispatched separately on mergedf9f65812,
with one bounded pilot attempt to close interrupted historicalpage82 work before
any new discovery. Its terminal receipt remains the next acceptance checkpoint.

Native recovery40620940956 SUCCEEDED onf9f65812: exact interrupted invocation
was gha_40606566606_1; zero observed/captured, no new discovery or publication.
The unknown interval was conservatively charged262144000bytes/900seconds, not
reported as transferred bytes. Cycle advanced to6;818originals+1metadata-only,
21verified batches,0pending/failed. Verified checkpointd429a9067baa697b93a363dd4bf4d3436e1707fd /
a9b294df7f19b80a656d5d548a5664a7413fcaa6369c1b4c2b9f92bdbf5a938d.
Continuous manual dispatch40621708833 now resumes serial bounded work. This is
workflow_dispatch, not natural recurrence acceptance. Evidence:
evidence/parliament-assurance/20261028/hosted-recovery-acceptance.json.

Actual natural run40619056595 triggered/started02:07:19UTC, terminal02:07:55UTC,
on01ffe237. The corrected cron inputs reached the CLI and correctly failed closed
on the retained verifier lease (parliament_writer_busy), without acquisition.
This is a natural fencing observation, not completed natural recurrence. Current
continuous run40621708833 was independently observed at02:39:37UTC onf9f65812:
correct GHA owner,enabled=true,paused=null,verified checkpoint,cycle7,work=null;
818originals+1metadata-only and21verified publications at that observation.

For documentation gates, our unstarted uv waiter was stopped after its shared
cache lock was found held by another process; that owner was left untouched.
Equivalent Conductor/format/secret gates ran through selected repo-local Python
3.15.1. The first direct secret invocation lacked the venv executable PATH and
failed before scanning; the qualified venv PATH invocation passed. No environment
replacement or cache modification was used. Source assurance remains unchanged.
