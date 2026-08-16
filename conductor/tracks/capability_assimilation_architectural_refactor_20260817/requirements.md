# Track 11 Requirements (MoSCoW)

## Must Have
- **MUST-1**: Remove all ad-hoc donor logging (Loguru) and standardize on stdlib `logging` with structured JSON support.
- **MUST-2**: Unify all HTTP network interactions under `httpx.AsyncClient` with bounded timeouts, retries, and CAS streams.
- **MUST-3**: Achieve 100% type conformance with `basedpyright` strict typing across all migrated modules.
- **MUST-4**: Maintain >95% branch coverage with zero skipped tests or artificial exclusions.

## Should Have
- **SHOULD-1**: Add mutation test suites for new source adapter parsers.
- **SHOULD-2**: Benchmark CAS throughput to confirm >400 MB/s streaming performance.

## Won't Have
- **WONT-1**: Do not retain duplicate adapter wrappers or legacy helper files.
