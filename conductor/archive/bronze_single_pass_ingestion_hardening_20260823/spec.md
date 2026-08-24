# Specification: Single-Pass Ironclad Bronze Ingestion Hardening

## Architecture & Single-Pass Flow
```text
Raw HTTP Stream (Bytes)
      │
      ├──> [Magic Byte Sniffer (First 512B)] ──> Validate MIME (fail-closed)
      │
      ├──> [MultiHash Stream Fan-out]
      │        ├── SHA-256 Engine
      │        ├── BLAKE3 Engine
      │        └── IPFS CIDv1 (Multicodec/Multihash)
      │
      ├──> [Schema Fingerprint Engine] ──> Structural AST hash (nz_schema_fingerprint)
      │
      └──> [Sharded B2 CAS Storage] ──> CAS / Sharded Directory
               │
               ▼
      [B1 Manifest Assembler + Ed25519 Signature (.sig)]
```

## Schema Updates
- **`B1 Acquisition Metadata`**: Add `ipfs_cidv1` and `ed25519_signature` fields.
- **`B0 Source Index`**: Store verified MIME types and signature status.
