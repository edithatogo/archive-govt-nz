# Track 5 Requirements (MoSCoW)

## Must Have
- **MUST-1**: Implement `AsyncBaseCaptureAdapter` protocol in `src/archive_govt_nz/capture/base.py`.
- **MUST-2**: Migrate Feeds (RSS/Atom/JSON), Bluesky, Threads, X/Twitter, YouTube, and Email into structured adapter packages.
- **MUST-3**: Stream all captured byte payloads directly into SHA-256 CAS (`ContentAddressedStore`) and emit immutable `CaptureEvent` receipts.
- **MUST-4**: Maintain rate limits, exponential backoff, jitter, and ethical robots/ToS compliance across all adapters.
- **MUST-5**: Achieve >95% branch coverage with unit and mock-transport tests for every adapter.

## Should Have
- **SHOULD-1**: Support offline deterministic fixture replay for all adapters.

## Won't Have
- **WONT-1**: Do not bundle all adapters into a single bulk cutover; each adapter family is promoted individually.
