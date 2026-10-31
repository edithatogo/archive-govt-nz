# Historical legislation packets

The manual **Historical legislation packet** workflow enumerates one oldest-first
page of 100 PCO Acts, selects five works with missing manifestations, enumerates
their versions to a terminal page (at most ten 100-version pages per work), and
captures every absent API-listed XML, HTML, PDF and original scan. This first
scope is legislation before 1901. It is a bounded acquisition packet, not a
national inventory or completeness assertion.

Use the existing `legislation-canonical-state` serialized writer. The workflow
restores an explicit approved parent through the existing custody verifier into
isolated Actions state. The routine freshness workflow and Parliament objects
retain their existing ownership. API authentication stays in the existing GitHub
secret. Original downloads are anonymous, confined to official PCO Act URLs,
paced, and limited to 16 MiB/file and 128 MiB of new response bodies per run.
Advertised PDFs require PDF signatures; XML must be an Act representation, and
HTML must identify its offered Act before custody. HTTP200 alone is insufficient.
The newest row of the API versions endpoint can advertise `latest` aliases.
These are pinned to that row's explicit expression date within the matching Act
path, and both advertised and dated URLs are retained in the inventory. Downloads
and canonical identities use dated URLs; floating links remain inadmissible.
No credential is forwarded to original-document endpoints; no native mutation is
retried. Unknown source formats, redirects outside the qualified host, partial
version lists, malformed pages or unsuccessful originals stop admission.

The canonical service receives explicit expression/manifestation targets with no
fallback substitution. An existing XML cannot substitute for a missing PDF or
scan. PDFs preserve their original bytes and source identities; empty extracted
text is intentional, not an OCR claim. Each parent record must remain byte-equal
in the cumulative manifest. The existing SHA-256/BLAKE3/CAS, accounting,
checkpoint and continuation-seal verification runs before packaging. The deterministic compressed
cumulative ZIP retains old objects, receipts, lineage and history, subject to the
existing canonical recovery size/expansion limits.

Both operations run from `main`, matching the existing parent-lineage boundary.
Run `capture` first. Inspect the immutable capture artifact, inventory, source
metadata, accounting and package SHA-256. The `publish` operation runs only from
`main`; it requires the exact successful capture run and inspected package digest.
The user's 31 October 2026 direction authorizes this bounded official-Act scope
and publication; the runtime records this as delegated scope authorization,
not as a claim that the user personally inspected a previously unknown hash.
The [current PCO copyright statement](https://www.legislation.govt.nz/copyright/)
permits reproduction of published legislation and licenses its other Crown
content under CC-BY. Preserve PCO attribution for presentation/API metadata;
incorporated third-party works remain outside this permission.
Existing records keep their prior source-specific rights. This scope grants no
rights over agency documents, third-party commentary or unrelated records.

The publisher verifies the exact existing dataset is public/ungated and qualifies
operation-specific write access using the supported SDK `auth_check(write=True)`.
It adds package, metadata, inventory and source-page evidence in one parent-bound
commit under `durable-state/v1/historical-CAPTURE_RUN/`. It never creates a dataset,
replaces a package or rewrites cards/rights/history. All four files must download
anonymously at the resulting exact revision and match their local bytes before a
verified publication receipt is emitted. Unknown commit outcomes retain the
journal; an existing exact package is reconciled by readback without another
write. Conflicts or mismatches remain failures.

Publication preserves the original default parent and immutable snapshots. It
creates a sealed cumulative child available for explicit later adoption through
the existing approved-parent mechanism. Do not silently switch the routine
workflow to an unreviewed parent. The native publication receipt identifies the
package path, revision, digest, counts and source authority for that integration.

Inventory `next_page` describes source enumeration only. `pending_work_ids` and
`capture_resume_page` retain the unselected works from the same page. A following
packet must restore the approved new child and resume that capture page before
advancing the source cursor. Do not treat the five-work cap as acquisition of the
other 95 candidates or a completed historical partition.

Validation uses affected test files during edits, one full pre-PR harness for the
coherent candidate, and required hosted checks. Reuse unchanged passing receipts;
repeat only changed gates or observed failures. Native capture, publication and
independent pinned recovery remain distinct acceptance evidence.
