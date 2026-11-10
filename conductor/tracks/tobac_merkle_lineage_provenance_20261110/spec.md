# Specification — Two-tier Merkle provenance and original-to-extract verification for tobac

## Objective and boundary

Provide content-addressed two-tier Merkle provenance manifests and deterministic original-to-extract verification receipts for official New Zealand and Australian public-health, customs/excise, and wastewater releases consumed by `edithatogo/tobac` (`F00`, `F01`, `nz_au_hardening_20261106`).

`archive-govt-nz` owns immutable raw-byte preservation, HTTP/WARC capture receipts, and original-to-derivative CAS fixity. `tobac` owns epidemiological and economic domain schemas, partial-identification interval construction, and VOI decision evaluation.

## Scope

1. **Two-tier Merkle provenance manifest schema**:
   - Separate the **runner/extractor closure digest** (`runner_closure_sha256` covering parser, schema, and normaliser versions) from the **immutable source-byte and candidate-evidence registry digest** (`evidence_registry_merkle_root` over sorted `(artifact_id, raw_bytes_sha256, extract_sha256)` leaves).
   - Prevent self-referential hash cycles when downstream consumers (`tobac`, `sourceright`, `searchright`) verify that a provenance sidecar matches both the archived raw release and the extracted tabular series.
2. **HTTP capture and transport provenance headers**:
   - Record canonical retrieval timestamps, response status, `ETag` / `Last-Modified`, redirect chains, and content-type digests alongside raw HTML/XLSX/CSV/PDF payloads for official statistical and regulatory releases (Ministry of Health / NZHS, NZ Customs Service, ABS, AIHW, ACIC wastewater).
3. **Deterministic original-to-extract verification CLI/API check**:
   - Verify that every extracted numeric row/cell sidecar cites an immutable raw payload SHA-256 and exact byte/sheet/cell coordinate in the CAS manifest, failing closed on missing raw bytes or hash drift.
