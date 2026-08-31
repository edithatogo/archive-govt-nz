# Parent-state restoration contract (Prompt 08)

Issue [#312](https://github.com/edithatogo/archive-govt-nz/issues/312).
This interface authenticates Actions continuation packages. It does not acquire
sources, discover a latest run, merge state, select durable storage, publish data,
or grant recovery authority. The three existing legislation workflows use
`.github/actions/legislation-parent-state/action.yml` before any state consumer.
The harvest workflow seals successful output before uploading a continuation.

## Trust and authority

The caller selects a **committed, unchanged, canonical JSON** reference below
`config/legislation/parents/`. Canonical JSON means sorted keys, two-space indent,
ASCII JSON escaping and a terminal LF, as emitted by `M.encoded` in the helper.
Thus document hashes are exact file hashes, not normalized substitutes. The CLI
checks the checkout commit against `GITHUB_SHA`; governance files must match
`git show HEAD:<path>`. Only the canonical repository's `main` context is accepted.
The library accepts already authenticated dictionaries: callers must provide the
same trust boundary themselves, never trust descriptors supplied by a download.

No operational reference or initial authority is supplied by this change. The
workflow default `config/legislation/parents/current.json` is deliberately absent.
Scheduled runs therefore fail before acquisition until an approved reference
exists. Do not convert that failure into bootstrap or auto-discover a replacement.
Updating a reference requires review of a new exact run/artifact and its receipts.
Expiry or a missing artifact requires a new reviewed choice, not a retry against
some other run. Prompt 09 owns durable storage and its selection.

The reference schema is `schemas/legislation-parent-reference-v1.schema.json`:

- Repository full name and numeric ID; explicitly reviewed workflow path, ID and
  name. New lane workflow names require reviewed pins, not library edits; live
  metadata must match the exact pinned workflow.
- Run ID, attempt, branch and exact software commit.
- Artifact ID, name, SHA-256 digest, size, `expired: false` and exact expiry instant.
- Manifest semantic root and exact file hash; checkpoint file hash; inventory
  root; CAS root; exact complete harvest receipt hash; supported schema versions.
- Explicit source identity: `legislation` with no seed, or the reviewed stable ID
  `historical-work-ids-0001` and its registry-verified byte hash.
- Exact continuation receipt hash, or `null` only for separately authorized legacy
  adoption. An unsealed parent is never accepted in continuation mode.

The CAS root is SHA-256 of canonical JSON containing the sorted list of
`{"sha256": digest, "size_bytes": size}` for every unique referenced CAS object.
The manifest verifier separately authenticates SHA-256, BLAKE3, byte size,
canonical identities, work membership and all checkpoint/receipt links. No orphan
CAS object is allowed. State documents use strict JSON, rejecting duplicate keys
and non-finite numbers. A success receipt must be committed, error-free and report
`changed` or `no_change` with consistent counts and roots.

## Initial modes

`bootstrap` means explicitly authorized empty state, with no parent reference.
`adopt` means an otherwise fully verified legacy native package with no lineage
receipt. It is not the donor ZIP format and is not the Prompt 04 merger. Adoption
must pin the exact native parent and attest its source identity. No metadata,
root or inner-object check is relaxed by adoption.

Both require a separate reviewed record below `config/legislation/authorities/`,
validated by `schemas/legislation-initial-authority-v1.schema.json`, plus explicit
`confirmed_initial: true` on a manual dispatch. The record names `edithatogo`, a
stable decision ID, approval/expiry instants, mode, source identity and exact
repository/branch/workflow/execution scope. Adoption also binds the exact parent
reference hash; bootstrap requires that field to be null. The execution ID is the
harvest batch ID, or the read-only workflow's explicit verification ID. Scheduled
runs cannot use either initial mode. A decision's reuse/replay policy remains an
operator responsibility: do not reuse a batch authority for another execution.
No signatures or remote approval are inferred from a JSON field; review and the
committed main-branch record establish the authority boundary.

## Quarantine and promotion

The interface uses a fresh private quarantine and a fresh destination on the same
filesystem. It rejects symlinked or overlapping paths. An exclusive, retained
reservation prevents cooperative callers from sharing a destination. The caller
must own the workspace; this is not a security boundary against another process
with permission to mutate that workspace. Use a fresh workspace after failure;
never erase a failed attempt to make a retry look successful.

Only fixed GitHub API endpoints receive the Actions read credential. Metadata is
fetched live, with every identity and expiry checked. The artifact redirect must
be HTTPS on an allowed GitHub Actions blob domain, without user information,
fragment or nonstandard port. The credential is not forwarded to storage. Signed
URLs and remote exception bodies are never written to receipts or logs.

Limits: 64 MiB archive, 128 MiB expanded state, 64 MiB per member, 4,096 files and
200:1 member compression ratio; metadata responses at most 1 MiB. Requests have
20-second transport timeouts and a 120-second elapsed check during body reads.
Limits fail closed; increasing them requires a reviewed contract change. HTTP
content encoding must be identity so HTTP decompression cannot bypass ZIP bounds.
ZIP members are read in memory before filesystem extraction. Only native state
files, canonical CAS paths, current lineage/seal and content-addressed receipt
history are accepted; traversal, duplicates, symlinks and encryption are rejected.

Downloaded bytes remain `quarantine/artifact.zip`. Only after outer digest, all
members, complete state and lineage pass does the helper create a verified stage.
It writes `quarantine/lineage.json` and `receipts/parent-lineage.json` **before**
renaming the stage into the absent destination. Incoming harvest, parent-lineage
and continuation receipts are preserved verbatim under
`receipts/history/<SHA-256>.json`; the old harvest receipt remains available to
read-only consumers until the next harvest replaces it. No historical bytes are
rewritten. No partially extracted state is promoted.

On failure, `restoration-receipt.json` is a failure capsule, not a continuation
package. Missing files/context produce a sanitized preflight receipt. If even the
receipt path is unsafe/unwritable, the command exits nonzero and says that receipt
creation failed. No empty state is substituted. Callers must stop on nonzero exit.

## Caller interface

After installing the locked environment, a caller passes the selected reference,
expected seed identity (if any), exact Actions context and fresh paths:

```sh
uv run --locked python tools/legislation_parent_state.py restore \
  --mode continuation \
  --parent config/legislation/parents/REVIEWED-REFERENCE.json \
  --state build/legislation-state \
  --quarantine build/legislation-parent-quarantine
```

For the exact-inventory lane, add `--seed-id historical-work-ids-0001`; the helper
resolves the registry rather than accepting a seed path. The parent must declare
that same identity. The discovery lane explicitly omits a reviewed seed and must
use a parent declaring no seed. A lane/source transition requires an approved
interface change; do not relabel a parent to force acceptance. Seed identity alone
does not prove all reviewed IDs were acquired or full legislative coverage.

The composite action sets `PARENT_EXECUTION_ID` and accepts mode, reference,
authority, confirmation, seed ID and Actions credential. `GITHUB_*` identifies the
repository, workflow, branch, run, attempt, event and checked-out revision. Caller
acquisition must run only after the action succeeds. No source request is made by
this helper. Tests use synthetic HTTP transports and packages exclusively.

After successful acquisition, the caller must run:

```sh
uv run --locked python tools/legislation_parent_state.py seal \
  --state build/legislation-state \
  --quarantine build/legislation-parent-quarantine
```

Sealing re-verifies complete state and compares lineage with the original
quarantine receipt and exact saved bytes. It writes
`receipts/continuation.json`, binding output roots, source, execution context and
one verified parent-lineage hash. Only then may a complete state artifact upload
run. Partial/retryable outcomes and sealing failures are failure artifacts, never
parents. The CLI records sealing preflight failure separately without replacing
restoration evidence. Read-only reconciliation and recovery use verified restored
state; this issue does not execute either operation or create a new continuation.

## Downstream handoff

Prompts 06/07 can use this action and stable seed interface. They still need
approved Prompt 11/12 concurrency and failure-semantics interfaces. Source/seed
transitions, bootstrap replay policy and partial-acquisition retry handling must
be explicit; this helper must not silently relabel or bless those states.
Prompt 09 may supply a different authenticated transport through a future reviewed
adapter without changing the inner-state, source or lineage invariants. Prompt 08
makes no remote restoration, archival or recovery claim.

Run focused tests with `pytest tests/tools/test_legislation_parent_state.py` and
workflow guards with `pytest tests/tools/test_legislation_workflow_integrity.py`.
`tests/tools/run_legislation_parent_state_mutations.py OUTPUT` runs bounded guard
mutations with fresh source copies and retains every log/hash. The repository's
full `./scripts/validate.sh` remains mandatory before PR delivery.
