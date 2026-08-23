# Implementation Plan: Single-Pass Ironclad Bronze Ingestion Hardening

### Phase 1: Magic Byte Filter & MIME Signature Engine
- [ ] Task: Implement `src/archive_govt_nz/bronze/sniffer.py` detecting valid XML, JSON, PDF, CSV, and WARC magic headers.
- [ ] Task: Integrate filter into `BronzeAdapter` to abort ingestion before CAS disk write on invalid signatures.
- [ ] Task: Add test cases verifying rejection of polyglots and HTML error pages disguised as PDFs.
- [ ] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 2: Streaming Multi-Hash Engine (SHA-256 + BLAKE3 + CIDv1)
- [ ] Task: Implement `src/archive_govt_nz/bronze/multihash.py` providing single-pass streaming IPFS CIDv1 computation.
- [ ] Task: Update `BronzeManifest` and Arrow record link columns with `nz_content_cidv1`.
- [ ] Task: Add unit tests verifying RFC/IPFS test vector compatibility.
- [ ] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 3: Structural Schema Fingerprinting & Drift Detection
- [ ] Task: Implement `src/archive_govt_nz/bronze/fingerprint.py` computing canonical schema hashes from JSON/XML/Arrow structures.
- [ ] Task: Integrate schema fingerprint routing into Silver layer partitioning.
- [ ] Task: Add unit and drift detection tests.
- [ ] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 4: Offline Ed25519 Manifest Sealing
- [ ] Task: Implement `src/archive_govt_nz/bronze/attestation.py` for deterministic Ed25519 key loading, signing, and verification.
- [ ] Task: Emit `.sig` files alongside B1 acquisition manifests and verify on readback.
- [ ] Task: Add cryptographic verification test suite.
- [ ] Task: Conductor Review & Automated Phase Gate Verification.

### Phase 5: Quality Gates & End-to-End Hardening Certification
- [ ] Task: Update mutation testing suite (`tools/mutation_medallion.py`) to test magic byte, multihash, and attestation mutants.
- [ ] Task: Validate full 20-stage gate harness.
- [ ] Task: Conductor Track Review & Final Certification.
