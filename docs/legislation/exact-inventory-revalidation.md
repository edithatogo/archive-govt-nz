# Exact-inventory revalidation lane

The `exact-inventory.yml` workflow is the target-owned custody and live
revalidation lane for seed `historical-work-ids-0001`. It is manual and processes
the registry-verified 500 IDs exactly. It does not search, schedule itself,
bootstrap empty state, publish data, or prove that Prompt 13 has run.

An operator must provide a unique batch ID, explicitly confirm execution, and
select a committed JSON parent reference below `config/legislation/parents/`.
The selected parent must itself declare the same governed seed. The Prompt 08
action authenticates hosted metadata, outer and inner fixity, parent roots, every
CAS object, and lineage before the only step that receives
`NZ_LEGISLATION_API_KEY`. Missing, expired, corrupt, differently scoped, or
unsealed state stops before source contact. There is deliberately no automatic
"latest run" selection and no fallback to empty state.

The source-set contract is
`config/source-sets/legislation-exact-inventory.yml`. It binds the stable seed ID,
500-line count, and SHA-256
`59923176fa34796d7673a20b880af9abe5520fe484595edb220f2bbc0e3b33e7`.
The runner forces source revalidation for every ID and writes the v3 accounting
receipt. A successful attempt requires all 500 works to be attempted, no skipped,
unavailable, partial, or failed dispositions, bounded retries, zero reconciliation
mismatches, fixed CAS and state limits, and a newly sealed continuation receipt.
Changed/newly preserved and unchanged/revalidated counts remain separate in the
receipt.

The workflow has read-only GitHub permissions and passes only the source API key
to acquisition. Its shared `legislation-canonical-state` concurrency group also
protects the existing discovery state writer. The job is limited to 360 minutes,
500 works, one serial acquisition stream, 4,096 CAS objects, 64 MiB CAS bytes,
128 MiB total state, and three source retries per work. These limits are
enforcement bounds, not permission
to omit an ID; exceeding one fails the run.

Every attempt retains the sanitized restoration, harvest, reconciliation, and
seed-selection receipts. A successful attempt additionally retains the complete
checkpoint, manifest, CAS, lineage, scope metadata, receipt history, and current
continuation seal for downstream Prompt 13 verification. GitHub Actions retention
is an operational cache and is not durable preservation authority.

Dispatch is outside Prompt 06. Before Prompt 13 dispatch, commit an independently
reviewed, unexpired parent reference for this workflow, confirm that the repository
secret exists, and use GitHub's manual workflow interface. A green configuration
or test run alone is not operational proof.
