# Reviewed Estimates overview recovery

The recovered cohort is exactly the 20 common overview profiles: 2002/03,
2004/05-2017/18 and 2022/23-2026/27. Two fresh builds per edition rebuild 221
selected facts, their lineage and dispositions for every source page. The fixed
Gold query verifies every source field against regenerated Silver. Printed
values, qualifiers, units and literal periods survive without cross-year
arithmetic, calendar mapping, currency or classification inference.

`reviewed-vote-health-recovery-20261027.json` records the complete Silver output
hashes, selected values, record identities, raw source JSON, quality flags and
repeat equality. Each Gold query digest is SHA-256 of UTF-8 `json.dumps` with
`sort_keys=True`, `ensure_ascii=False`, `allow_nan=False`, default separators and
no final newline. This is a versioned serialization, not an RFC 8785 claim.

## Census blocker resolved

The first cohort attempt failed closed because the primary census lacks the
2009/10-2013/14 captures. Their existing edition-specific censuses retain the
exact source hashes, official locators and observation times. The recovery
runner now reads those five separately pinned files only for the corresponding
allowlisted object hashes. It rejects absent/ambiguous records and altered
supplement bytes. It neither changes the historical primary census nor invents
replacement observation times, locators, capture records or rights decisions.
The receipt lists all six census pins actually used. The original WARC/capture
receipts remain separate evidence; this replay makes no new HTTP-capture claim.

## Adapter and numeric reconciliation

The 2002/03 source now has an exact common overview registration using its
existing seven-statement parser, original hash, page count and transformation.
Its three Parquet payloads (facts, lineage and dispositions) match the retained
native command's fresh output byte-for-byte. The native CLI path is unchanged.
An obsolete rejection test for that now-qualified edition was updated to reject
unreviewed 2003/04 instead. Unknown editions still fail closed.

All five modern editions retain their previously recorded Silver hashes and
complete Gold-query digests exactly. Existing modern receipt structure is
preserved. Other source pages remain explicitly unreviewed. The 2016/17 native
registration boundary remains intact.

The integrated clean-room orchestrator now invokes the whole reviewed cohort
in place of its five-edition-only lane. Its other product/report lanes are
unchanged; this focused recovery reuses their existing evidence. Unregistered
vintages and other source families are not covered by this cohort. The broader
Silver/canonical coverage, Gold reconciliation, complete validated Platinum,
operational assurance and final completion contracts remain open.

## Validation

The 36 affected contracts passed. The complete local harness then passed
8,456 tests with 14 capability skips and 96.88% measured coverage against
the unchanged 80% gate, 81 schemas / 71 representative documents, parity 9/9,
all configured mutation checks and supply-chain gates. The obsolete rejection
case was retained in the bounded failure log before its supported-edition fix.
