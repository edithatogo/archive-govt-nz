# Capture-resume binding integration

The full locked harness at `78c17e2d` completed with exit 0: 5,565 tests
passed, coverage 97.86%, all configured schema, parity, mutation and hygiene
checks passed, CAS throughput 651.84 MB/s (minimum 25 MB/s), dependency audit,
licence inventory, secret scan and validated 112-component SBOM passed.

This passing run is not final review clearance. Independent review identified
two additional malformed-record cases: conflicting duplicate HTTP Content-Type
headers and a missing final WARC record terminator. Follow-up regression tests
and fixes are required before merging. The original source/CAS binding finding
remains open until that correction and validation are complete.

Earlier portability correction `7b672a9c7448ec4ffb5f925553b70761db2f3993`
passed all three hosted OS checks in run `34083824580`, including Windows job
`101623984365` (12m36s). Normalization inherited that correction at `3c446166`
and passed all three OS checks in run `34083833612`. These older hosted passes
are not attributed to the newer WARC-binding implementation.
