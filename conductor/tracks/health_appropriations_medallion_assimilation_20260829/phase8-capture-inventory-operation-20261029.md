# Capture inventory reconciliation operation

The read-only CLI and MCP operation accepts named census inputs and capture
receipts with explicit SHA-256 pins and, where required by a capture receipt,
its original pinned request. It uses the existing observation-preserving
inventory builder and returns counts and input pins without resource URLs or
local paths. Input count, individual bytes, total bytes, total rows and request
matching comparisons are bounded. No
capture, source-object replay, rights evaluation, normalization or publication
is performed.

Two repeated MCP calls on the retained `source-census.json` (SHA-256
`aa6f9d55ed8f416c8ea890add9ecc5363cbe4c0333f7efaa02db9fd6d44df272`)
and `official-capture-2026-10-03-health-complete.json` (SHA-256
`017b3a9adbda288c60693ef038e4c0da198d8db99b2bca9cf4bb81adbc6efb5f`)
returned identical receipts: 143 resources, 143 census observations, 75
recorded captured resources and 75 capture observations. The legacy receipt
does not have a capture-time request binding; this operation does not create one.

The focused synthetic contracts exercise CLI/MCP equality, repeatability,
redaction, no writes, changed-pin rejection and missing request rejection.
The first run exposed a missing MCP output schema; its correction was rerun
successfully. The combined focused selection passed 54 tests and found one
missing JSON Schema dialect declaration; the affected protocol test passed
after correction. Ruff and the scoped type check passed. Full repository
validation and protected PR delivery remain pending.

The first full harness reached its test stage after passing lock, Conductor,
format, lint and typing. The test stage ended with 8,696 passed, 14 skipped,
30 failed and 19 errors in 901.63 seconds. An `IO_ENOSPC` workbook-writing
error was observed during the run; individual failures require rerun and
classification. The run does not establish a full pass. Subsequent temporary
test output is directed to an isolated directory on PortableSSD with free space.
The 49 failed or errored nodes all passed on the failure-only retry. The
remaining 26 harness stages passed separately, including schema validation
(95 schemas / 85 documents), parity (9/9), mutation gates, audit, licence,
secret scan and SBOM validation. This does not turn the failed full run
into a single full-pass receipt or supply its missing complete coverage proof.

After those gates, row and request-matching work limits were added. The affected
inventory and MCP selection passed 44 tests, and scoped Ruff and typing checks
passed on Python 3.15.1. Fresh hosted full assurance is required for the final
PR tree before merge.

PR #811's three hosted assurance jobs passed, but its patch coverage status
failed. Added focused contracts for malformed inputs, cumulative size limits,
invalid capture pins and redacted CLI failures. Nine operation tests pass;
scoped branch coverage reports 97.83%, without changing the 80% repository
floor. The new PR head requires fresh hosted checks.
