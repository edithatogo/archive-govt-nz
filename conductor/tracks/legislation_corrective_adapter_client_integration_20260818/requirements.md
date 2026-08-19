# Requirements: Adapter and Client Transport Integration

Track: `legislation_corrective_adapter_client_integration_20260818`  
Parent: `legislation_corpus_consolidation_corrective_20260818`

## MoSCoW Requirements

### Must
1. **Unified Source Acquisition**:
   - Route all legislation transport from `NZLegislationAdapter` through `NZLegislationApiClient`.
2. **Deterministic Pacing & Rate Limit Resilience**:
   - Enforce 200ms minimum inter-request pacing.
   - Handle HTTP 429 and 403 responses with exponential backoff and `Retry-After` header adherence.
3. **Conditional Header Transport**:
   - Transmit `If-None-Match` (ETag) and `If-Modified-Since` conditional headers on repeated requests.
4. **Dual-Hash CAS Persistence**:
   - Store ingested byte streams into `ContentAddressedStore` with cryptographic SHA-256 and BLAKE3 digests.
