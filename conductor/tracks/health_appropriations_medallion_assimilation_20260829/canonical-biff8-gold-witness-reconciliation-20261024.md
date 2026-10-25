# BIFF8 Gold numeric-witness reconciliation — 24 October 2026

Canonical Gold now emits `biff8_numeric_witness_reconciliation.json` whenever
the BIFF8 appropriation or revenue products are present. Each source fact is
linked to its one amount-field lineage record and numeric-evidence row. The
control retains the source vintage, source-object SHA-256, literal period,
record/source row, source column, encoded integer, payload SHA-256, encoded
bytes, numeric-evidence ID and exact Decimal amount. Duplicate or missing fact,
lineage, or witness links fail closed.

The report is copied into the package manifest and each present BIFF8 product;
package verification checks its structure, bounded identity accounting and
cross-copy equality. This demonstrates preservation of the admitted numeric
witness through canonical Gold. It is not a second parse of the original
workbook, a donor or official-source comparison, a unit/currency assertion, a
rights decision, or publication approval. Historical differences remain
source-separated and uninterpreted.

Focused verification passed for the witness reconciliation contract, the full
canonical consumer suite, and the Gold verifier suite: 92 tests passed. Review
also hardened malformed family and count handling so invalid JSON structures
are rejected without set-construction errors and booleans cannot satisfy integer
count fields. The final repository harness passed on CPython 3.15.1:
8,415 tests passed, 14 skipped, and 97.06% coverage against the 80% threshold;
schema, parity, mutation, audit, licence, secret-scan and SBOM checks passed.
Protected hosted Actions remain the delivery gate.
