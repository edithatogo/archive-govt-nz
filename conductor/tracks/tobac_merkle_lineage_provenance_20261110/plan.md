# Implementation Plan — Two-tier Merkle provenance and original-to-extract verification for tobac

- [ ] Define the versioned two-tier Merkle provenance manifest schema (`runner_closure_sha256` and `evidence_registry_merkle_root`) with canonical sorted leaf serialisation and zero self-referential hash cycles.
- [ ] Add deterministic original-to-extract verification checks binding extracted tabular/numeric sidecars to archived raw HTML/XLSX/CSV/PDF bytes and HTTP capture receipts.
- [ ] Add synthetic and fixture-backed regression tests covering tampered raw bytes, modified extractor closures, out-of-order Merkle leaves, and missing source payloads.
- [ ] Verify downstream consumer handoff parity with `edithatogo/tobac` (`scripts/hosted_lineage.py`, `src/tobac/data.py`) and `edithatogo/sourceright` (`Track 111`).
