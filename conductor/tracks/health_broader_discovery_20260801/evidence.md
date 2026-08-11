# Evidence

Live paired evidence is recorded in
`../../../evidence/health-discovery-20260811.json` and its Markdown companion.
The bounded run observed 815 unique datasets, including 77 health-group
members. A full rerun reconciled all 815 as unchanged. Ten raw response pages
remain local under ignored `build/live` storage and are individually hash-linked
by the two manifests. No resource payload was captured or published.

This is reproducible query evidence, not an unsupported completeness claim.
All 815 records remain payload-ineligible in this metadata-only track; 101 lack
catalogue licence metadata and are explicitly decision-required.

## Completion assurance - 2026-08-11

| Evidence | State | Detail |
| --- | --- | --- |
| Shared executor | verified | `321b8fd`; POST JSON and GET query encoding share retries, timeout, byte limits, hashing, and error handling |
| Evidence receipt | verified | `7ecea55`; paired JSON/Markdown receipt committed after the initial hosted missing-file failure |
| Hosted implementation | passed | PR #63 CI `31475571237`, CodeQL `31475571272`, and workflow policy `31475571231` succeeded |
| Complete Windows gate | passed | `scripts/validate.ps1`; 343 tests, 95.77% overall branch-aware coverage, schemas and all supply-chain stages passed in 455.9 seconds |
| Critical Track 12 coverage | passed | `health_discovery.py` and `health_scope.py`: 100% line and branch coverage across 20 focused tests |
| Mutation assurance | passed | resource policy 8/8, versioning 3/3, redundancy 6/6, and ArchiveBox 9/9 mutants killed |
| Payload capture | prohibited/not run | metadata-only boundary retained |
| Publication | prohibited/not run | no Hugging Face upload, Zenodo deposition, or DOI action |

The first PR run `31475190606` failed because the newly referenced evidence
file was absent from that revision. This was a repository packaging defect,
not a catalogue or transport failure; commit `7ecea55` added the evidence and
the next hosted run passed. The historical failure remains recorded.
