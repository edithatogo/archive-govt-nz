# Requirements: Single-Pass Ironclad Bronze Ingestion Hardening

## Background & Rationale
The Bronze layer is the immutable evidentiary foundation of `archive-govt-nz`. To ensure zero-trust ingestion while preserving strict performance (<10s CI/CD gates, minimal SSD write amplification), we must validate and attest payloads during ingestion in a single stream pass.

## Core Requirements
1. **Magic Byte / Header Signature Filter**: Inspect the initial 512 bytes of raw streams to reject polyglots, truncated HTML error pages, or malformed binaries before committing to B2 CAS.
2. **Streaming Multi-Hash Triplet**: Compute `sha256`, `blake3`, and `cidv1` (`bafkrei...` IPFS multihash) concurrently in memory without multi-pass disk reads.
3. **Deterministic Structural Schema Fingerprint (`nz_schema_fingerprint`)**: Calculate a canonical 16-byte digest of tabular/JSON/XML layouts to enable Silver partition routing and automatic schema drift alerts.
4. **Offline Ed25519 Manifest Sealing**: Cryptographically sign B1 acquisition manifests using local deterministic Ed25519 keypairs (zero external SaaS/Rekor dependency).
5. **Zero Write-Amplification Impact**: Guarantee <5% latency overhead over standard CAS ingestion.
