# Layout fixture and operation-profile checkpoint — 2026-09-13

This checkpoint closes the Phase 5.1 versioned-layout-fixture task. The
`health-layout-fixtures/v1` manifest has one unique, versioned layout ID for
each approved source family. It records every enabled read-only local operation
profile only for families with an `available` fixture.

Budget, Vote Health and population remain `required` with no operation profile.
Their absence is intentional: a standalone extractor or discovery record does
not enable family-wide normalization. No source was acquired, altered or
published.

Focused validation ran:

```text
uv run --locked pytest tests/tools/test_health_layout_fixture_manifest.py tests/domains/health_appropriations/test_source_operations.py
285 passed
```

The repository validation harness is required before the pull request. This
checkpoint does not complete source-family normalization, contextual-series
semantics, publication, recovery or the Health Appropriations track.
