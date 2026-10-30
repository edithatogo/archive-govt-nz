# NZ legal and parliamentary archives: coverage audit

Audit date: 31 October 2026, Australia/Brisbane. This is an audit and completion
plan, not a capture, publication or activation instruction.

## Findings

The archives contain useful preserved material, but none establishes complete
coverage of NZ legislation, case law or Parliament. The greatest immediately
reusable capability is the committee-report worker. Legislation needs broader
enumeration and historical-version capture. General case law needs a qualified
source-to-original-document pipeline; notices and listing rows cannot fill that
gap.

| Collection | What is evidenced | Principal gap |
| --- | --- | --- |
| Canonical legislation | Pinned continuation ZIP downloaded anonymously; outer size/hash and every internal CAS object's SHA-256 checked. 904 records for 552 works. See the [readback](../evidence/coverage-audit/20261031/legislation-recovery-readback.json). | The actual work population is **453 local Acts, 52 public Acts and 47 imperial Acts**. No private/provincial Acts, Bills, amendment papers or secondary legislation occur in this selected state. Version/format coverage is also incomplete. |
| Historical legislation dataset | Separate superseded publication exists, with 6,788 files at the observed revision. | Reconcile historical identities, versions and payload hashes against canonical custody before treating any as additional coverage. File counts are not work counts. |
| Modern Hansard | Published card reports **193,922 document rows**, from eight DocumentsDB CSV files, Parliaments 47–54. Normalized Parquet exists. | No official sitting/document census reconciled to this extract. Source ZIP is dated 2024-09-06; fresh 2025–26 coverage is unproven. Rows are documents, not verified speech turns. |
| Historical Hansard | Hathi collection has **510 inventory records**; main legacy dataset has metadata/manifests, not 510 preserved text volumes. Related research-fulltext inventory contains **one `.txt` under `texts/`**. | Reconcile volume chronology, acquire eligible originals/text and prove per-volume custody. 141 inventory volume numbers need enrichment. Restricted routes remain separate. |
| Select committee reports | Live one-row search reports **10,970** results. Hash-verified frozen checkpoint contains **949 report identities**: 947 captured, one metadata-only, one failed/access-held. Ledger records 37 verified batches and 1,041 distinct payload hashes. Every captured identity has verified batch membership. | Roughly 10,021 source identities remain outside the observed identity count; this subtraction is a planning estimate, not an exact anti-join. Historical cursor is page 95, size 10; scheduled job uses recent-only mode. |
| Submissions and official advice | Generic discovery/capture components exist; broad collection remains unqualified. | Source endpoint, stable identities, rights per item and attachment completeness. Parliament's general permission excludes submissions and most advice. |
| Other parliamentary business | Some material may occur incidentally in report/Hansard records. | No evidenced complete dedicated archive of written questions/answers, petitions/responses, papers presented, Order Papers, Journals, daily progress, bill-context pages or Library publications. |
| Courts public notices | Manifest reports **4,206 normalized rows**: 3,457 RSS, 689 X, 49 Bluesky, ten website and one email record. | No evidence these are 4,206 full judgments. Manifest includes an explicitly named email-ingress smoke record; exclude it from empirical coverage. Latest source timestamps mostly stop in June 2026 or earlier. |
| Medico-legal/coronial | Public descriptive snapshot and source adapters exist in a separate repository. | Published correction says earlier coronial completeness referenced synthetic fixtures. Current snapshot is observations/index metadata, not a complete coronial case-text corpus. It cannot stand in for general case law. |

All dataset revisions and gates are frozen in [datasets.json](../evidence/coverage-audit/20261031/datasets.json)
and the [Hathi inventory summary](../evidence/coverage-audit/20261031/hathi-summary.json).
The continuation contains only 556 distinct expression identities for 552 works;
904 records must not be interpreted as 904 different Acts or versions.
The original 552-record legislation publication and later 904-record continuation
represent related states of the same 552-work population; do not add them.

## Existing pipelines: what can be reused

### Legislation

`domains/legislation/corpus.py`, `api.py`, `accounting.py`, `checkpoints.py` and
the parent/merge tools provide canonical identities, conditional requests,
CAS, manifests, reconciliation, authenticated parent restoration and isolated
child-state merging. Explicit nested work targets can describe expressions and
manifestations. Reuse these rather than creating another archive identity.

However, `_enrich_work_identity()` takes `versions[0]`, builds **one expression**,
and `_primary_manifestation()` admits only XML/HTML. Normal discovery therefore
does not acquire every historical version, PDFs or original scans. XML/HTML are
preservation fallbacks, not a promise to retain all formats. A PDF-only agency
instrument needs a supported capture/normalization path, not a fabricated XML URL.
`iter_search_works()` reads page one only; `iter_work_versions()` makes one
response request and does not follow version pagination. Prove response exhaustion
before using either for complete enumeration.

The exact-inventory workflow revalidates a governed **500-work seed**. It cannot
discover the missing national corpus. The weekly scope searches titles for
`enacted 2026` and `amendment 2026`, starts at page one, allows four pages per
query and caps candidates at 50. It stages an isolated child for later exclusive
merge; it does not automatically update Hugging Face. Its 29 October successful
[manual run](https://github.com/edithatogo/archive-govt-nz/actions/runs/40951408482)
does not prove broad coverage or natural weekly recurrence.

**Query-contract mismatch requiring qualification:** the committed freshness scope
passes `public`, `local`, `private`, `secondary` as `legislation_type`, and sends
`sort=work_id`. The current [official API documentation](https://api.legislation.govt.nz/docs/)
documents legislation types `act`, `bill`, `amendment_paper`,
`secondary_legislation`, Act subtypes through `act_type`, and `sort_by` values
such as `year_asc` and `most_recently_updated`. These do not match. A zero-result
run must not be treated as proof of freshness until representative positive
controls and actual server filter/order behavior pass. This audit made one
unauthenticated bounded request (HTTP 401), did not recover or transfer an API key,
and does not assert how the authenticated server handles unsupported parameters.

The published card/registry still foreground the original 552-record package;
the selected parent is the later continuation. Publish a clear current-state
pointer and reconcile cards/registry with accepted manifests after integration.
The repository's four-dimension completion evaluator describes migration,
recoverability and publication identity; its `complete` result is **not national
corpus completeness**. The 33,693 search-derived candidates are also not an
authoritative denominator or an exact missing-work count.

### Parliament reports and other collections

`parliament/reports.py` qualifies the current committee-report API;
`pipeline.py`, `worker.py`, `publication.py`, and `hosted_*` provide durable
candidate shards, bounded streaming capture, rights decisions, immutable batches,
remote verification, leases, checkpoint recovery, cooldowns and failure holds.
Reuse these components with collection-specific source contracts.

The existing destination is
[`archive-govt-nz-global/parliament`](https://huggingface.co/datasets/edithatogo/archive-govt-nz-global/tree/main/parliament).
The frozen checkpoint is generation 945, cycle 42, enabled, with no current
owner/lease at observation. This audit did not claim that lease. The latest
[scheduled run receipt](https://github.com/edithatogo/archive-govt-nz/actions/runs/41057634651)
records bounded completion, 947 captured, zero pending and one reviewed access
hold. This evidences a real scheduled invocation, not guaranteed hourly execution
or finished historical coverage.

The configured cron is hourly, but the actual observed recent runs are separated
by hours. Both scheduled and manual jobs pass `--recent-only`, restricting new
discovery to the first ten ten-record pages. `hosted.py` supports historical and
reconciliation partitions when recent-only is false, but changing the live
operation belongs to its existing writer. At ten records per batch, a roughly
10,021-record historical remainder needs about 1,003 net-new batches before
duplicates, source drift, missing attachments and failures. This is a work-unit
estimate, not a duration promise.

The public catalogue receipt still describes **four batches / 21 rows**, whereas
the current checkpoint ledger has 37 verified batches. Rebuild the catalogue
from immutable accepted batches after a consistent snapshot; do not assume its
current card/catalogue describes the whole published archive. Keep API-response
objects, report PDFs, observations, identities and publication batches distinct.

The generic legacy parser and XML Hansard adapter are reusable code, not live
endpoint qualification. Hansard parsing supplies fallback identifiers/dates;
require authoritative source identity/date before production admission. The
separate `corpus-nz-hansard` workflows rebuild the supplied ZIP, not a verified
current sitting census. Its monthly publication defaults to dry-run, and the
inspected publication/video workflows still select Python 3.14. Qualify those
lanes on repo-local 3.15.1 before adopting them under current project requirements.
Video workflow output artifacts are not evidence of full media preserved on HF.

Historical Hansard has related Hathi inventory/fulltext/feature/analytics datasets.
The frozen blocker reports describe static-host/SSH/rsync prerequisites, and the
fulltext inventory shows only one interim Internet Archive text. Those are
historical blocker statements, not a live authentication audit. Feature manifests
and shell staging recipes do not prove extracted-feature payloads are present.
Recheck exact existing access before declaring a route unavailable or requesting
new access. Do not equate metadata rights codes with permission to rehost scans.

### Case law

The local `CourtsPublicNoticesIngestor` can preserve supplied bytes and metadata;
it does not enumerate courts or fetch linked judgments. Feed and web infrastructure
can support discovery, hashing and capture, but a judgment-specific identity,
version, restriction and attachment contract is needed.

The separate `corpus-cases-medilegal-nz` repository has MoJ courts, HDC, HPDT,
tribunal, ERA and other adapters plus HF synchronization. Inspected MoJ/HDC
adapters fetch one configured listing page and parse listing records; that alone
does not establish paginated discovery or original judgment-body capture. Its
daily matrix includes HDC, HPDT, MoJ tribunals, ERA and teachers, **not MoJ courts**,
and selects Python 3.12. Reuse only after source-level tests and 3.15.1 runtime
qualification. The local HDC source-set is disabled, with publication disabled.
Its existence does not establish a running HDC archive.

The [Courts' own source guide](https://www.courtsofnz.govt.nz/judgments) identifies
JDO for Supreme Court judgments, Court of Appeal from 2003 and High Court from
2005; District Court publishes a representative selection; historical cases and
special jurisdictions require additional sources. Judgments of public interest
remain on that website for only 90 days. Prioritize capturing eligible linked
originals from current listings, then backfill JDO and other courts. Do not use
feed completeness as a judgment denominator. This audit did not crawl JDO,
NZLII, District Court or tribunal databases or qualify bulk reuse of their content.

## Completion plan, in order

| Priority / packet | Concrete work | Acceptance evidence |
| --- | --- | --- |
| P0 — Coverage accounting | Define national scope by collection, court/type, dates, version and format. Add per-source discovered/eligible/captured/failed/held/published counts, separate from migration status. Exclude synthetic/smoke observations. | Frozen upstream inventories and deterministic anti-joins to pinned published manifests; unknown denominators stay unknown. |
| P0 — Legislation query qualification | Correct/version API type/subtype and ordering contracts; positive controls for Acts, Bills, amendment papers and both secondary publishers. Add bounded pagination and durable continuation across partitions. | Saved sanitized request/response contracts, stable-ID deduplication, terminal-page proof and known-positive results under the existing authorized key. |
| P1 — Report historical completion | Existing native owner enables bounded historical/recent/reconciliation rotation, preserving checkpoint and holds. Reconcile all 10,970 current report identities; revisit metadata-only, changed and late attachments. Rebuild the public catalogue. | Complete identity anti-join; all eligible originals pinned and hash-verified; exceptions itemized; clean cold restore; subsequent natural schedule captures a new/revised item. |
| P1 — Legislation backfill | Reconcile historical dataset into canonical identities, then enumerate all Act subtypes, Bills, amendment papers and secondary legislation by status/publisher. Enumerate all versions and selected original formats, including PDFs/scans. | Each expected work/version/format has a captured original or specific exception. Verified exclusive merge, new durable package, public pinned readback and current pointer. |
| P1 — Judgment acquisition pilot | Qualify read-only JDO and Courts listing/document contracts; enumerate one court/year, capture original PDF/HTML, citation, court, date, version/hash and restrictions. Keep notices separately typed. | Known-positive cases found; pagination complete for pilot; original bytes recover from HF at pinned revision; citation deduplication and withdrawal/replacement handling demonstrated. |
| P2 — Expand case law | Supreme Court, CA, HC; then District and specialist courts/tribunals; historical sources as distinct partitions. Reconcile medico-legal records without importing synthetic completeness claims. | Per-court/year source inventory and original-document anti-join. Explicit unavailable/nonpublic/suppressed cases; no claim to all court files or unpublished decisions. |
| P2 — Hansard reconciliation | Join the DocumentsDB extract to official sitting/document lists; backfill missing Parliaments/dates and post-extract material. Map Hathi volumes to official chronology and qualified public overlap sources. | Per-sitting/per-volume coverage, original-to-derived hashes, missingness ledger, published rebuild on 3.15.1. Explicit gaps between historic volumes and modern extract. |
| P2 — Additional parliamentary records | Written Q&A, petitions/responses, Journals, Order Papers, daily progress, Library material and bill-context relationships, each with its own source/rights contract. Separate parliamentary papers by originating publisher. | One completed-item pilot per shape, all linked attachments accounted for, retry/recovery and relationship reconstruction, then partitioned backfill. |
| P3 — Rights-dependent collections/media | Submissions, third-party advice/papers and audiovisual material only under specific source permissions and applicable terms. Preserve safe catalogue metadata for pending items where permitted. | Object-specific redistribution basis and approved publication path; unresolved rights remain visible exceptions. |

Use existing canonical HF identities. Do not merge historical/DOI snapshots into
living datasets by overwriting provenance, change gates, or create another dataset
just to make counts appear complete. New collection namespaces/destinations need
an explicit integration decision by the native owner. Preserve originals before
OCR/text extraction; derivative failures must not erase originals.

“Complete” should mean **all publicly available, eligible material in a declared
source/date/version scope is either remotely verified or has an explicit unresolved
exception**, plus a working freshness process. It cannot mean all unpublished,
suppressed or otherwise inaccessible court records. Parliament's
[current reuse statement](https://www.parliament.nz/Copyright) excludes submissions,
most advice and most parliamentary papers from its general permission; footage
has separate terms. Public visibility alone does not resolve those exceptions.

## Audit provenance and limits

- Chat: `01a18d6e-759f-76c0-85cd-03413c023c8e`.
- Owned branch: `codex/legal-coverage-audit-20261031`; app-managed worktree:
  `/Users/doughnut/.codex/worktrees/legal-coverage-audit/archive-govt-nz`.
- Audited repository baseline: `495a54d9` (`origin/main` at inspection).
- Owned paths: this report and `evidence/coverage-audit/20261031/` only. The
  original shared checkout's dirty Health/source-test work was left intact.
- Native scope: read-only public HF metadata/pinned downloads, GitHub workflow
  reads, one public report search and one unauthenticated legislation probe.
  No native writer, shared authentication, schedules, holds or publication changed.
- Evidence: [manifest](../evidence/coverage-audit/20261031/audit-manifest.json),
  [report checkpoint summary](../evidence/coverage-audit/20261031/parliament-summary.json),
  [scheduled receipt](../evidence/coverage-audit/20261031/parliament-run-41057634651.json),
  [court aggregate](../evidence/coverage-audit/20261031/courts-summary.json).
- Downloaded legislation package and all 904 CAS hashes checked. Report checkpoint
  compressed SHA-256 checked; one manifest, its API object, and a separate original
  PDF sampled and hash-checked. This is not a full remote-object recovery audit.
- Hansard row totals are published-manifest/card claims, not a fresh scan of all
  Parquet rows. Historical dataset counts are not a deduplicated national census.
- No tests were changed or native jobs run. No PR is opened; the required full
  validation harness remains necessary before any future PR.
- Next operation: repository/native integrator selects a bounded implementation
  packet from the table, using the existing Parliament writer for live report
  changes. This audit lane owns no capture or publication operation.
