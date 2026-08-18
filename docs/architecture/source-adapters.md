# Architecture Specification: Multi-Source Adapters

`archive-govt-nz` integrates source-specific acquisition logic into thin, asynchronous adapter modules implementing the common `BaseSourceAdapter` contract.

---

## Adapter Framework Contract

All adapters inherit from [`BaseSourceAdapter`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/adapters/base.py) and implement:

1. **`observe()`**: Queries the remote public API or feed to discover new post/record identifiers.
2. **`fetch_payload()`**: Downloads the raw byte stream using [`ArchiveHttpClient`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/http.py) with bounded timeouts and exponential backoff retries.
3. **`normalise()`**: Parses the payload into canonical `StandardArchiveRecord` structures.
4. **`store()`**: Saves raw bytes into [`ContentAddressedStore`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/object_store.py) and appends lineage to [`ProvenanceLedger`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/ledger.py).

---

## Implemented Adapters

| Adapter Module | Target Sources | Acquisition Protocol | Rate Limit / Quota Handling |
|---|---|---|---|
| [`adapters/feeds.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/adapters/feeds.py) | RSS 2.0, Atom 1.0, JSON Feed | HTTP GET with conditional `If-Modified-Since` & `ETag` | Bounded polling intervals (4 hrs) |
| [`adapters/bluesky.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/adapters/bluesky.py) | Bluesky AT Protocol | Public `app.bsky.feed.getAuthorFeed` endpoint | 3,000 req / 5 min cursor pagination |
| [`adapters/threads.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/adapters/threads.py) | Threads (Meta) | Public profile JSON-LD and Graph syndication | Exponential backoff (1s - 30s) |
| [`adapters/x_twitter.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/adapters/x_twitter.py) | X / Twitter | Public syndication tokens & embed endpoints | Strict circuit breaker on rate limiting |
| [`adapters/youtube.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/adapters/youtube.py) | YouTube Channels | Channel RSS and YouTube Data API v3 | Daily quota exhaustion monitoring |
| [`adapters/email.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/adapters/email.py) | Agency Newsletters | RFC 5322 MIME parser & IMAP/Cloudflare workers | Zero external rate limit (inbound) |
| [`archivebox_pilot.py`](file:///Volumes/PortableSSD/GitHub/archive-govt-nz/src/archive_govt_nz/archivebox_pilot.py) | Agency Websites | Headless Chrome DOM rendering & PDF snapshot | Concurrency cap (max 2 parallel tasks) |
