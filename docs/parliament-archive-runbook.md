# Parliament archive operations

Use the repo-selected `.venv/bin/python` and verify Python 3.15.1 before running. The public destination is fixed to [edithatogo/archive-govt-nz-global](https://huggingface.co/datasets/edithatogo/archive-govt-nz-global/tree/main/parliament). Every batch requires anonymous, ungated readback and revision-pinned hash verification. No private fallback exists.

Use one durable `--state-dir` for historical/recent report streams and one active owner. Keep its SQLite ledger, CAS, candidate shards and batch manifests together. Do not place it solely in expiring CI artifacts. This task uses `build/parliament/public-reports` backed by task-owned PortableSSD storage. Do not replace the environment or state beneath a running process.

```sh
.venv/bin/archive-govt-nz parliament --action status --state-dir build/parliament/public-reports
.venv/bin/archive-govt-nz parliament --action run-reports --state-dir build/parliament/public-reports --partition historical --max-records 100 --max-bytes 262144000 --max-seconds 900 --max-spool-bytes 8589934592
.venv/bin/archive-govt-nz parliament --action run-reports --state-dir build/parliament/public-reports --partition recent --max-records 100 --max-bytes 262144000 --max-seconds 900 --max-spool-bytes 8589934592
```

Historical resumes its independent cursor. Recent revisits the first ten pages; historical offsets may shift, so neither exhausted offsets nor this recent window proves complete coverage. Periodic full reconciliation is required before a completion assertion. Each turn first recovers any staged report publication before collecting new work. Acquisition time/body/record limits are separate from the subsequent checkpointed native publication and verification stage.

The public report API response is preserved verbatim, with payloads separately hashed. Missing attachments and unknown dates stay explicit. Unknown source fields, robots denials, redirects, cooldowns, lease conflicts, invalid PDF responses, hash mismatches or private/gated targets fail closed. Do not change the user agent to evade a denial. Do not auto-retry a native mutation or clear a lease file to force an active writer out.

For a failed capture, inspect the bounded error and use `--action retry --source-id ID` only after resolving its cause. For an intentional new source observation, use `--action refresh --source-id ID`; old bytes and metadata remain immutable. A staged batch can be resumed using `--action publish --batch-id HASH`; an unknown upload outcome is checked remotely before another commit. Preserve failed-verification evidence. Do not delete spool originals without a qualified retention/recovery policy.

Submissions and most committee advice lack general reuse permission in the current source statement. Legacy generic crawler access is denied. Their adapters and the additional legacy collections remain unqualified; do not enable them merely because report capture works. Report manual proof, future natural schedule proof and complete archive reconciliation are distinct gates. See [track evidence](../conductor/tracks/parliament_archive_streams_20261026/evidence.md).
