# MoSCoW requirements

## Must

- Discover all datasets in `ministry-of-health` using bounded CKAN API calls.
- Preserve dataset/resource counts, stable IDs, metadata timestamps, and API hashes.
- Produce deterministic JSON evidence and explicit metadata-only policy.

## Should

- Re-run idempotently and compare counts and IDs.
- Record unavailable or malformed API responses without partial promotion.

## Could

- Add health-topic query comparison after organization scope is reconciled.

## Won't (this track)

- Download source payloads, transform data, or publish to Hugging Face/Zenodo.
