# Shared FOI execution authority

`GitHubStateStore` stores only control metadata in the dedicated
`edithatogo/archive-govt-nz` branch `foi-execution-state`. It never fetches a source,
publishes raw data or activates a scheduler. Normal reads fail when the authority
ref is absent. `bootstrap()` is the explicit exception: it creates an orphan
branch containing only an empty `state.json`, and verifies it by readback. It does
not import working-tree files, source records, credentials or unrelated history.

All source queues share one ref. The state contains its schema version, a global
generation counter and source-keyed queue documents. Keys must match their
owner's source ID. Only the strict queue schema is accepted; identifiers must be
bounded slugs. Source URLs, arbitrary descriptive fields and raw payloads are
excluded. Callers must generate opaque identifiers, never put secrets or personal
names into otherwise syntactically valid identifiers. This is not an automatic
secret classifier. Source-specific eligibility remains outside this backend.

`read(key)` returns a `StoredState` compatible with `QueueRepository` and records
the exact observed ref SHA. `read_all()` pins one complete snapshot for global
budget and origin checks. Subsequent source reads and writes cannot silently
refresh beyond that pin; a conflict requires a fresh explicit reconciliation.
Use trusted, revision-pinned policies to account for every active queue. Unknown
active source policies must block admission rather than be excluded from totals.

A write verifies the caller's source version and last-read global SHA, uploads a
bounded blob and tree, and creates a commit whose sole parent is that exact SHA.
It updates the ref with `force: false`. A competing commit makes the candidate a
divergent branch, so GitHub rejects its non-fast-forward update. No blind retry is
performed. The entire published snapshot is then downloaded again and checked.
This follows GitHub's [update-reference contract](https://docs.github.com/en/rest/git/refs?apiVersion=2022-11-28#update-a-reference).

A failed postwrite readback can mean the commit already succeeded and another
writer advanced the ref. The caller must reread and reconcile; it must not retry
capture, publication or bootstrap automatically. Failed CAS may leave unreachable
Git objects, but does not authorize dispatch. API errors are reported without
response bodies. Redirects are refused, response streaming is bounded in 64 KiB
chunks, and the caller supplies an authenticated client with finite timeouts.
Credentials are never persisted in state or receipts.

## Bounds and recovery

Each snapshot is capped at 1 MiB, each API response at 4 MiB, and the branch at
10,000 logical state generations. The worst-case snapshot history is therefore
approximately 10 GiB before Git compression, plus Git metadata; this is a hard
stop rather than automatic compaction. Operators must plan a reviewed archival
checkpoint and authority migration before the limit. Reads verify the pinned
commit/tree/blob identities, Git blob content hash, canonical JSON and all source
queue schemas. Historical Git commits remain available for forensic recovery;
the backend does not walk the entire ancestry on each read.

The concurrency guarantee assumes all authorized writers use this backend and do
not force-reset or delete the ref. This code does not install branch protections
or prevent a malicious administrator from rewriting history. A deleted ref must
not be recreated from an empty snapshot as routine recovery. Preserve the last
independently recorded SHA and reconcile against Git history before any explicitly
authorized repair. Hosted branch protection is a separate deployment concern.

Shared state CAS is necessary but does not alone fence external side effects.
Both donor and receiver must consult the same authority, drain admitted jobs
before ownership changes, and use an atomic sink condition or a single executor
serializing transfers and writes. Rights/privacy clearance, eligible raw restore,
shadow parity, rollback measurement and a scheduled incremental cycle remain
separate acceptance evidence. A control rehearsal is not production cutover.
