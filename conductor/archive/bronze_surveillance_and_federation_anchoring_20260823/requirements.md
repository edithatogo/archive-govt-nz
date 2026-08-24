# Requirements: Surveillance Heartbeat Ledger & Cross-Repository Federation Protocol

## Background & Rationale
An evidence-first government archive must prove continuous surveillance (distinguishing between 'regulatory stillness' and 'scraper failure') and enable zero-copy federation joins with partner repositories (`global-medicines-atlas`, `fyi-archive`) without central database locks or redundant storage.

## Core Requirements
1. **Surveillance Heartbeat Ledger (`304 Not Modified`)**: Log crawl checkpoints where upstream servers return HTTP 304 / matching ETags without writing duplicate B2 blobs, keeping an unbroken surveillance chronology with minimal SSD write amplification.
2. **Canonical Cross-Repository URN Protocol**: Standardize composite URN identifiers (`urn:nz:<domain>:<agency>:<time_context>:<entity_type>:<local_id>`) shared across `archive-govt-nz`, `global-medicines-atlas`, and `fyi-archive`.
3. **Zero-Copy Federated DuckDB Parquet Views**: Provide pre-configured SQL join views linking NZ statutory notices to GMA medicine schedules and FYI OIA records.
4. **Asynchronous OpenTimestamps Batcher**: Build a non-blocking background task to calculate Merkle roots over weekly B1 acquisition manifests and anchor them to Bitcoin/public transparency logs via OpenTimestamps (`.ots`).
