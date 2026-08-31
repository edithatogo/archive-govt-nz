# Durable legislation state and preservation authority

Prompt 09, issue [#321](https://github.com/edithatogo/archive-govt-nz/issues/321).
This contract makes Actions artifacts a bounded operational cache. It implements
local custody packaging and publication planning, not remote publication or the
independent Prompt 10 recovery acceptance drill.

## Decision PRESERVE-LEG-009

Select the **existing Hugging Face dataset `edithatogo/corpus-legislation-nz`**
as the planned durable authority, under `durable-state/v1/<package SHA-256>/`.
A usable custody reference must bind the dataset identity, exact Git revision,
package SHA-256, sizes and readback receipt. Never use a moving branch as proof.
This decision does not claim that the newly packaged state is already there.
No new dataset, repository, concept DOI, storage account or secret is created.

Destinations were evaluated in the required order on 2026-08-31 UTC:

1. Existing configured HF identity: metadata is reachable at revision
   `1efa35e72c378068cfb112d060bd0502497f61b1`, `private: false`, `gated: auto`.
   It matches `config/source-sets/legislation.yml`. Select a separate package
   prefix without modifying existing corpus files or dataset cards. Git revision
   and content hashes support exact readback; they do not prevent an owner or
   provider deleting history. The repository's access gate is not encryption,
   privacy protection or evidence of redistribution rights.
2. GitHub Release checkpoint: the observed cutover release and donor-backup draft
   have `immutable: false`. They cannot currently serve as provider-enforced
   immutable custody. An immutable checkpoint is a supplementary option only
   after separate settings/release authority and independent asset verification.
   No release or setting is changed here.
3. Existing Zenodo lineage: record `20592540` independently reports version DOI
   `10.5281/zenodo.20592540` and concept DOI `10.5281/zenodo.20592539`. The old
   source-set configuration calls the version DOI a concept DOI. This decision
   records the observed distinction without rewriting historical evidence or
   editing public metadata. Use the existing concept only for a meaningful future
   immutable release after an explicit gate; never mint a new concept for a
   GitHub authority change. The old DOI/configuration mismatch is a handoff.
4. Other configured archive mechanisms: local quarantine and existing GitHub
   donor backups retain originals, but are not independently verified durable
   remote custody for this exact canonical state. No suitable preconfigured
   private/encrypted payload destination has been established by this issue.

Provider basis: HF repositories are [Git repositories](https://huggingface.co/docs/hub/en/repositories)
with [storage constraints](https://huggingface.co/docs/hub/storage-limits);
GitHub [immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
require that protection to be enabled; Zenodo [versioning](https://help.zenodo.org/docs/deposit/manage-versions/)
keeps related versions within an existing lineage. These capabilities do not
constitute permission or proof of a new upload.

## Rights, retention and ownership

The current merged payload has unresolved redistribution rights. Its local
package is **payload-blocked**. Public eligibility of source identifiers or a
Crown-copyright label does not clear every payload or retained parent archive.
The entire package, including nested parent archives, stays local until a
reviewed decision covers every byte. We do not encrypt then publish blocked
payload, change repository gating, or assume that a public dataset is private.

A separate minimal metadata projection contains only package hash, state roots,
counts, an enumerated rights status and explicit non-publication/non-coverage
claims. It excludes manifest records, source URLs, checkpoints, parent archives,
local paths and free-form authority text. Its publication also needs explicit
approval; producing a dry-run plan is not that approval. Gated HF access may
limit anonymous metadata-file readback even when API metadata is visible.

Rights declarations contain a decision ID and authority commit for any
`public_approved` payload. Those fields record a claim; they do not create legal
rights or authorize the agent to upload. A future executor must authenticate the
reviewed declaration, package hash and accountable publication approval. Blocked
plans never contain a `state.zip` upload entry. Existing remote bytes are never
deleted or rewritten to repair a rights mismatch.

Retention intent is permanent for complete packages, original parent evidence,
verification receipts and failed attempts. No HF provider retention guarantee or
expiry date is inferred. Actions cache artifacts retain their own expiry and
must never be the sole copy. There is currently no separately verified remote
custody copy of this newly built package. Local media loss, owner deletion,
account loss, access-gate changes and provider failure remain risks.

`edithatogo` owns the selected identity. Ownership transfer must preserve the
existing identity/history where possible and record old/new authority, exact
revisions and hashes. Verify availability and byte equality under the receiving
owner before changing custody references or retiring a copy. Do not delete the
old copy or mint a replacement identity automatically. Independent recovery and
redundancy assessment remain Prompt 10 work after approved durable publication.

## Package format and trust

`tools/legislation_durable_state.py` has four offline commands: `build`, `verify`,
`restore` and `plan`. There is no upload client and no implicit network fallback.
The typed input descriptor and expected package digest are trusted caller inputs:
obtain them from reviewed evidence, not from the download being verified.

The v1 package is a deterministic ZIP_STORED file. Names are sorted; timestamps,
permissions and ZIP platform headers are fixed. No compression or archive path
normalization is accepted. Limits are 256 MiB outer package, 4,098 members,
64 MiB per member; input-tree reading additionally retains Prompt 08's 128 MiB
expanded-state and 4,096-file limits. Verification enforces the same expanded
state limit before promotion. Package inputs must be regular files, not links,
directories or special files. Larger state requires a reviewed format or
bounds revision, not relaxed checks at runtime. Workspaces must be private and
exclusive to cooperative callers; this is not a hostile same-user filesystem
sandbox.

- `package.json`: format version, input pin, scope/source/seed identity, rights
  declaration, builder revision and code hash, semantic roots, and an ordered
  original-file index with path components, byte sizes, SHA-256 and BLAKE3.
  The indexed CAS entries form the object index. It also indexes all original
  manifest/checkpoint/receipt/lineage/parent files without rewriting their bytes.
- `state/`: exact original files. A canonical merge includes both retained parent
  ZIPs/descriptors, completion inventory, merge receipt and version links. A
  native continuation includes the Prompt 08 seal, lineage and receipt history.
- `RESTORE.txt`: fixed verification/restore instructions, checked byte-for-byte.

For the Prompt 04 canonical merge, independently pin the completion marker,
merge receipt and manifest root. Verify the marker's full inventory, parents'
archive/descriptor hashes and commits, merge status/counts, native checkpoint
structure, roots, work/version membership and every CAS object's dual hashes and
size. Retained nested ZIPs remain opaque original evidence, not new extraction
inputs. Their exact hashes are bound to the previously verified merge marker.
No Actions metadata fetch or unexpired operational cache is required.

For a native continuation, the input includes the reviewed Prompt 08 reference.
The verifier reuses its source/root/seal/parent-lineage checks offline; it does
not treat historical artifact expiry as evidence of corruption of preserved
bytes. Operational use of an Actions parent still needs Prompt 08's live checks.
A merged package is never disguised as a native harvest receipt or automatically
adopted into an acquisition lane.

The merged 552-work scope is identified by its exact inventory root, with no
seed-only claim. The reviewed 500 IDs and the 33,693 search-derived candidate IDs
retain their distinct meanings; none of these counts proves full coverage.
Future source or seed transitions must preserve explicit identities and lineage.

## Offline commands

Supply reviewed input and rights JSON. Use exclusive outputs outside the Git
checkout for payload packages. Substitute the exact source software commit and
verified digest; no command below grants publication authority.

```sh
uv run --locked python tools/legislation_durable_state.py build \
  --input /absolute/verified-state --pin /absolute/reviewed-input.json \
  --rights /absolute/reviewed-rights.json --software-commit FULL_GIT_SHA \
  --output /absolute/new-state.zip
uv run --locked python tools/legislation_durable_state.py verify \
  --input /absolute/new-state.zip --digest EXPECTED_SHA256 \
  --output /absolute/new-verification.json
uv run --locked python tools/legislation_durable_state.py restore \
  --input /absolute/new-state.zip --digest EXPECTED_SHA256 \
  --output /absolute/fresh-state
uv run --locked python tools/legislation_durable_state.py plan \
  --input /absolute/new-state.zip --digest EXPECTED_SHA256 \
  --observation /absolute/observed-destination.json \
  --output /absolute/new-plan.json
```

Build validates its own complete output before an exclusive write. Verification
requires an externally pinned digest, validates canonical encoding and all
original bytes, and performs semantic state verification again. Restore verifies
fully before creating a sibling `.quarantine` directory, writes originals there,
compares readback bytes and promotes only into an absent destination. Write
failure retains quarantine; retry requires a new workspace, never erasure of a
failed attempt. CLI failure is nonzero with a sanitized message; it does not
emit a success receipt. Callers must retain command exits/log hashes as evidence.

A publication observation has exact dataset identity, a revision or null, and
path/hash/size claims. Null revision permits only an empty observation. A matching
claim produces `verify_existing_bytes`, never an upload/readback success claim.
Missing entries produce `upload_after_approval`; a conflicting digest or size
fails closed. This permits idempotent and partial-upload planning without
replacing remote data. A later approved executor must compare the base revision,
perform one coherent commit, independently cold-read every planned byte at the
returned exact revision and retain partial/failed attempts. Never invent a
revision/DOI, blindly retry against moving main, or infer completeness from an
upload response. All current plans report `dry_run_only`, null published revision
and DOI, and `readback_verified: false`.

## Handoffs and validation

Prompt 10 owns final independent recovery acceptance after custody and access
are established. Prompts 06/07 must not bypass Prompt 08 authority by consuming a
locally restored merge directly. Prompt 11/12 concurrency and failure semantics
remain separate. Any rights clearance and actual publication is a separate gate.

Focused tests cover deterministic byte order, cold local restore, corruption,
wrong pins/parents, missing/orphan objects, malformed checkpoint/archives,
rights-blocked plans, partial upload claims, retries and exclusive promotion.
Targeted mutation controls supplement native gates. Run the repository's full
`./scripts/validate.sh` and require exact-head hosted checks before delivery.
