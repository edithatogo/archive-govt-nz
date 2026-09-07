# Ordered operational verification

Prompt 13 operational acceptance is verified. Standalone no-write run
33968519628 completed before acquisition in full run 33968609350. Both ran
reviewed main `87f65e8b37cbc16bc6c7cf8b5b93a19e48f0f207`. The full run also
executed its own source preflight before harvest. Both preflight receipts
record credential presence, HTTP 200, a one-request bound, no redirects,
zero preserved payload bytes, and equal before/after state file hashes.

The exact sanitized snapshots are preserved in `preflight-only/source-preflight.json`
(SHA-256 `c27a5a6e453928430cef4c8d3243b8ecf3de6f2087ebb81efaee1eca73dd007d`)
and `preflight-full/source-preflight.json`
(SHA-256 `3b10952662ef41415d0f671ce280a959d3e80824406b9014939d6b2c850de2cd`).

All six retained artifact ZIPs were freshly downloaded using read-only GitHub
REST requests. Their exact lengths and SHA-256 digests matched GitHub metadata.
The native `tools/legislation_parent_state.py` functions `unpack`, `state_roots`
and `verify_parent` independently verified all 904 CAS objects, state roots,
receipt schemas, execution identity and the continuation seal. A changed CAS
object was rejected by the same verifier. The downloaded canonical payload
remains under ignored `build/operational-readback/`, outside source control.

The native `tools/reconcile_one_legislation_batch.py` was rerun against the
downloaded state and governed seed with batch `prompt13-ordered500-20260905`.
Its fresh receipt has zero mismatches. The 500 per-work outcomes equal the
governed seed exactly: 352 changed, 148 unchanged, no failed, partial,
unavailable or skipped works. Cumulative state contains 904 records; this is
not a claim that 904 distinct works were acquired in this run.

`verification.json` retains the independently calculated roots, counts, artifact
digests, primary step timestamps, negative control and fresh reconciliation.
`500-work-target-revalidation.json` is the superseding Prompt 13 receipt.
Original failed and blocked observations remain unchanged. Repository validation
and delivery are recorded in the track's run log, independently of execution.

## Reproduction

Retrieve run/jobs/artifacts through `gh api` for runs 33968519628 and 33968609350,
then each listed artifact through `actions/artifacts/<id>/zip`. Assert ZIP size
and SHA-256 against the retained metadata before inspecting members. Use the
native parent verifier on the complete-state ZIP; bind its reference roots,
seal digest, source, repository, workflow path and run identity to the primary
run and continuation. Compare the 500 receipt Work IDs to
`seeds/reviewed/historical-work-ids-0001.txt` and rerun the native one-batch
reconciler on the safely unpacked manifest, checkpoint and CAS.

Compare both source-preflight snapshots, require credential-present/HTTP 200,
and compare primary job timestamps to establish preflight before acquisition.
An HTTP 200 obtained using a configured credential does not prove that anonymous
requests would be rejected. No credential values were retrieved or recorded.

## Scope limits

The independently recovered and approved durable parent contains 552 records.
Both full runs continued from that parent. A 904-to-child second hosted cycle
and durable publication of the 904-record output remain unproven and are not
required Must criteria of this track. The optional second-cycle limitation is
retained explicitly. Actions artifact retention is not durable publication.
