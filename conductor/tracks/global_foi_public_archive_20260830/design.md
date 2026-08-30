# Approved design and ownership boundary

DEC-FOI-001 assigns orchestration and public publication to `archive-govt-nz`.
`fyi-archive` remains the operational owner until verified transfer; approval
of the destination architecture is not evidence that cutover has occurred.

```mermaid
flowchart TD
  C[Versioned country and source registry] --> O[archive-govt-nz orchestration after cutover]
  O --> A[Pinned fyi-cli adapters]
  A --> Q[Original bytes and transport receipts]
  Q --> B[Content-addressed raw store]
  Q --> M[Object metadata and provenance index]
  C --> I[Global public source catalogue]
  B --> R[Rights and privacy eligibility]
  M --> R
  R --> H[Public HF revision: raw objects and metadata]
  I --> H
  H --> V[Anonymous download and hash verification]
  V --> L[Coverage and freshness ledger]
  L --> O
  R --> X[Restricted store and safe gap records]
  H --> P[Versioned downstream foi-process handoff]
```

No extracted index replaces Bronze. Raw source metadata and its searchable
projection have distinct identities. Snapshot manifests join source/object IDs,
content hashes, parent-child relationships, original response receipts and
published revision/path; derived rows cannot point at unverified uploads.

## Logical public layout

The following is a proposed layout, finalized after inventory and size review:

- global catalogue: `countries`, `sources`, `coverage`, schema and index manifest;
- existing per-instance repositories: `indexes/`, `manifests/`, `objects/sha256/`,
  and `receipts/`, with original formats or bounded WARC packages;
- legacy historical indexes remain intact and explicitly labelled discovery;
- raw shard/package manifests enumerate every member, byte count and SHA-256;
- public objects, metadata and catalogue entries carry reciprocal stable IDs.

Publish immutable payloads first, verify them, then promote indexes referencing
that exact revision. A failed upload/verification cannot advance the public
current-snapshot pointer. Prove interrupted publication and idempotent resume.
Only approved public fields reach catalogue exports; restricted metadata can
itself be sensitive even when raw payload publication is blocked.

## Safe lease recovery

Compare ledger revision, lease identity and owner-run state before release.
Successful runs require receipt reconciliation before crediting coverage.
Failed/cancelled terminal runs may be released only under the tested recovery
policy; active/unknown ownership stays fenced. State writes detect concurrent
updates. Never clear all leases or advance the cursor to skip the conflict.

## Migration

Import existing manifests/checkpoints as provenance-bearing records; do not
turn old manifest record counts into new raw-capture receipts. Reuse retained
captures for shadow comparison to avoid double source load. Export resumable
checkpoints and verify rollback before transferring the scheduler. Leave donor
code/history and public dataset identities intact. Fix donor-side incidents in
bounded scoped patches while it remains the active operational owner.

## Global rollout

The country universe is versioned; territories and the EU are separate entities.
For every country: discover named public sources, assess adapter/rights/pacing,
perform a bounded capture and restore, then enable backlog and incremental
schedules. Unsupported or blocked sources remain visible; adding a country
never silently activates arbitrary source URLs or creates a false 100% metric.

## Additional operational safeguards

- A top-level snapshot pins each per-instance repository revision and manifest
  digest. Promotion validates all references; a partial country upload leaves
  the prior valid snapshot discoverable. Old readers keep a consistent view.
- Export accepted raw bytes, manifests and checkpoints to durable storage before
  temporary Actions artifacts expire. Reconcile the oldest expiring batches
  first; do not replay sources merely because a temporary transport artifact vanished.
- A shared owner generation or equivalent durable fence spans both repositories.
  GitHub workflow concurrency within one repository is insufficient. A stale
  donor process must be unable to reserve work or publish after transfer.
- Restore from a pinned public snapshot and exported state in a clean environment,
  with no local cache. During an HF outage retain durable pending work, back off,
  and never mark uploads verified. State the measured recovery time and data-loss
  window; do not promise unmeasured availability.
- Treat source URLs, redirects, MIME types and attachments as untrusted. Block
  private-network destinations; do not execute active content. Bound archive
  expansion, member paths and parser resources. Retain eligible originals in
  isolation while quarantining unsafe files from public delivery.
- Configure per-source/global byte, request, runtime and retry budgets. Shard
  manifests and raw packages for bounded downloads; preserve object identifiers
  when compacting. Model queue age/fairness and storage growth, not only row counts.
