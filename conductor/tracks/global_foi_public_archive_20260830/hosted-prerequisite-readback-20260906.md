# Hosted prerequisites and source reconciliation — 2026-09-06

No pending whole acceptance criterion was marked complete. Read-only verification
establishes the bounded facts below; [machine receipt](hosted-prerequisite-readback-20260906.json)
retains exact revisions, digests, counts and limitations.

## P1.5: verified components, full criterion pending

- [Real NZ batch 33307777685](https://github.com/edithatogo/fyi-archive/actions/runs/33307777685)
  remains the latest real-backfill run. Its successful `17226–17227` artifact is
  unexpired; downloaded ZIP SHA-256 matches GitHub and the existing receipt.
  All seven retained objects match their inventory sizes and hashes (49,405
  bytes). This proves that bounded retained artifact, not public HF restoration.
- Fresh issue #365 readback contains 685 completed ranges/receipts and no lease.
  Range arithmetic reaches 17,227 with no gap after the recorded canonical
  initial `0–500` block. The queue remains 33,208 entries, with 15,981 remaining.
  The NZ real-backfill monitor is still disabled. Older raw coverage and the
  known `17225–17226` missing-originals batch are not repaired by this check.
- [HF sync 33901357761](https://github.com/edithatogo/fyi-archive/actions/runs/33901357761)
  succeeded at `7793293e488bd39d3fbb1e36ceb98820beb40313`. Its execution receipt
  binds the standalone summary digest. The summary records 33,217 manifest
  rows, zero newly materialized records and no added/updated/removed entries.
- Anonymous reads at public revision
  `52d747d055b00eba3f185e000efa2700e43f8c1e` verified the
  [NZ manifest](https://huggingface.co/datasets/edithatogo/fyi-archive-nz/blob/52d747d055b00eba3f185e000efa2700e43f8c1e/manifests/latest_manifest.json)
  against the hosted artifact and summary digest, and the
  [card](https://huggingface.co/datasets/edithatogo/fyi-archive-nz/blob/52d747d055b00eba3f185e000efa2700e43f8c1e/README.md)
  byte-for-byte against the rendered artifact. The generated count, timestamp
  and manifest hash agree. The manifest read was capped at 32 MiB.

The recent seven HF-sync runs are successful and the latest real backfill has
not changed since August 30. This bounded observation does not establish all
retry behavior. In particular, the sampled sync is unchanged; AC03's changed
sync proof is not established. P1.5 remains pending under AC02/AC03/AC09.

## P2: deterministic reconciliation and one concrete correction

The pinned catalogue and materialized rollout have exactly the same 251 entity
IDs. All 30 catalogue source IDs survive in the 255-source rollout, with matching
entity assignments. The additional 225 rows reference source-discovery receipts;
they remain candidates requiring broader review, not reviewed archival sources.
No country is complete and all 251 entities still require broader discovery.

Content inspection found `ar-derechoaldato` referenced a receipt whose
`source_id` is `nz-fyi`. The old verifier only checked existence and reported
valid. P2.8 adds source-ID binding, checks entity IDs when receipts declare them,
and rejects missing identity, malformed JSON and non-object receipts. The AR
row now uses the existing `separate_pilot_receipt_required` state. No substitute
Argentina evidence or rights decision was invented. The corrected ledger has
225 discovery receipts, three other source-specific receipts and 27 placeholders.

Six red tests reproduced the defects. All 15 rollout tests now pass, with 100%
module line/branch coverage; Ruff format/lint and BasedPyright pass. Two isolated
source/entity guard mutations were killed by real pytest failures. Native
Conductor validation passes all 92 tracks. These checks establish receipt
attribution, not the truth or completeness of the receipt's assertions.
P2.2–P2.4 remain open for broader reviewed dispositions and matching phase gates.

## Reproduction and scope

- `gh run list --repo edithatogo/fyi-archive --workflow nz_real_backfill_batch.yml --limit 8 --json databaseId,conclusion,headSha,createdAt`
- `gh run list --repo edithatogo/fyi-archive --workflow hf_sync.yml --limit 8 --json databaseId,conclusion,headSha,createdAt`
- `gh api repos/edithatogo/fyi-archive/actions/artifacts/9731030582/zip`
- `gh api repos/edithatogo/fyi-archive/actions/artifacts/9947761049/zip`
- `gh api repos/edithatogo/fyi-archive/issues/365` (decode zlib/base64 body locally;
  retain only aggregate evidence in the repository).
- `gh api repos/edithatogo/fyi-archive/actions/workflows --paginate`
- Read the Hugging Face dataset API anonymously to pin its head; hash the
  revision-pinned manifest stream and card, and compare against ZIP members.
- `uv run --locked pytest tests/test_verify_foi_rollout_evidence.py --cov=archive_govt_nz.foi_rollout_evidence --cov-branch --cov-report=term-missing -q`
- `uv run --locked python tools/verify_foi_rollout_evidence.py conductor/tracks/global_foi_public_archive_20260830/country-rollout-20260831.json conductor/tracks/global_foi_public_archive_20260830`

Artifacts were inspected locally without extracting or committing source payloads.
No publication, dispatch, donor change, issue edit or ownership transfer occurred.
No full harness was started; the parent owns combined gates after integration.
