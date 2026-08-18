# Requirements: Adapter and Client Integration

## Non-Negotiable Reuse Contract
- Exactly one archive-facing adapter: `NZLegislationAdapter` in `src/archive_govt_nz/adapters/nz_legislation.py`.
- Exactly one source API client: `NZLegislationApiClient` in `src/archive_govt_nz/domains/legislation/api.py`.
- No parallel `V2`, `New`, `Enhanced`, or `Legacy` adapters or clients.
- Adapter must use client for all transport without direct independent HTTP requests.

## Ported Donor Behaviours
- `X-Api-Key` authentication and conditional ETag/Last-Modified headers.
- Rate-limit remaining/reset tracking and low-watermark logging.
- `Retry-After` compliance and 429 exponential backoff.
- 403 burst-limit backoff mitigation.
- Configurable base URL, timeout, and pacing interval.
- Asynchronous transport method `get_document_raw_async`.
