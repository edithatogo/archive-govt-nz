# Architecture Specification: Legislation Publication Continuity

**Scope**: Automated publishing to Hugging Face, Zenodo, and standard linked metadata.

---

## 1. Multi-Target Distribution

```
                       +-------------------------------+
                       | archive-govt-nz Publisher     |
                       +---------------+---------------+
                                       |
          +----------------------------+----------------------------+
          |                            |                            |
          v                            v                            v
+--------------------+       +--------------------+       +--------------------+
| Hugging Face       |       | Zenodo             |       | Linked Metadata    |
| Living Dataset     |       | Concept Lineage    |       | RO-Crate 1.1       |
| (corpus-leg-nz)    |       | (10.5281/20592540) |       | Croissant JSON-LD  |
+--------------------+       +--------------------+       +--------------------+
```

---

## 2. Integrity and Readback Verification

1. **Staged Publication Plan**: Synthesizes changes and verifies Crown Copyright reuse permissions.
2. **Atomic Upstream Push**: Pushes Parquet shards and metadata descriptors.
3. **Independent Remote Readback**: Verifies upstream file sizes, SHA-256 hashes, and dataset accessibility before emitting a publication receipt.
