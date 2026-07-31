# Preservation packaging evaluation

This is a bounded evaluation for the Treasury vertical slice. It does not adopt
OCFL, RO-Crate, or BagIt as a release requirement. The authoritative paired
machine-readable receipt is `evidence/preservation-packaging-evaluation.json`.

| Standard | Current status | Intended role | Known gap |
| --- | --- | --- | --- |
| OCFL | Candidate | Immutable versioned object layout | Needs an operational profile around the ledger |
| RO-Crate | Candidate | Research provenance graph and metadata | Does not replace storage or resumability |
| BagIt | Candidate | Portable transfer package | Snapshot-oriented; external version ledger remains required |

The current recommendation is to retain the content-addressed store, SQLite
ledger, JSON Schema manifests, Parquet/JSONL derivatives, and WARC receipts as
the release baseline while evaluating these standards against real Treasury
fixtures.
