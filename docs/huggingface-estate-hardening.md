# Hugging Face archive estate hardening — 26 October 2026

Scope: the 44 datasets maintained/referenced by this repository and four related public collections. This is not an audit of unrelated model-training, biomedical or private repositories in the account. Public metadata changes preserve originals, repository identities, DOI roles and existing access gates.

## Native changes and readback

- All 44 dataset cards validated through Hugging Face's native metadata validator before upload. Cards were committed against observed parent revisions and downloaded at the resulting pinned revisions for SHA256 comparison. Forty-two used anonymous downloads; the two already-gated datasets used authenticated byte verification plus anonymous public metadata readback.
- Corrected the global card's stale zero counts, unsupported size/task assertions, official-publisher implication and blanket CC BY statement. Source-specific rights, exclusions, coverage, attribution, contact, citation, version pinning and recovery are explicit.
- Added a public Parliament guide, rights file and viewer catalogue: four reconciled batches, 21 catalogue rows, ten distinct original payload hashes. Every referenced manifest and object was anonymously downloaded and checked. Metadata rows and overlapping pilot versions are not additional document coverage.
- Corrected Hansard source documentation that incorrectly said no payload despite its 536,442,492-byte ZIP. The gate remains; this metadata pass does not qualify that entire source ZIP for unrestricted distribution.
- Added explicit table configurations for compatible published files; Health's seven distinct tables have seven separate subsets. Legislation's column-order differences have compatible names/types. Existing qualified DigitalNZ, FYI and Hansard configurations are retained. Metadata/plan-only repositories explicitly disable the tabular viewer rather than manufacturing data rows.
- Completed collection membership and explanatory notes: legal/parliamentary 8 items, public-web 9, HathiTrust 5, global FOI 24. Country scaffolds, bounded captures, derived products, gated sources and frozen snapshots have distinct notes. All four collections were anonymously read back as public.

Measured file inventories identify published assets, not full-source completion. Approximately empty or metadata-only repositories remain explicitly so; no missing payloads or rights clearances were fabricated.

## Durable prevention

The default publisher preserves an existing maintained root card unless an explicit replacement card is supplied. Its fallback card reports missing counts as unknown, limits harvest counts to their own scope, removes invented size/task categories and uses source-specific rights. The estate-card generator no longer fabricates an `id:string` schema or applies a blanket licence to Hansard; it preserves the registry's CC0 metadata licence and labels architectural text as design intent.

Focused tests verify those behaviours, and the reviewed snapshot reflects the intentional wording changes. The full harness passed format, lint and types; its test stage had 8,424 passes and one expected card-snapshot mismatch. After updating that snapshot, all eleven affected tests/snapshots passed. Remaining assurance stages were resumed without rerunning unrelated tests; final receipts are recorded in the track run log.

## Viewer acceptance and remaining limits

The Parliament viewer serves all 21 rows through anonymous `first-rows` HTTP 200. Twelve of fourteen tabular repositories expose their expected configs; Health and FOI process-demo conversion remained pending at the latest readback. Conversion jobs may return the service's temporary busy response; configuration validation and readable direct Parquet files are separate from successful hosted conversion. Do not call a pending viewer accepted or repeatedly rewrite source files to work around a backend queue.

Two public repositories retain existing download gates: `nz-hansard-source-archive` and the DOI-associated `nz-legislation-corpus`. No private repository was made public, no gate was removed, no DOI identity was renamed, and no source payload was replaced. The canonical Hansard and new Parliament report distribution remain public and ungated. Submissions/advice source restrictions, full historical capture and natural schedule proof remain independent unfinished gates.

Use the [receipts linking maintained cards at pinned Hub revisions](../evidence/huggingface-hardening/20261026/) to locate exact dataset revisions and changed paths. Public collection descriptions have a 150-character Hub limit; detailed distinctions are recorded in item notes and dataset cards. Collection listing does not establish completeness or a rights grant.

Official contracts used: [dataset cards](https://huggingface.co/docs/hub/datasets-cards), [manual viewer configuration](https://huggingface.co/docs/hub/en/datasets-manual-configuration), [viewer controls](https://huggingface.co/docs/hub/en/datasets-viewer-configure), and [collection management](https://huggingface.co/docs/huggingface_hub/guides/collections).
