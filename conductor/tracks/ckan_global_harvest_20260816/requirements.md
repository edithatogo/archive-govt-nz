# MoSCoW Requirements — Track 18: Global CKAN Catalog Harvester

## Must

- Discover the complete `data.govt.nz` catalogue via paginated CKAN `package_search` without organization filtering.
- Reconcile reported counts vs discovered packages, deduplicating dataset and resource identities.
- Apply automated rules-based licensing and rights evaluation (CC-BY, CC-0, Open Data vs Unknown/Restricted).
- Fail-closed: record restricted, sensitive, or missing-rights resources as metadata-only tombstones without initiating download.
- Enforce per-host rate limiting and global concurrency/byte budgets during streaming payload capture.
- Stream admitted payloads into immutable content-addressed storage (SHA-256 and BLAKE3).
- Record all HTTP transaction failures (404, 410, 403, 500, timeouts) into a structured Broken URL & Exception Ledger for follow-up.

## Should

- Support automated fallback to CKAN DataStore exports when direct download URLs are missing or broken.
- Support batch triangulation against the Wayback Machine / Internet Archive for dead links.
- Generate normalized JSONL and Parquet catalogue derivatives.
- Generate RO-Crate JSON-LD metadata describing dataset provenance and distribution graphs.
- Provide BagIt manifest staging for citable preservation bundles.

## Could

- Support automated periodic incremental delta sweeps.


## Won't (this track)

- Bypass license or rights gates for unconfirmed resources.
- Publish payloads externally without explicit publication authorization.
