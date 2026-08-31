# Prompt 03: final donor operational state

Verification attempt 02 passed. The authenticated ZIP contains 500 seed work IDs,
500 manifest records, 500 processed IDs and 500 distinct CAS objects. These are
measured counts, not constants in the verifier. Every object passed SHA-256,
BLAKE3, byte-size and path-identity checks. The independently recomputed semantic
manifest root and seed digest match the audited pins. Weekly reconciliation has
zero mismatches. No missing or unreferenced CAS objects were found.

## Authority and revisions

- Target baseline: `113bac597cb95ce7aba5c877da4cffde6a0346cc`.
  The prompt supplied no audited target SHA for comparison.
- Archived donor final head: `b40587f1b1aec7356a0f623916fcc8212397d283`.
- Donor workflow's target execution pin: `d9abc05fa648f8b2049fb443477bc8f97691cf7f`.
- Donor run: [32487942675](https://github.com/edithatogo/corpus-legislation-nz/actions/runs/32487942675).
- Artifact ID: `9450742423`, `target-legislation-weekly-32487942675`.
- Outer SHA-256: `1975e473793fd701b81b53a7f6fd696bbeaa257b41bdc55250f064a21ad9e54e`.
- Seed SHA-256: `59923176fa34796d7673a20b880af9abe5520fe484595edb220f2bbc0e3b33e7`.
- Semantic manifest SHA-256: `a32dc371a1a47ae30a4afd58a9cbde2a439f3536d7705eb776e0fa68b4cd16db`.

`github-metadata.json` records live retention: not expired at observation,
expiry `2026-11-19T13:38:58Z`. Retention is an observation, not a future guarantee.
The ZIP was acquired with authenticated GitHub artifact API access and its outer
digest verified before extraction. No signed URL or credentials were retained.
`acquisition.json` is the historical pre-extraction receipt.

## Verification contract and failed attempt

The bounded offline tool is `tools/verify_final_donor_state.py`; focused synthetic,
negative and property tests are `tests/tools/test_verify_final_donor_state.py`.
It rejects mismatched metadata, unsafe/duplicate ZIP paths, special members,
excessive expansion, duplicate JSON keys, inconsistent roots/identities/receipts,
missing objects and orphan objects. A fresh external quarantine and output
directory are required. It emits a stable first-failure ledger and never repairs
source records. Maximum ZIP size is 64 MiB, expanded size 128 MiB, member size
64 MiB and member count 4096. Metadata must come from authenticated GitHub and
expectations must be independently pinned; the offline tool cannot authenticate
an arbitrary caller-supplied metadata file by itself.

`verification-01` remains failed with `manifestation_path`. That was an incorrect
verifier assumption, not an established source defect: the donor stores 348 dated
HTML-page manifestation URIs and 152 explicit-format URIs. The pinned producer
keeps a preferred canonical URI separately from the fetched manifestation.
`verifier-correction.json` records the source pin and correction. Attempt 02
requires both URIs to identify the same official work and dated expression while
allowing different preferred/retrieved formats. No donor bytes changed.

All 500 records have no `media_type` field; the report therefore records zero
media-type declarations checked. Optional declarations are validated when present.
No inferred media classification is presented as a donor declaration. Hash and
schema verification is not legal-text semantic validation or source-rights approval.

Lineage receipts bind the prior canary run `32487223314` and artifact name to this
weekly package. `parent-run-readback.json` independently records that run's GitHub
metadata. The parent artifact was not downloaded, so this does not establish
byte-for-byte parent payload reconstruction. Initial and canary receipts retained
inside this unchanged-root package also pass their counts, roots and reconciliation
checks. This verification profile is intentionally specific to this audited state.

## Prompt 04 handoff

Use only `verification-02/final-donor-state-verification.json` (status `passed`)
and `verification-02/prompt04-inventory.json` (eligible `true`). The latter lists
all 511 files as path components with byte sizes and SHA-256 identities. Its hash
is `61d054a24e39792cdef21783c68c4f5bb31903139608fc5854cdd66e9b68aa7e`;
the verification receipt hash is
`46e193732d5a798a33a8647f58f7d5962dc449e9cde0148a51250073e6272e97`.
`verification-02/SHA256SUMS` binds both JSON outputs and the readable report.

Local package location:
`/Volumes/PortableSSD/Quarantine/archive-govt-nz/final-donor-state-9450742423/artifact.zip`.
Verified extraction is the sibling `candidate-02` directory.
`quarantine-readback.json` records independent disk readback of all 511 files.
The ZIP and extracted files are read-only; permissions are not WORM storage.
The immutable identity is the content digest. Rehash the ZIP and every inventory
entry before Prompt 04 consumption. Do not consume `candidate-01` or attempt 01.

This handoff supplies verified input only. It does not authorize or perform a
canonical merge, publication, donor unarchival, rights clearance, HF dataset,
Zenodo DOI, or changes to the independent `edithatogo/legislation` product.
Corpus bytes are outside Git; committed evidence contains only metadata,
identifiers, inventories and verification receipts. Prompt 04 must also respect
its separate prerequisite lineage issue and its own acceptance gates.

## Reproduction

From the implementation checkout, use new (nonexistent) quarantine and output
paths; never overwrite either historical attempt:

```sh
uv run --locked python tools/verify_final_donor_state.py \
  --archive /absolute/path/to/authenticated-artifact.zip \
  --metadata evidence/migrations/corpus-legislation-nz/final-donor-state/github-metadata.json \
  --expectations evidence/migrations/corpus-legislation-nz/final-donor-state/expectations.json \
  --quarantine /absolute/external/path/to/new-quarantine \
  --output /absolute/path/to/new-verification-output
```

For focused coverage, configure coverage with `branch = true` and
`include = */tools/verify_final_donor_state.py` in its run section, and
`fail_under = 100` in its report section. Run the focused test file with
`--cov --cov-config=<that configuration> --cov-report=term-missing`.
The mutation receipt specifies each targeted guard and pytest selector. To
reproduce, copy the verifier into an isolated project/tools directory, replace
`if not condition:` with a guard that bypasses only the named invariant, and
point `DONOR_VERIFIER_UNDER_TEST` at that copy. Run the recorded selector with
`--no-cov --maxfail=1`. Only assertion failures count as killed mutants;
collection and infrastructure failures do not. Never mutate the delivery source.

## Resumed delivery

`resume-verification.json` supersedes the earlier local-quality blockage. The full native harness now passes, and the recovered drive package matches every recorded hash. `delivery-base.json` records rebase onto d6bc0c96c44488a75b7e98bd9cb95591eeb97a38 without verifier or artifact changes. No canonical state import or publication occurred. Final delivery remains subject to hosted checks on the final PR head.
