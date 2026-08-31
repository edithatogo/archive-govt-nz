# Fresh original-to-product replay

Observed 2026-08-31 UTC using versioned code at `4bedcf1` in an isolated clone.
This is a four-profile local replay, not full AC-12/Platinum, source-area,
rights or publication completion. No network acquisition was performed.

Two new empty derivative directories independently ran `plan_rebuild`,
`execute_rebuild`, `export_compatibility`, `export_gold`, then `render_plots`.
Inputs were the retained donor manifest pinned at
`893f387e1f361400285ccc84802b497e87802d1ad913826ff7d9055b07a03b74`
and its original CAS objects. The retained observation context
`2026-08-30T08:58:00+00:00` was reused, not asserted as a new acquisition.
All 23 donor objects and the manifest were hash-checked before/after; only
the four selected Budget/BEFU/HYEFU/historical workbooks feed extraction.

## Observed results

Each run produced 38 files / 8,077,673 bytes. Every byte matches between runs:

| Stage | Files | Bounded result |
| --- | ---: | --- |
| Raw source extraction | 18 | 341 facts; raw-run manifest `da65ee2f38e2450e7273e84fa48b0b29a6a44670d84401fdbb7389f710fa0269` reproduced |
| Compatibility SQLite/sidecars | 4 | All 341 facts; exact-value and lineage sidecars retained |
| Gold | 8 | 321 selected facts; forecast summaries excluded explicitly |
| Plots | 8 | Six PNGs, contracts and manifest |

All 23 original object hashes remain unchanged. Every compatibility/Gold/plot
payload hash and exact file closure was verified. The fresh raw run was
reverified by the existing downstream readers. Outputs stay outside Git in
`/tmp/health-originals-e2e.KwBOYT/{first,second}`; no old package was overwritten.

## Older retained product comparison and bounded difference

An additional strict comparison with older retained products initially raised
`AssertionError` at compatibility. This failure was retained and investigated,
not hidden by rewriting either product or weakening the two-run comparison.

All 18 raw files, exact-value/lineage sidecars, all eight Gold files and all
eight plot files match older retained bytes. The only differences are the
SQLite file and its manifest. The prior manifest records SQLite 3.50.4; the
current runtime records 3.53.1. Independent immutable/read-only connections
confirmed identical SQL schema, table definitions and all 341 ordered rows
across five tables; both databases pass `PRAGMA integrity_check`.

Only byte offsets 98 and 99 differ in the 49,152-byte SQLite file. They lie in
the writer-library-version field at offsets 96–99 documented by the
[SQLite file-format specification](https://www.sqlite.org/fileformat.html#write_library_version_number_and_version_valid_for_number).
The manifest differs only in `sqlite_version` and the corresponding output
hash. Thus this is runtime-stamped binary drift, not changed financial data.
Old SQLite/manifest pins are preserved; current manifest is
`ed8464a7c36a24e9ae5d13256435c522f44a1c16324ce9d157971679d2236602`.
Do not claim cross-runtime byte identity or patch the database header.

## Receipt pins and remaining scope

- Replay script SHA-256:
  `b7a4ae1e44f70b929f85833a1ff93a65a61ce5d913aea8988a90fd484f8a87ca`.
- Successful two-run log SHA-256:
  `fa395ae160b74a9873111d58dd4f046dce8f204fb382f7872755b9f0c361f091`;
  real replay exit code zero.
- Initial strict retained-comparison script SHA-256:
  `72a3db01931d86785a10031a1f263e2e4712f591b80ac33f7e0d1f55934bc284`.
- Independent SQLite schema/row/byte comparison script SHA-256:
  `b2dcb1f604544ae9a62e1403d7e006f4384833634c863efb61abf3b1b3289ff0`.

The temporary driver is an execution receipt, not a newly installed production
command. This run excludes Platinum metadata, interrupted-stage reuse,
additional source areas and later vintages. Those remain separate tasks;
neither a local success marker nor this evidence authorizes a new candidate,
Hugging Face update or donor retirement.
