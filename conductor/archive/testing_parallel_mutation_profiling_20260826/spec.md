# Specification: Testing Modernization (Pytest-Gremlins, Parallelisation, Property Testing & Scalene)

## 1. Architectural Objectives

1. **`pytest-gremlins` Mutation Testing Engine**:
   - Install and lock `pytest-gremlins>=1.9.0,<2` in dev dependencies.
   - Configure gremlins mutation flags, coverage-guided mutation filtering, and pardon annotations where appropriate.
   - Build a unified mutation runner `tools/run_gremlins.py` that executes mutation testing and emits structured JSON reports (`build/gremlins-report.json`).

2. **Full Parallel Test Execution (`pytest-xdist`)**:
   - Configure pytest execution to support parallel execution (`-n auto` or `-n logical`, `--dist=loadscope`).
   - Validate process isolation across temporary directories, memory DuckDB views, and subprocess stdio MCP servers.
   - Accelerate the 1,100+ test validation suite from ~4 minutes to sub-60 seconds.

3. **Property-Based Testing Expansion (Hypothesis)**:
   - Establish dedicated `tests/properties/` suite with explicit Hypothesis `@given` strategies:
     - `test_urn_properties.py`: URN parse/format/validate roundtripping over arbitrary text, whitespace, and Unicode.
     - `test_multihash_properties.py`: BLAKE3 and SHA-256 fixity hashes, byte lengths, and CIDv1 multihashes.
     - `test_schema_properties.py`: Medallion schema conversions and PyArrow Table validity.
     - `test_matcher_properties.py`: Aho-Corasick invariant matching over arbitrary corpus text.

4. **Scalene Deep Profiling Harness**:
   - Implement `tools/profile_scalene.py` utilizing `scalene` to profile memory allocation (Python vs C/Rust native), CPU usage (Python vs native), and copy overhead.
   - Benchmark the critical streaming path: Bronze ingestion -> Silver Parquet streaming -> Gold DuckDB queries.
   - Generate reproducible JSON and text receipts in `build/profiling-scalene.json`.

5. **Assurance Gate Synchronization**:
   - Add `gremlins` and `scalene-profile` stages into `src/archive_govt_nz/assurance.py` and verify with `./scripts/validate.sh`.
