# Reserved metadata roots — independent P2 review fix

Follow-up to `bfc531596c9fdd2c6be912b1a1a6401131e2170e`, 2026-09-07.
Meitner identified that exact-string exclusions admitted case variants and
descendants of reserved metadata files. Fully consistent `manifest.json`,
`RO-CRATE-METADATA.JSON`, `MANIFEST.json/child.bin` and
`ro-crate-metadata.json/child.bin` inventories could therefore pass.

The new guard casefolds the first path component and reserves `manifest.json`,
`ro-crate-metadata.json`, `readme.md` and the whole `metadata` directory. These
cover the manifest and required metadata roots in the health candidate inventory;
all metadata directory members and descendants are protected without maintaining
a fragile list of individual descriptor filenames. Existing portable-name checks
and payload-to-payload collision checks remain unchanged.

The test helper binds **every** payload key, rights reference, bundle digest,
Croissant member and RO-Crate identity to each test path. Before the fix, the
22-case new regression selection yielded **18 failed / 4 passed**: failures were
missing expected exceptions, not unrelated fixity/identity errors. After the fix,
all 22 pass. Tests cover case variants, mixed-case descendants, README and whole
metadata-directory reservation; `data/manifest.json`, `metadata-copy/payload.bin`
and `manifest.jsonl` remain valid nonreserved payload paths.

Final checks: **164 affected tests passed** (116 module cases), **100% module
line/branch coverage** (139 statements, 14 branches), **28/28 cold mutants killed**
with pytest exit 1 and baseline exit 0. The three added mutants remove root
casefolding, remove descendant protection and disable metadata-directory
reservation. Ruff check/format and focused basedpyright pass.

Reproduce using the commands in `metadata-application-contract.md`, with the
current mutation runner and tests. The earlier evidence JSON remains a historical
receipt pinned to the original commit, not current source hashes. Current hashes
and results are in `metadata-application-reserved-root-reviewfix.json`.

No shared lifecycle, generator, adapter, dependency, rights or federation changes.
No full harness or remote writes. Parent owns independent re-review/integration;
GDP/Crown and FOI review work was paused for this fix, not declared complete.
