# NZ Parliament report preservation

Source: [New Zealand Parliament select committee report index](https://selectcommittees.parliament.nz/reports?Tab=All). Maintained by [archive-govt-nz](https://github.com/edithatogo/archive-govt-nz); independent, not endorsed by Parliament.

## What is present

Immutable batch manifests link exact original PDF report bytes and original public API response bytes. The derived `catalogue.jsonl` is a navigation aid; its `snapshot_revision` fixes the reconciled batch population. `catalogue-receipt.json` records measured counts. Overlapping pilots share files and must not be counted as distinct source documents solely by row or batch count. `source_metadata` and `source_payload` are separate representations. Metadata-only records have no available attachment; unknown source dates are explicit.

The current source index was observed to contain 10,970 report entries. Only bounded pilot batches have been captured here. No full report, full historical Parliament, submission or advice completeness claim follows from the pilots or the index total.

## Reuse and source boundaries

The [Parliament copyright statement](https://www.parliament.nz/Copyright) identifies select committee reports as public domain. Official Office of the Clerk / Parliamentary Service catalogue metadata is attributed to New Zealand Parliament under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); original API bytes are unchanged. Consult the exact hash-bound manifest decision and [repository rights guide](../RIGHTS.md). Submissions and most committee advice are excluded from general source permission. Legacy generic crawler access is denied. Those lanes stay blocked; no private fallback is used.

## Download and restore

Use the catalogue's `snapshot_revision` when retrieving its manifest and object paths with `hf_hub_download(repo_id="edithatogo/archive-govt-nz-global", filename=PATH, repo_type="dataset", revision=REVISION, token=False)`. Verify SHA256(manifest bytes) equals `batch_id`; verify every original's SHA256 and byte count. Never treat a successful upload response as remote recovery proof. The metadata maintenance pass independently downloaded and verified every manifest and referenced object at its snapshot revision.

Use for preservation and reproducible source analysis. Do not infer official endorsement, legal currency, complete coverage or permission for unrelated content. Cite New Zealand Parliament, this dataset, pinned revision and exact batch/object hashes. Record any transformations separately. Report metadata/integrity issues to the project issue tracker with dataset/revision/hash; avoid disclosing sensitive content.

## Updates

The worker has separate historical/recent cursors and acquisition/publication checkpoints. It preserves old versions rather than silently overwriting them. Scheduled execution, historical reconciliation and full archival completion require their own evidence. The catalogue is rebuilt from published immutable batches and may lag later uploads. Existing Hansard distributions remain separately identified in the legal/parliamentary collection.
