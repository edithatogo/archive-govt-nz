# Daily Treasury and Vote Health preservation

The global CKAN harvest runs daily at 04:17 UTC (14:17 Brisbane). The Vote Health
publication workflow runs daily at 04:47 UTC (14:47 Brisbane), with its own CKAN
read and publisher checks. Both also support manual dispatch. GitHub may delay
scheduled starts.

The global harvest preserves original catalogue resource identity while resolving
Treasury Budget landing pages to the exact linked XLS/XLSX URLs. Historical
landing aliases use previously verified publisher page locations and recheck
those pages live. A live CC BY 4.0 link and workbook links are mandatory. Capture
also checks workbook signatures. Catalogue errors, empty discovery, no eligible
resources and zero successful captures fail the run. The old historical-evidence
fallback and inferred default licence are removed.

The health workflow owns `edithatogo/nz-health-appropriations`. Its reviewed
`config/health-publication/release.json` starts with the 27 recovered workbook
editions and their 85 published file identities. It retains CKAN discovery,
rechecks exact publisher links and licences, verifies workbook hashes, and
rebuilds Vote Health facts and lineage with the existing qualified parsers.
Changed bytes or unsupported layouts fail for qualification. This bounded scope
does not claim complete coverage of all Budget editions or the dataset's older
Gold tables.

Historical Parquet serialization can differ with the current qualified runtime.
Only exact Arrow schema, metadata and value equality permits reuse of the
checksum-verified historical bytes from the immutable baseline revision.
Duplicate fact identities, empty tables or mismatched release bytes fail.

Preparation runs without publication credentials. Its receipt is uploaded before
publication. Publication uses the existing `HF_TOKEN`, the fixed dataset target,
and a frozen parent commit. It adds missing reviewed files, refuses divergent
existing files, and records a no-change receipt without an empty commit when all
files already match. An uncertain commit retains intent and is not retried by the
command. Anonymous immutable-file readback and viewer row checks run afterwards.
A viewer error leaves publication unverified and fails the run.

To add another edition, qualify its source licence, exact bytes and parser, add
its facts and lineage to the reviewed release manifest, and validate the candidate
through normal PR checks. Fact paths cannot be overwritten. Card or metadata updates require an explicit
`replace_sha256` entry with the currently published hash, reviewed alongside the
new content. The frozen parent guard still applies to every update.

The NAS recovery archive stays retained. A successful workflow covers only the
selected release and does not establish that all unique recovery evidence is
preserved elsewhere. No workflow has archive-deletion capability.

## Initial operational evidence

On 8 November 2026, CKAN's bounded Budget query succeeded from the local runner.
Treasury returned HTTP 403 for the first exact publisher page, so live preparation
stopped before any publication. The scheduled workflow must pass from GitHub,
including anonymous readback and viewer checks, before it is called operationally
verified. Local source replay and hosted execution are distinct evidence.

Local replay of all 27 sources passed, and the 85 release files matched their
immutable published hashes. All 11 supplement viewer configurations returned
HTTP 200 with matching full row counts. The receipt is retained in
`config/health-publication/qualification.json`. The Budget 2025 raw transport
witnesses preserve manifest-derived record identities after exact raw schema,
metadata and value parity.
