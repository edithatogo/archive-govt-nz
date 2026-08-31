# Spec - SOTA Test Infrastructure

## Status
done

## Goal
Add hypothesis property-based tests, integration and smoke test directories, coverage baselines, and pytest markers to the project test suite.

## Acceptance Criteria
- Hypothesis property-based tests exist for pure functions (_parse_int_header, _retry_after_seconds, slug_for_path, URL/content-type mappings)
- Integration test directory (tests/integration/) with cross-component pipeline tests
- Smoke test directory (tests/smoke/) with full CLI pipeline tests via CliRunner
- Coverage configuration in pyproject.toml with fail_under = 60
- Pytest markers (unit, integration, smoke, hypothesis) registered and applied to all tests
- 120+ tests passing, ruff clean, ty clean

## Evidence to Record
- Total test count
- Coverage percentage
- Hypothesis test examples/shrinking findings
- Integration test scenarios
- Smoke test scenarios

## Evidence Recorded
- 89 existing unit tests + 31 new tests = 120 total
- 8 hypothesis property-based tests added
- 3 integration tests in tests/integration/
- 2 smoke tests in tests/smoke/
- Coverage configured with fail_under = 60
- pytest markers registered and applied across all test files
