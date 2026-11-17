# Parliament P1 — source, authorisation, reconciliation and destination

**17 November 2026 update to #779.** This supersedes the earlier P1 hold-oriented assessment without erasing historical source observations. The project operator expressly confirms that the access/reuse issues previously treated as external restrictions **have already been addressed**, and directs implementation to proceed. Record this as an operator authorisation decision, **not** as a claim that Parliament has rewritten its general copyright statement or its publicly observed source policies.

The P1 task is now to establish and verify source identities, filters, pagination, attachment semantics and index intersections; carry forward existing source-specific provenance into each actual admission; and use the already-qualified public Hub publisher. Do not initiate another blanket policy-permission review. Continue retaining original bytes, item-specific rights provenance, released/private status, privacy treatment and verifiable publication receipts.

## Read-only source observations

The following initial-page observations were made on 17 November 2026 through the public website. These are *view observations*, not exhaustive snapshots. They are distinct from the 26 October native API and robots-policy receipts retained in [Conductor evidence](../conductor/tracks/parliament_archive_streams_20261026/evidence.md).

| Index | Source URL | First-page visible population | Scope and identity |
| --- | --- | --- | --- |
| Evidence / submissions | [Evidence listing](https://www3.parliament.nz/en/pb/sc/evidence-submissions/) | **1,194,789** displayed, 20 rows on page 1 | Released evidence, including public submissions; opaque `..._EVI_...` document identity; default newest-first observation |
| Advice | [Advice listing](https://www3.parliament.nz/en/pb/sc/advice/) | **12,221** displayed, 20 rows on page 1 | Released committee advice; opaque `..._ADV_...` document identity; default newest-first observation |
| Submissions and advice | [Combined listing](https://www3.parliament.nz/en/pb/sc/submissions-and-advice/) | **746,385** displayed, 20 rows on page 1 | Mixed categories with displayed document type and current/previous/all Parliament controls; site describes all as 47th–54th |
| New reports | [Reports index](https://selectcommittees.parliament.nz/reports?Tab=All) | **10,970** from the dated **26 October** qualified API observation, not a fresh count | New-host GUID `id`, distinct GUID `attachmentId`, `/api/data/search` POST with page/pageSize/keyword and explicit report type |

The 55th Parliament global navigation is not evidence that the separate 54th/47th–54th legacy listing filters have updated. The default index totals are not mutually comparable and **must never be summed or used as unique archived-document counts**. A reports index terminal page with missing attachments is metadata-only and not proof of historical completeness.

### Exact source-ID cross-index examples

Bounded public-page link inspection confirms two **same-permalink** matches without downloading submission/advice body content:

1. Evidence index ↔ combined index: `54SCJUST_EVI_27dd41ab-acd3-4afa-a59f-08deb151b1c7_JUST361886`. The same source identifier resolves from both index links on 17 November.
2. Advice index ↔ combined index: `54SCMAOC_ADV_116502_MAOC546`. The same source identifier resolves from both index links on 17 November.

These two matches establish that identity joins are feasible; they do **not** demonstrate a total overlap, an entire-page anti-join, full historical coverage, an attachment set or eligibility of any particular body. The sample contains only opaque IDs and index links, not submission text, personal information or third-party original bytes.

## Bounded reconciliation implementation

`src/archive_govt_nz/parliament/reconciliation.py` adds the pure `IndexSlice`/`reconcile_indexes` contract. Given three retained source-listing slices, each with view, effective filter scope, snapshot identity, source total, observed exact IDs and a separately proven terminal flag, it reports:

- Exact EVI↔combined and ADV↔combined matches, evidence-only, advice-only and combined-only identities.
- Specialist-source identity conflicts as **ambiguous**, not silently matched.
- Duplicate rows separately from distinct source IDs.
- A true full-coverage flag **only** where all three views have an equal proven scope and snapshot, counted rows match the source totals, and each has authoritative exhaustion proof.

This function reconciles **metadata only** and neither crawls sites nor stages publication. The first 17 November observations do not yet meet whole-index exhaustion/snapshot conditions; no complete anti-join or historical population is claimed. Six synthetic focused tests passed using the available local Python 3.13.5, with a pre-implementation failing import; the repo-selected 3.15.1 and full harness require separate CI/native proof. Tests do not create production source permissions.

## Source contract, authorisation and publication boundaries

- **Source access:** the operator's current direction resolves the *project-level authorisation question*. The 26 October generic `www3` robots-denial receipt remains accurate historical evidence, not a conclusion that every read-only listing/view is now unreachable. Use the authorised access route and record its specific actual response/authority in the source capture ledger. Do not evade network controls or fabricate an endpoint test.
- **Source rights:** Parliament's [published general licence](https://www.parliament.nz/Copyright) continues to describe reports as public domain, Clerk/Parliamentary Service-owned material under CC BY 4.0, and submissions/most advice outside that *general* grant. The operator confirms **separately resolved authorisation** for this work; do not misstate that as a new blanket licence from Parliament. Retain object-level basis, source/author attribution, proof URL, scope, exact SHA-256, release/withdrawal changes and personal-information controls when actually publishing.
- **Destination:** fixed existing public, ungated [`edithatogo/archive-govt-nz-global`](https://huggingface.co/datasets/edithatogo/archive-govt-nz-global/tree/main/parliament). Report objects use immutable `parliament/batches/{manifest_sha256}/manifest.json` and `.../objects/{sha256}`. Reuse the existing `NativeHub` parent-revision write path and **anonymous revision-pinned SHA-256 readback**. Existing verified report receipts do not verify future submissions/advice payloads.
- **Operational ownership:** do not reset or duplicate the active report publisher, historical cursor, worker state or cadence; no unqualified payloads or new Hub writes are produced by P1 itself. Local tests, hosted checks, source capture, Hub commit and independently verified remote publication remain distinct receipt states.

## P1 completion boundary

**Established:** operator authorisation direction; qualified existing report API/destination; initial current public index views; two direct exact-ID cross-view examples; reusable pure ID reconciliation with six focused regression tests.

**Still to verify technically:** preserved permitted source index snapshots with effective filters, page/terminal evidence and attachment identity contract; a scope-labelled anti-join over the intended historical partition rather than a two-ID sample; the repo-selected Python 3.15.1/full gate and required hosted acceptance; and any future original-body/publication receipts. None is an invitation to reopen the settled general authorisation question.

See [plan and run log](../conductor/tracks/parliament_archive_streams_20261026/index.md) and [PR #879](https://github.com/edithatogo/archive-govt-nz/pull/879).
