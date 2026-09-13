# Missing-originals recovery audit — 2026-09-06

The `17225–17226` batch is **not recovery-ready from the located evidence**.
The later `17226–17227` candidate is byte-verified and locally recovery-ready,
but it contains a different request. No source acquisition, publication,
dispatch or ownership change was performed.

## Missing batch: exact evidence loss

[Run 33305989413](https://github.com/edithatogo/fyi-archive/actions/runs/33305989413)
captured request 18631. Fresh artifact readback of unexpired artifact 9730497676
matches the previously recorded ZIP digest `67bb806b…b17f2`. All 14 retained
members are manifests, ledger or analytical sidecars; there is no raw inventory,
original request store, HTML, attachment payload, WARC or WACZ. Their 55,497
uncompressed bytes include eight attachment references and ten WARC record IDs.
The manifest, event and attachment sidecar hashes match the batch receipt.

The source-records Parquet contains identifiers, locators and hashes, not raw
content. No artifact member matches recorded request-content SHA-256
`5b48db2d192ad852186a0b85e5ac6537d2e7e82fd392bfafeda43d8eb1a02e84`.
Hashing all 31 files in the retained NZ preservation area found no matching
request content. A bounded filename scan of that area and the local donor
checkout found no 18631 original. This does not rule out an unexamined backup.

Anonymous public Hub metadata at revision `52d747d055b00eba3f185e000efa2700e43f8c1e`
listed 34 paths, with no matching original-candidate path (18631, WARC/WACZ,
raw archive, objects, snapshots or data/raw). This is a current-head path check,
not an exhaustive historical content search.

**Exact next repair:** locate the original request JSON matching that digest,
the original HTML/WARC and the eight attachment payloads identified in the
retained manifest. Validate hashes, relationships and the actual capture context,
then prepare a package from a trusted raw inventory. No conversion of these
sidecars can manufacture the absent originals. If no retained copy exists,
retain the historical gap. A later acquisition would be a new observation,
with its real timestamp; it cannot restore the lost historical bytes.

## Later candidate: independently reverified local recovery

The existing package at
`/Volumes/PortableSSD/Archives/foi-preservation/nz-fyi/run-33307777685-reconstructed-v2`
has manifest SHA-256
`3514658895d5e26726f4d23a776a709a4c0fce165dcfb8e307ef10f4d15bb49e`.
It contains request 18632, two responses, two events and eight original files.
Complete package verification and a fresh cold restore passed. Rebuilding from
the retained capture with the same recorded context reproduced the manifest
and every package file byte-for-byte. The original package was not modified.

The existing `nz-reconstructed-publication-decision.pending.json` binds exactly
this candidate and remains pending with no reviewer/evidence references. The
older `a78bef…` disposition is a different candidate and was not reused.
Thus private local recovery is ready; public eligibility is not established by
this audit. These are the existing decision fields, not a new permission gate.

## Validation and reproducibility

- `gh api repos/edithatogo/fyi-archive/actions/runs/33305989413/artifacts`
- `gh api repos/edithatogo/fyi-archive/actions/artifacts/9730497676/zip`
- Inspect ZIP member inventory without extracting payloads; hash retained
  members and compare with the historical batch receipt.
- `uv run --locked python tools/foi_package.py restore --root /Volumes/PortableSSD/Archives/foi-preservation/nz-fyi/run-33307777685-reconstructed-v2 --output /tmp/foi-hosted-readback.mPzObL/nz-candidate-cold-restore-20260906 --manifest-sha256 3514658895d5e26726f4d23a776a709a4c0fce165dcfb8e307ef10f4d15bb49e`
- Call `prepare_package` on retained `run-33307777685` using the verified
  package's `CaptureContext` and `capture_inventory_sha256`, into a new local
  directory; compare manifest and all package-file bytes.
- `uv run --locked pytest tests/test_foi_package.py -q --no-cov`: 105 passed.

No receiver defect was found: its existing package preparation requires the
trusted raw inventory and rejects absent originals. No duplicate implementation
or fabricated raw fixture was added. Full gates remain with the parent.
Exact hashes, scope limits and outcomes are in the
[machine receipt](missing-originals-recovery-audit-20260906.json). Historical
hash-chained receipts and `local-safe-gaps` bytes remain unchanged.
