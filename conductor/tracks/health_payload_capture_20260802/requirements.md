# MoSCoW requirements

## Must

- Capture only candidates from an approved metadata discovery receipt.
- Enforce HTTPS, byte/time/redirect/decompression/archive-expansion limits.
- Independently validate content type and quarantine suspicious payloads.
- Preserve originals immutably with SHA-256, BLAKE3, provenance, and tombstones.
- Fail closed on unclear rights, sensitivity, credentials, or publication status.
- Provide deterministic manifests, resumability, and evidence receipts.

## Should

- Support resumable downloads and bounded concurrency.
- Emit WARC transaction records where material.
- Produce Parquet/JSONL derivatives only as separately identified transformations.

## Could

- Add provider-specific adapters and richer format detection.

## Won't (this track)

- Publish to Hugging Face or Zenodo.
- Capture resources without an eligible discovery receipt.
- Resolve legal, privacy, or rights ambiguity by inference.
