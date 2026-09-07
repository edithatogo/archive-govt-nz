# Canonical child-manifest reconciliation — 2026-09-07

Isolated from G `7b1959cf0f1b23b80984d8cafafac5767547f210` on
`codex/foi-child-manifests-20260907`. P4.1/P4.2/P4.4 local prerequisite only;
no phase, rights, publication or programme acceptance is asserted.

## Contract and scope review

The existing Hub interface suffices for bounded metadata reconciliation: public
identity, exact-revision sizes and anonymous bounded downloads. No new Hub API,
transport implementation, remote call or raw-object download was introduced.
The new dedicated `foi_child_manifests` module reuses release pointer/table
contracts, package canonical serialization/safe paths and the existing v2 package
schema. Packaged copies of the two existing JSON schemas support installed code;
tests require exact byte parity with the repository schema originals.

Canonical publication now requires each named child to have a valid v2 package
manifest. It reads `current.json` at the source's **catalogue-pinned hf_revision**,
not at the observed latest head. The pointer must name the expected repository,
an immutable snapshot revision, a manifest digest and the exact five v2 tables.
The referenced manifest is read in that same repository at the pointer's exact
snapshot revision, SHA-256 checked, schema validated (including formats), and
joined to the exact source ID/country. All twelve file paths must occur exactly
once; arbitrary paths and duplicate JSON members fail closed.

An additive `child-manifests.json` records source/repository identity, immutable
pointer and snapshot revisions, pointer/manifest hashes, manifest bytes and table
references. The catalogue manifest hashes this file. Existing canonical registry,
coverage and source rows remain byte-identical; only the delivery manifest changes
and the child reference file is added. Restore-before-promotion and conditional
commits remain in the existing `publish_snapshot` implementation.

**This is manifest metadata verification, not `verify_package` or raw restore.**
The latter requires fetching and validating every raw object and is deliberately
not invoked here. Manifest file hashes are references, not proof those payloads
exist or were downloaded. Rights remain separate; original manifest declarations
are not changed into approval. Source/raw coverage and schedules are unchanged.

## Bounds and compatibility

- At most 23 child repositories, with unique source/repository identities.
- At most two document downloads per child: 4,096-byte pointer and 262,144-byte
  manifest caps, at most 6,123,520 document bytes for 23 children. Exact size is
  checked before download and on received bytes. JSON is parsed only after this
  check; hashes and schemas precede binding.
- Bounds concern document counts/bytes. Transport timeout/retry behavior remains
  the existing Hub implementation's responsibility; this is not a new global
  network deadline or hostile-filesystem sandbox.
- A missing, forged, oversized, unsupported-schema or mismatched child fails
  before any global snapshot upload/pointer promotion. Existing catalogue bytes
  are preserved; no legacy-manifest fallback silently weakens canonical mode.
- Default/v1 publication and raw publication decision guards are unchanged.
  The explicit canonical path is intentionally stricter. Old pinned child
  revisions without these contracts will block; no live child state was observed
  or assumed, and pins were not advanced to make tests or publication pass.

## Focused validation and review

Final result: 174 passed, including three static hash/source/repository guard
mutants killed; child module and publisher each have 100% statement/branch
coverage. Locked offline Ruff format/lint and BasedPyright pass. See the paired
[machine validation receipt](child-manifest-reconciliation-20260907.json).

TDD red: missing dedicated module, then canonical publication lacked the expected
child-reference file/manifest binding. Synthetic fixtures cover all 23 actual
catalogue identities but **do not represent observations of those repositories**.
Tests cover exact revision selection, hash/schema/source/country/table bindings,
private/wrong targets, duplicate JSON/files/repositories, missing manifests,
unsafe paths, typed limits and download-size mismatch. End-to-end MemoryHub tests
prove failed child verification preserves an existing v1 catalogue byte-for-byte
and performs no global upload. Successful canonical retries remain idempotent.

The final test invocation uses a fresh isolated uv environment with no PYTHONPATH
or root-namespace masking. Shared fixtures load by absolute file path, not a
`tests` namespace import. The parent-owned phase-validator import correction is
not included or modified by this commit.

```sh
UV_OFFLINE=true uv run --locked pytest tests/test_foi_child_manifests.py tests/test_foi_child_manifest_mutants.py tests/test_foi_delivery.py tests/test_foi_package.py tests/test_publish_foi_cli.py -q --cov=archive_govt_nz.foi_child_manifests --cov=archive_govt_nz.foi_publication --cov-report=term-missing
```

Conductor implement/review guided the API sufficiency review, TDD and scoped
authority audit. Parent owns independent review and full integration checks.
No new raw approval, live readback, publication, activation, plan closure or full
harness occurred. Follow-up live evidence, if separately authorized, must retain
missing/unsupported child failures rather than silently replacing historical pins.
