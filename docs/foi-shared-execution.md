# Shared FOI execution controls

The approved control authority is the dedicated `foi-execution-state` Git branch
in `edithatogo/archive-govt-nz`. Every write conditionally advances its exact
previous commit; GitHub workflow concurrency is an additional local safeguard,
not the cross-client lock. Receipts bind each operation to the authority commit.
A conflict is terminal for that command and requires inspection, never blind retry.

The manual workflow can explicitly bootstrap the branch, then enqueue, reserve,
and terminally reconcile a uniquely identified control rehearsal. Rehearsal
termination deliberately exercises a failed, exhausted job without fetching a
source. The state persists across runners. This verifies real shared storage and
lease transitions; it does not establish donor cutover or corpus completeness.

`tools/foi_dispatch.py plan --source SOURCE --receipt NEW_FILE` reads registered
sources and bounded acquisition scopes. Existing donor sources, including NZ,
remain blocked in this command. Merely supplying `--acquisition-authorized`
cannot enable their capture. Approved acquisition subsets have distinct IDs:

- `ca-federal-atip.nil-returns`: an offline executor for already-retained Canadian
  institutional nil-return bytes.
- `us-federal-foia.annual-statistics`: an explicit planning scope; no executor is
  attached in this dispatcher.

A numeric run/attempt suffix, such as `.20260831-1`, gives each independent
acquisition an immutable queue without replacing earlier evidence. Scope origins
are explicit: Canada's catalogue uses `open.canada.ca`; the bounded US DOJ report
uses `www.justice.gov`, distinct from the donor registry's `www.foia.gov` entry.
Neither subset replaces full-source ownership or claims national completion.

## Actual offline archival execution

With an appropriately scoped `GH_TOKEN` already configured:

```bash
uv run --locked python tools/foi_dispatch.py capture-ca \
  --source ca-federal-atip.nil-returns.20260831-1 \
  --owner-lease local-ca-20260831-1 \
  --acquisition-authorized \
  --input-root /private/retained-ca-input \
  --output-root /private/new-ca-package \
  --receipt /private/new-ca-control-receipt.json
```

The input contains `ati-nil.csv`, `ati-schema.json` and `source-metadata.json`.
No network request goes to Canada. The executor verifies the provider's dataset,
resource, schema and licence metadata, preserves original bytes, generates the
bounded index and manifest, and cold-restores into a second new private directory.
The source metadata must include an explicit successful provider response. This
is preparation and verification of retained bytes, not a new national crawl.

Before filesystem work, the command reserves work under the shared authority and
rereads the exact live job and owner. After successful restore it conditionally
records `captured`, the manifest SHA, and no publication revision. That terminal
state releases the active job lease while retaining its token history. It gives
no public coverage credit and uploads no raw package. Public rights/privacy and
anonymous restoration gates remain independent.

Each batch reserves at most one request slot, 64 MiB of storage and 60 seconds of
executor runtime. Actual source requests for this offline executor are zero.
Global active reservations share ceilings of ten request slots, 256 MiB and
600 seconds, plus one active job per origin. Pilot preflight caps every file at
8 MiB, the package at 40 MiB and the restore at 24 MiB before writing; generated
indexes are bounded before emission. Timeouts terminate the child process. These
are active-operation ceilings, not rolling daily quotas or an automatic fairness
scheduler.

Source policy, origin, adapter mode, retry/lease limits, batch/global ceilings and
registry metadata enter each job's policy hash. Any drift while a job is active
blocks admission. Therefore a legitimate catalogue update may require explicit
reconciliation of retained control state before further execution.

Failures preserve stage receipts and partial private files. A failed or uncertain
executor leaves its exact reservation fenced; there is no automatic expiry or
requeue. Successful preparation followed by a conflict remains reported as
prepared locally, not as an absent capture or verified shared completion. The
command currently cannot reconcile an arbitrary external executor's terminal
receipt or renew an expired source owner. Such stuck jobs require the bounded
recovery integration; do not delete state or reset tokens to bypass it.

No continuous acquisition schedule, production donor ownership transfer, public
raw publication, or automatic country-wide fairness is claimed by this deployment.
The separate read-only health lane reports stuck controls without dispatching work.
