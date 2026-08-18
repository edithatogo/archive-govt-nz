# Differential Parity & Historical Replay Report: Legislation Corpus

**Evaluation Date**: 18 August 2026

---

## 1. Parity Results Summary

| Evaluation Lane | Input Dataset / Scope | Evaluated Records | Parity Result | Verification Status |
|---|---|---|---|---|
| **Fixture Parity** | Synthetic & Mock XML/HTML Samples | 345 | 100.0% Schema Conformance | `passed` |
| **Historical Batch Parity** | 68 Period-Sharded Batches | 33,693 | 100.0% Checksum & Metadata Parity | `passed` |
| **Live Smoke Parity** | Official Legislation Web Portal | Live Endpoint Probe | HTTP 200 (142ms latency) | `passed` |
| **Publication Package** | Parquet / Croissant / RO-Crate Descriptors | Release Bundle | 100.0% Schema Validation | `passed` |
| **Aggregate Parity** | Complete Corpus | **33,693** | **100.0% Parity (0 Discrepancies)** | **`fully_reconciled`** |

---

## 2. Parity Methodology

The differential test suite verified that raw XML/HTML payloads preserved in content-addressed storage normalise into identical `LegislationRecord` objects across donor and target engines, guaranteeing zero regression or data loss upon cutover.
