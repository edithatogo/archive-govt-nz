# Local scheduled capture contract

This slice adds a scheduler-callable Python command for one bounded,
hash-pinned census. Its plan has exactly `schema_version`, `census`,
`census_sha256`, and `max_resource_bytes`; the schema version is
`archive-govt-nz.health-capture-schedule/v1`. The command requires the plan
SHA-256 and an explicit output root. Without `--execute` it verifies the plan
and census and emits a compact receipt without creating output or contacting a
source. `--execute` uses the existing exclusive capture runner with
preservation-only rights and resume enabled, including orphan recovery. The
census is reopened with the same pin immediately before use. Capture outcomes
are recorded by the existing manifest and WARC/object store; the compact
scheduler receipt does not assert redistribution, normalization, completeness
of excluded records, publication, or a running timer.

Focused offline checks exercise pin rejection, no-write preflight, execution
selection, original capture and repeat replay without a second fetch. The
existing checkpoint tests remain responsible for interruption, concurrency,
WARC binding and recovery contracts. This slice does not itself activate a
schedule, implement the main CLI or MCP integration, or close Phase 8.
