# Operational common dispatch for reviewed Vote Health overviews

Fourteen reviewed main Estimates profiles (2004/05-2017/18) now feed source
operations through actual common DispatchResult records, field lineage and
all-page losses. This closes operational adoption for these profiles, not
Phase3 or other publication forms. The2002/03 profile/composite and existing
direct normalizer APIs remain unchanged.

The public compact source-operation/v1 receipt retains its existing three-table
hash contract. A new closed internal
`archive-govt-nz.vote-health-overview-operation/v1` manifest records source
context, canonical AdapterSelection receipt and original common losses. Its
explicit compatibility projection preserves native table bytes, including
preserved_only to preserved_unreviewed and the legacy2016 unreviewed reason.
The original common losses remain available in the manifest. Rights remain
not_evaluated and currency remains null where the source does not qualify it.

`overview_operations.verify_overview` requires a separately retained manifestSHA
and trusted source/profile context. It verifies the pinned metadata before
provenance consumption, regenerates exact common selection and canonical table
hashes, rejects malformed/unknown/extra metadata or output files, verifies all
three bounded table snapshots, and rechecks the manifest pin. It never infers
its authority pin from the input file or repairs partial output. Scoped producer
run inventories/recovery receipts must retain the manifestSHA; the compact
operation receipt alone cannot authenticate embedded selection.

## Native proof

[Native run inventory and pinned manifests](./overview-operational-dispatch-20261017.json)
records14 profiles,209 facts and42 Parquet files per repeat. Every pre-existing
reference file was checked against its retained SHA before reuse. Both actual
source-operation builds match all42 canonical reference files byte-for-byte;
both new manifest sets are deterministic and pass externally pinned readback.
The14 metadata manifests intentionally evolve and are not claimed byte-identical
to old manifests. Existing outputs and Bronze source bytes/stat remain unchanged.

All70 actual common dispatches (preflight, two writes, two readbacks per profile)
were observed, while the direct native normalizer was patched to reject any
use. Each dry run created no output. No source download, rights decision,
analytical admission, external collection or publication action occurred.
Native command completed0 under the shared validation guard on clean276a8225;
implementation hashes bind its proof independently of later documentation commits.

## Focused and remaining assurance

Focused contracts pass545 tests with10 skips. They include actual dispatch use,
compact receipt stability, tampered selection/digest/loss/context and re-pinned
forged-output rejection, missing/extra output, wrong manifest pin and interrupted
partial-output retention. Existing repetitive direct-route mocks were replaced
with14 explicit common-route cases. Ruff and strict typing pass. The80% floor
and all deadlines remain unchanged. Full exact-head validation and PR delivery
are still pending. General recovery-profile admission and remaining adapters
are separate open tasks; no whole-track recovery claim is made.
