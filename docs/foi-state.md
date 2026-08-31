# Local FOI state persistence

`foi_state.StateStore` stores append-only canonical JSON versions in SQLite.
Every update compares the expected version under `BEGIN IMMEDIATE`, validates
retained history, and commits the snapshot and head together. A losing writer
receives `state_conflict`; it must reread and reconsider the transition rather
than replaying an external action. Closing and reopening the database preserves
accepted versions. Exceptions roll back the transaction.

The store rejects noncanonical or altered records, missing history, unsafe keys,
symlink database paths and configured document/history limits. Its per-key head
reference detects accidental tail truncation. The hash chain is an integrity
check, not a signature: replacing or rolling back the entire database and its
head is outside this guarantee. Use a trusted local directory and retain tested
backups. A path precheck does not protect against a hostile filesystem owner.

Default limits are 1 MiB per document, 10,000 versions and 16 MiB of encoded
history per key. These are not a global database or key-count quota.
Budgets fail closed; reaching the configured history cap requires explicit
retention planning. There is no automatic pruning or destructive compaction.
Do not put source payloads or credentials in the queue document. Raw objects
belong in the separately verified preservation package.

`foi_queue.QueueRepository` binds the owner fence and queue to one local state
version. The store itself grants no rights, verifies no publication receipt and
performs no network requests. It is not a cross-repository ownership authority:
sharing a SQLite file over network storage is not the deployment design.

Hosted execution still needs authoritative shared conditional updates, verified
source eligibility, enforceable run quotas and a sink that rejects stale owner
epochs (or a single executor serializing side effects and transfers). Successful
local tests do not activate captures, transfer ownership, or prove public raw
restoration.
