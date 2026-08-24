# Review & Certification: Single-Pass Ironclad Bronze Ingestion Hardening

Certified complete on 2026-08-23 (UTC).

## Delivered capabilities

1. **Magic byte / MIME signature filter** — `src/archive_govt_nz/bronze/sniffer.py`
   detects XML, JSON, PDF, CSV, and WARC signatures from the first 512 bytes;
   `BronzeAdapter` aborts ingestion before any CAS disk write on invalid or
   polyglot payloads.
2. **Streaming multi-hash engine** — `src/archive_govt_nz/bronze/multihash.py`
   computes SHA-256, BLAKE3, and IPFS CIDv1 (`bafkrei...`) in a single pass;
   manifest and Arrow record link columns carry `nz_content_cidv1`.
3. **Structural schema fingerprinting** — `src/archive_govt_nz/bronze/fingerprint.py`
   produces the canonical `nz_schema_fingerprint` digest used for Silver
   partition routing and drift detection.
4. **Offline Ed25519 manifest sealing** — `src/archive_govt_nz/bronze/attestation.py`
   signs B1 acquisition manifests deterministically (RFC 8032 vector covered)
   with `.sig` sidecars verified on readback; no external SaaS/Rekor dependency.

## Verification evidence

- Full test suite: **997 passed** (`uv run --locked pytest --assert=plain`,
  126.48 s) including `tests/bronze/` suites for sniffer, multihash,
  fingerprint, attestation, manifest, and adapter behaviour.
- Mutation gates all green, including `mutation-medallion` covering
  `bronze_magic_sniffer`, `bronze_cidv1_multihash`, and
  `bronze_ed25519_attestation` mutants.
- Remaining assurance stages green locally on 2026-08-23: schemas, slops,
  benchmark-cas, dependency audit, licence inventory, secret scan, SBOM
  (116 components). Lock, format, lint, and type gates green via
  `scripts/validate.sh`.

## Boundaries

No publication, deployment, signing of external artefacts, rights decisions,
or donor actions were performed by this track. Repository readiness only.