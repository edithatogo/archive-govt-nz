# Risk Management Ledger

| Risk ID | Description | Severity | Mitigation |
|---|---|---|---|
| RSK-01 | Rate limit throttling by NZ Legislation API | Medium | Exponential backoff, Retry-After header parsing, and request pacing. |
| RSK-02 | Third-party incorporated material copyright infringement | High | Granular classification in CAS; omit restricted items from public bundles. |
| RSK-03 | Premature donor archival before target stability | High | Strict shadow cutover gate requiring 2 observed target harvest cycles. |
