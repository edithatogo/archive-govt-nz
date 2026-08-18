# Architecture Specification: Canonical Preservation System

`archive-govt-nz` provides an evidence-first, reproducible digital preservation architecture for New Zealand government records, datasets, and public communications.

---

## 1. Storage & Ingestion Model

1. **Content-Addressed Storage (CAS)**:
   - Every raw byte stream ingested from public endpoints is hashed using dual cryptographic digests: **SHA-256** and **BLAKE3**.
   - Storage is organized content-addressably: `objects/{prefix}/{sha256}`.
   - Guaranteed immutable, deduplicated payload storage.
2. **W3C PROV-O Lineage**:
   - Every ingestion event produces an immutable Entity-Activity-Agent graph.
   - Entities record the raw CAS hash, retrieval timestamp, HTTP headers, and URL.
   - Activities document normalisation, compaction, and derivative compilation.
   - Agents document the specific adapter and worker commit hash executing the job.

---

## 2. Container Formats

- **ISO 28500 WARC 1.1**:
  - Gzip-compressed records encapsulating warcinfo, request, response, and metadata records.
- **WACZ (Web Archive Collection Zipped)**:
  - Standard zip container bundling WARC records, CDXJ indexing, and datapackage.json fixity manifests.
- **Parquet Analytical Tables**:
  - Snappy-compressed columnar tables structured for DuckDB, PyArrow, and Polars analytical workloads.

---

## 3. Disaster Recovery & Fixity

- **Deterministic Replay**:
  - Zero-network offline replay engine reconstructing domain entities and auditing bitstream fixity.
- **Restore Drill**:
  - Automated rehearsal harness verifying complete database and archive reconstruction from cold backup snapshots.
