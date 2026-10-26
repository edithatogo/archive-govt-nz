# Parliament archive assessment — 26 October 2026

Status: proposed collection boundaries and execution design; no crawler,
schedule or Hugging Face publication has been activated by this assessment.

## Collections

| Priority | Collection | Preservation value |
| --- | --- | --- |
| First | Released public submissions and attachments | Original public evidence, including supplementary submissions |
| First | Official committee advice and attachments | Departmental reports, initial briefings, scrutiny memoranda and responses to evidence |
| First | Committee reports and business-item pages | Findings, recommendations and the relationships connecting evidence to its outcome |
| Next | Petitions, responses, and papers presented | Formal requests, responses and tabled accountability records |
| Next | Written questions and answers | Executive accountability records with distinct question/answer identities |
| Next | Order Papers, Journals and daily progress | Procedural chronology and changing business state |
| Next | Parliamentary Library research papers | Context and research publications, retained by edition |
| Reconcile | Hansard | Reuse existing domain implementation; independently establish capture coverage |
| Later | Hearing video/audio, captions and transcripts | Separate media lane after endpoint, rights and volume qualification |

Retain Parliament bill pages and their contextual links; reuse existing
legislation preservation for shared authoritative documents rather than
duplicating a full legislation pipeline. Preserve source identifiers and
relationships even when identical attachment bytes share one stored object.

## Live observations

- https://www3.parliament.nz/en/pb/sc/evidence-submissions/ displayed
  1,194,789 records, 20 per page, and describes committee-released evidence.
- https://www3.parliament.nz/en/pb/sc/submissions-and-advice/ displayed
  746,385 records and offers current, previous and all-Parliament views.
  The totals have different apparent scopes; neither is a proven unique
  submission count. Reconcile filters, legacy routes and overlapping identities.
- https://www3.parliament.nz/en/pb/sc/reports/ redirected to
  https://selectcommittees.parliament.nz/reports?Tab=Current . Its document
  discovery contract remains unqualified; the new host must be assessed.
- The submissions/advice page distinguishes public submissions from official
  advice and exposes document type, committee, date and business-item context.

## Independent work streams

1. Historical discovery: partition by verified Parliament/committee/business
   filters and date intervals. Persist each discovered page and an immutable
   candidate shard before acknowledging its discovery checkpoint.
2. Recent monitoring: revisit a bounded overlapping window, deduplicate by
   source identity and content, and periodically reconcile older partitions.
   Publication dates alone cannot detect all late releases or replacements.
3. Capture: consume durable candidate shards, streaming attachment bytes to
   temporary files while hashing. Atomically admit only complete verified
   objects; retain HTTP failures and incomplete work for bounded recovery.
4. Publication: consume verified capture batches, upload immutable object and
   metadata shards, verify the exact remote revision, then publish the batch
   receipt. Keep capture-complete and publication-verified checkpoints distinct.
5. Derivatives: extract text/OCR and build searchable Parquet shards separately
   so extraction failures never prevent preservation of originals.

Use distinct cursors and single-owner leases per collection/partition. Share
one host-wide request budget across all lanes; extra streams must not multiply
pressure on Parliament. Serialize updates to a shared Hugging Face catalogue
or use revision-conflict checks; never let competing uploads replace each
other's manifests or dataset card.

## Initial bounds to qualify in a pilot

- End a run at the first of 100 records, 250 MiB or 15 minutes.
- Initially allow one active request per host and approximately one request
  per second, subject to published access rules and server responses.
- Respect Retry-After; checkpoint and defer rate-limited work rather than
  retrying aggressively. These bounds are proposed, not measured capacity.
- Apply per-file limits and a bounded spool. Publish eligible completed
  batches as they become ready; reclaim local payloads only after verified
  remote recovery and the selected local retention policy permit it.
- Shard catalogue data by collection/partition and immutable batch identifier.
  Qualify archive packaging for large small-file counts before choosing raw
  per-document uploads versus bounded containers plus an offset index.

Do not rely on offset pagination alone for a changing index. Qualify sort and
filter semantics, retain boundary overlap and page fingerprints, and mark a
partition complete only after terminal-page and identity reconciliation.

## Implementation and acceptance sequence

1. Qualify old/new site routes, pagination, attachments, stable identifiers,
   access rules and reuse terms. Use synthetic/redacted fixtures in Git;
   submission payloads and personal data do not belong in the source repo.
2. Implement and test discovery, durable candidate shards and crash-safe
   streaming capture for one completed business item.
3. Confirm the exact existing Hugging Face destination and qualified write
   route. Use additive namespaced paths and a collection-specific description;
   the current CKAN publisher's blanket CC-BY description is unsuitable.
4. Verify a pilot upload by downloading its pinned manifest and sample original
   objects, comparing hashes and reconstructing the business-item relationships.
5. Enable bounded historical and recent lanes, then expand by collection after
   each source contract and recovery path has passed.

Report discovered, eligible, captured, failed, changed, withdrawn,
rights-pending and remotely verified counts separately. Public availability
does not establish a redistribution licence. Retain applicable rights and
restriction decisions and support withdrawn/replaced source observations.
No full-archive or operational-success claim follows from this document.

## Implementation and public-destination update — 26 October 2026

Reports now have a bounded resumable API/capture/publication lane. Ten reports were manually captured and anonymously hash-verified in the existing public, ungated [Hugging Face dataset](https://huggingface.co/datasets/edithatogo/archive-govt-nz-global/tree/main/parliament). All eligible Parliament outputs must use that public destination. Code rejects private or gated targets and has no repository-creation fallback. This is a pilot, not all Parliament data.

Submissions and most committee advice are excluded from the current general reuse permission; legacy crawler access is denied. Their full archival and additional legacy collections remain blocked pending qualified source/access/reuse contracts. See the [track evidence](../conductor/tracks/parliament_archive_streams_20261026/evidence.md).
