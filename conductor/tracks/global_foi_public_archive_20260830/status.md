# Current implementation status — 2026-08-31

The approved track is active. Repository setup and source-catalogue foundations are merged; public raw delivery, worldwide acquisition and scheduler takeover are not complete.

| Question | Verified answer |
| --- | --- |
| Which countries are fully captured? | None has passed full-snapshot raw/public-restore acceptance. Existing captures are partial and must not be promoted by queue counts. |
| Has it switched over? | No. archive-govt-nz is the approved receiver; fyi-archive remains the owner until parity, public restore and ownership fencing pass. |
| Is everything public on Hugging Face? | All 23 registered destinations were anonymously public and ungated at inventory time. This does not prove raw completeness. The public source catalogue and its indexes are published and anonymously verified; no new public raw upload was performed in this implementation. The separate AU/NSW private-retention destination remains private. |
| How many remain? | No global request denominator is known. The pinned discovery universe has 250 geographic entities plus EU: 28 entities have seed sources and 223 require source discovery. This is not a count of sovereign countries. NZ has 15,981 unprocessed queue entries out of 33,208; historic credited entries still require raw-retention reconciliation. |
| Why is NZ automation paused? | A successful artifact omitted original bytes. Automatic dispatch is disabled until retained-byte restore and durable retention are verified and historical gaps reconciled. |

## Delivered

- Approved Conductor track, parent issue #233, eight phase subissues, append-only evidence and repaired legacy validation; both Conductor validators report zero errors.
- Country/source/regime catalogue, donor seed and public-revision provenance, deterministic JSONL indexes and coverage report. Unknown denominators and rights decisions remain explicit.
- Guarded exact-lease recovery and dedicated HF sync summary/card contract. Hosted recovery succeeded; hosted HF dry run succeeded without uploading.
- Raw capture inventories, WARC payload and attachment hash verification, upload/clean-download verification before queue credit, and fail-closed legacy publication adapters that no longer fabricate delivery receipts.

One-request hosted raw restore passed in run 33307777685: seven retained files, 49,405 bytes, two WARC responses, exact manifest agreement with the queue receipt. That sample had no attachments. This remains temporary storage; no country-completion claim follows.

## Still required

- Full source discovery and per-source access, capture, redistribution and privacy decisions.
- Request/object metadata indexes, durable immutable raw packages and historical retention audit.
- Eligible raw Hugging Face upload, revision-pinned raw links, anonymous cold restore and raw capacity evidence for NZ plus a second eligible source. The public source catalogue is already delivered.
- Bounded country schedules, global ownership fencing, shadow parity, rollback and one observed incremental cycle after transfer.

The user's public-HF authorization is recorded. No repeated routine approval is needed; third-party rights, private data and provider capacity remain separate evidence requirements. Additional safeguards are mapped in recommendations.md. See metadata.json, plan.md and the dated receipts for acceptance state; successful tests do not close the remaining phases.

## Continuation scope

The metadata-only publication workflow is active. Latest observed run 33358508220
succeeded; evidence PR #267 is merged. Donor monitor 322525555 remains manually
disabled. Public catalogue verification does not satisfy raw publication gates.

Local scheduling, durable queue state and ownership/parity controls are being
validated. They do not yet provide a hosted shared authority or execute captures.
Source policy resolution, cumulative run quotas, authoritative sink fencing,
verified public raw restore and hosted incremental-cycle evidence remain open.

Canadian federal ATI nil-return originals have an explicit provider licence and
a bounded machine screen, recorded in ca-atip-candidate-evidence-20260831.json.
The 6,191 rows are institutional monthly nil returns, not released FOI responses.
No Canadian source activation, accountable privacy decision or public raw upload
is inferred. The NZ exact-candidate decision remains pending.

A new NZ v2 candidate was reconstructed and cold-restored from retained WARC evidence, with exact original-byte agreement. Its manifest differs from the historical candidate and is recorded separately. Three full local validation attempts timed out; focused controls remain green, and hosted validation is required before readiness.

Hosted Ubuntu passed 2,048 tests at 96.84 percent coverage. Its later secret-scanner failure involved two provider checksum fields, now omitted from the public projection without changing original metadata or scanner policy. Corrected-head checks remain pending on PR #272. The exact reconstructed candidate has its own pending decision.
