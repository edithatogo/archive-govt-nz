# Deferral Gate Assessment

**Date:** 2026-08-22
**Status:** **KEEP DEFERRED**

## Deferral Gate Criteria

The deferral gate in `conductor/tracks.md` requires all of the following before resuming RO-Crate, BagIt, OCFL, or graph/vector implementation:

| Criterion | Current Status | Evidence |
|-----------|---------------|----------|
| **Materially larger corpus** | ❌ Not met. Corpus is growing (Treasury 91 resources, Legislation 33,693 seeds, Global CKAN harvesting) but still modest. No single dataset exceeds 7,000 files. | `archive-evidence-ledger.json`, HF readback receipts |
| **Stable provenance joins** | ⚠️ Partially met. Legislation has stable provenance through the corrective programme. Treasury has evidence ledger. Health is metadata-only. | Parity receipts, evidence ledger |
| **Demonstrated query workloads exceeding SQLite/Parquet/DuckDB** | ❌ Not met. All current queries are satisfied by SQLite/Parquet/DuckDB. No workload has been demonstrated that requires graph/vector. | No evidence found |
| **Interoperability/retention/security/cost assessment** | ❌ Not met. Bounded preservation fixtures exist but are self-checks, not independent validation. No operating cost analysis exists. | `preservation_conformance_20260801/evidence.md` |

## Recommendation

**KEEP DEFERRED.** The corpus is not yet materially larger, no query workload exceeds current tooling, and no independent interoperability assessment exists. The bounded fixtures remain valuable evaluation evidence but do not justify adoption work.

## Conditions for Re-evaluation

The deferral gate should be reassessed when:
1. The archive corpus exceeds 100,000 objects across all source-sets
2. A query workload is demonstrated that performs poorly on Parquet/DuckDB (e.g., multi-hop graph traversals, semantic similarity search at scale)
3. An independent validator (e.g., `bagit.py`, `ro-crate-validator`, `ocfl-validator`) is available and has been run against the corpus
4. Operating cost projections for preservation formats are produced