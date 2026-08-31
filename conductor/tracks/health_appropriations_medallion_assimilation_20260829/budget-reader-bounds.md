# Public Budget reader metadata bounds

This narrow follow-up retains the existing Budget v1 reader API, typed facts,
lineage, disposition joins, snapshots, row and expanded-byte limits. It inspects
at most five directory entries to enforce the exact four-file package closure,
and supplies 4 MiB Thrift string / 100,000 container limits when constructing
each ParquetFile, before metadata inspection or table materialization.
This is bounded transport consumption, not a hostile-Parquet sandbox, new
source semantics, original workbook capture, rights clearance or publication.
No raw packages, originals or HF objects are written.

## Red-first evidence

Five new tests include an exact four-entry success control and a generator that
fails if a sixth entry is requested, a constructor spy checking both caps before
decode, and two real-decoder tiny-cap rejection cases. Before implementation,
four failed and the control passed; receipt
`/tmp/health-budget-reader-bounds.ph7VOb-red.log` preserves the outcome.

First lint found a non-raw regex test literal, corrected without production
change. The first green run passed 61 tests but two new tests expected
ArrowException instead of the decoder's actual OSError size-limit failure;
correcting that expectation yielded all 63 passing. Strict typing then rejected
the spy's unrestricted keyword forwarding (four errors); explicit named cap
arguments resolved it without suppressions or production changes.

The focused critical gate passed all 63 tests in 4.63 seconds with 100% coverage
across 140 statements and 30 branches; Ruff and BasedPyright pass. Critical JSON
is retained at `/tmp/health-budget-reader-bounds.ph7VOb-critical.json`.
Independent review, cold mutation and native delivery receipts follow separately.
