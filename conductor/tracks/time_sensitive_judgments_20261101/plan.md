# Time-sensitive judgments

- [x] Enumerate the three senior-court public-interest lists. The 1 November snapshot has three Supreme Court cards, one Court of Appeal card and 23 High Court cards. Other Courts links to separate District and Employment Court sources.
- [x] Reconcile one JDO court/year. The Supreme Court 2004 date filter requires padded ISO dates. All 30 returned document IDs were distinct. Repeat with the repo-local Python CLI and a fresh output path: `.venv/bin/python tools/jdo_inventory.py 2004 output.json`.
- [x] Publish a bounded original-body pilot. Four public-interest originals and the 9 November 2004 Pharmacy Care Systems decision passed identity review. The latter uses its docket because the original supplies no neutral citation. One anonymous pinned packet readback checked all five body hashes and all 57 inventory entries. One focused test passed.
- [ ] Resolve item-level review for 23 public-interest PDFs and 29 inventory-only JDO entries. Prioritise expiring listings. Record publication orders and third-party appendices separately.
- [ ] Qualify recurring discovery, replacements and withdrawals before expanding automatic publication. Preserve same-citation revisions. A listing expiry alone does not establish withdrawal.

[Verified packet](https://huggingface.co/datasets/edithatogo/archive-govt-nz-global/blob/f5c5ca39919d4cba4b057ac2c265f625a549f88f/judgments/pilots/20261101/packet.zip). SHA-256 `68a53f2ba37dd11e75b2b41d7bea8d4837375679d6c51253958587294682faf2`.

Chat 01a18d6e-759f-76c0-85cd-03413c023c8e, standard worktree /Volumes/PortableSSD/CodexWorkData/legal-coverage-20261031/recovery-checkout-20261101, branch codex/time-sensitive-judgments-20261101. Native scope was the single additive judgments pilot path. The notices archive and Parliament writer retain their existing ownership.

## Wider case law, 2025

- [x] Enumerate all ten court categories returned by the Ministry taxonomy. Page counts and unique document paths agreed for each court, totalling 3,972 distinct published links. Family and Youth Court entries are represented only by opaque document-path hashes in the public inventory.
- [x] Publish four reviewed original PDFs, one each from the Court of Appeal, High Court, Employment Court and District Court. Their neutral citations, dates, source URLs, byte counts and digests are in the manifest. One anonymous pinned readback verified the ZIP, manifest and every original. The focused court-label and pagination regression passed.
- [x] Run the companion medico-legal repository’s source-audit and source-rights commands with its own Python 3.15.1. Its ledger classified all 17 sources as fetch scaffolds with parser stubs and source-specific citation/derived-metadata caveats. This supports separate source qualification before raw publication.
- [ ] Review outstanding 2025 bodies, including orders with annexes, then extend court/year partitions and qualify replacement and withdrawal handling. The 2025 inventory accounts only for JDO’s published selection.

[Verified 2025 packet](https://huggingface.co/datasets/edithatogo/archive-govt-nz-global/blob/45d04e439fa2e752c40c402c95feee900da4bbf2/judgments/2025/court-year-inventory-20261101/packet.zip). SHA-256 `4d91908daeb9c376c4a10752d89d806929ae5389c51815035e4cdab26562ca91`. This chat retained the CLI worktree and wrote only the new dated Hub packet. The companion source and its publication scope remain with their existing writer.
