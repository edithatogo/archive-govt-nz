# Global FOI public archive — approved specification

Status: approved by the user on 2026-08-30; see [approval](./approval.json).
No implementation, publication or controller cutover is claimed by track initialization.

## Outcome

Provide an operational, country-indexed public FOI archive with three separately
verifiable products: a source catalogue, an object-level metadata index, and
byte-preserved raw source objects. Reuse the existing capture and preservation
components. Repair current automation before migrating responsibilities.

The user explicitly requests public Hugging Face archiving. Record this as
publication intent and authority within the agreed scope; do not ask again for
routine publication solely because it is external. This does not establish
third-party redistribution rights, resolve privacy restrictions, supply missing
credentials, or authorize donor deletion. Unclear source dispositions stay blocked.

## Ownership decision: DEC-FOI-001

The user approved `archive-govt-nz` as the orchestration, indexing, raw-storage
and public-publication owner, with `fyi-cli` retained as the source-transport
adapter and `foi-process` as the downstream consumer. Approval was recorded on
2026-08-30 in [approval.json](./approval.json), including hashes of the reviewed
draft. The request also authorized considering additional improvements.

This decision supersedes the old federation-only ownership boundary for FOI
capabilities. It does not authorize wholesale merging/deletion of donor history.
The prior WONT-1 is retained with a dated supersession note. Preserve all existing
public dataset identities and the active donor until hosted parity, safe state
handoff and public restore permit a controlled transfer. There must never be two
active source schedulers. Donor retirement remains out of scope.

## Scope and requirements

The normative MoSCoW requirements and acceptance criteria are in
[requirements.md](./requirements.md). Scope includes:

- Recovery of the NZ lease/reservation failure and HF JSON-summary failure.
- One versioned country/territory/jurisdiction/source registry; reconcile the
  current 23 runtime instances, 29 source sites and 42 jurisdiction targets.
- Expand discovery beyond those seeds to every country in a pinned country
  universe. Represent territories and supranational jurisdictions distinctly;
  a missing adapter or source is an explicit disposition, not an absent row.
- Faithful original metadata, request pages, correspondence, decisions,
  attachments and relevant HTTP/WARC evidence; historical CDX indexes remain
  discovery evidence and cannot substitute for captured bytes.
- Public source index and safe per-object metadata index, revision-pinned raw
  object packages, rights/takedown handling, anonymous remote restoration.
- Bounded incremental and historical acquisition, durable checkpoints,
  interruption recovery, monitoring, and country-by-country activation.

## Review refinements

[Recommendations](./recommendations.md) makes the existing recovery, integrity,
security and resource requirements concrete: artifact-expiry protection,
revision-consistent catalogue promotion, cross-repository owner fencing,
clean-room recovery, hostile-payload quarantine, and bounded growth/retries.
These introduce no new service, publication destination or paid infrastructure.
Acceptance checks and tasks below cover these refinements under AC05–AC12.

## Acceptance and completion

System readiness requires all Must criteria, automated negative-path tests,
repository gates, successful hosted repair runs, a verified public NZ slice,
and a second eligible instance proving isolation and generality. In addition,
every country must have a reviewed source disposition and every approved,
supported source must have a scheduled acquisition path and a visible backlog.
A denied/unknown source can be honestly blocked without breaking the scheduler;
it cannot count as fully captured. World-corpus completion is a separate metric
and remains false while any in-scope capture or remote verification gap exists.

Country/site snapshot completeness requires an enumerated, revision-bound
population and reconciliation of requests, pages, attachments, revisions and
stored raw hashes. Unknown denominators produce null percentages. Report
inaccessible, excluded, restricted, failed and pending items separately; never
shrink denominators silently to report 100 percent.

## Non-functional constraints

Non-interactive CLI; Linux hosted execution and supported macOS validation;
per-origin pacing, capped concurrency and cost/storage forecasts; deterministic
indexes; content addressing; bounded retries; no payloads in source Git; no
secret or unapproved personal-data logging. Reuse the approved Python/JSON
Schema/Parquet/CAS/Hugging Face stack before introducing infrastructure.

## External gates

- Repository ownership and specification/plan approval: satisfied by approval.json.
- Per-source access, retention, redistribution, privacy and takedown evidence.
- Working least-privilege credentials and platform storage constraints.
- Hosted parity, anonymous restore and recovery evidence before cutover.
- Donor archival/deletion, new DOI releases and paid capacity are out of scope.

## Authoritative inputs

- `AGENTS.md`, `conductor/product.md`, `product-guidelines.md`, `tech-stack.md`,
  `workflow.md`, `autonomy.md`, and `autonomy-policy.json` at receiver baseline
  `5eda36dd2d204a6a859100f913b411c44a08bf62` (all paths relative to `conductor/`
  except `AGENTS.md`).
- `conductor/tracks/post_consolidation_riopa_interoperability_20260817/requirements.md`:
  WONT-1 carries the dated FOI ownership supersession; donor-history preservation remains in force.
- `conductor/archive/common_publication_distribution_hub_20260823/spec.md`,
  `src/archive_govt_nz/bronze/`, `src/archive_govt_nz/dist/`, and
  `schemas/publication-manifest-v2.schema.json`: reuse candidates, not operational proof.
- Donor `https://github.com/edithatogo/fyi-archive` at
  `cba7b0dec2734bdc9ff51c69610fc55cb1fc5aa1`:
  `src/fyi_archive/config/archive_instances.json`,
  `configs/archive_source_graph.json`, `configs/jurisdiction_archive_targets.json`,
  `src/fyi_archive/nz_backfill_state.py`, `.github/workflows/hf_sync.yml`.
- Existing donor issues #196, #365, #370, #377 and #378: preserve their scope and
  evidence; parent closure alone is not satisfaction of open child criteria.
- Live baseline and failure evidence: [evidence.md](./evidence.md).
- The authoritative country list/version, source rights records, adapter release,
  and every HF revision must be pinned during Phase 0/2; none is invented here.

## Out of scope

Analysis/OCR/model training, legal conclusions, a new web frontend, donor code
history merging or deletion, unrestricted disclosure, bypassing authentication
or robots controls, and claims of exhaustive national records outside the
reviewed public FOI source universe.
