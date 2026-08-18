# Run Log: Adapter and Client Integration

- Upgraded `NZLegislationApiClient` in place with async transport, pacing, retry policies, and rate-limit tracking.
- Upgraded `NZLegislationAdapter` to use `NZLegislationApiClient` for all document fetching.
- Added comprehensive unit tests in `tests/domains/test_legislation_api.py` and updated `tests/capture/test_legislation_and_gazette_adapter.py`.
- Verified zero direct `httpx` bypass calls remain in the adapter.
