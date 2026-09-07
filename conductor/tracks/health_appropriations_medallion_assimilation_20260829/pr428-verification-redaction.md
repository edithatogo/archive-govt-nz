# PR428 verification redaction — 2026-09-07

Review thread PRRT_kwDOTo2MOM6fzNfz, comment 3946931241. Isolated base G
58fee9d6332072efc15adea6e6221fd9d891b2a8, not the chart-packaging H worker.
Conductor implement/review used with dedicated evidence and focused tests only.

The public verify_eight now matches legacy.verify_rebuild's Exception boundary:
ordinary failures become ValueError with only a stable prefix and exception
class, raised from None. The existing verification body is unchanged in a
private helper. KeyboardInterrupt/SystemExit propagate unchanged. No CLI,
shared reader, source, rights, output creation or orchestration semantics change.

TDD: 13 red tests, two cancellation cases already passing. Non-object JSON PLAN
arrays/null/string/number/boolean previously escaped as TypeError; injected read
errors and missing state also lacked the public normalization boundary.
Actual CLI subprocess tests require exit 2, exact structured JSON and empty
stderr with no private payload. Missing CLI state remains absent after failure.
Direct tests verify file bytes unchanged and process-control exception identity.

Focused command: PYTHONPATH=src /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python
-m pytest tests/domains/health_appropriations/test_eight_verification_redaction.py
tests/domains/health_appropriations/test_rebuild_eight.py -q.
Final result: 37 passed. Ruff check/format and basedpyright on both changed
Python files pass. Self-review confirms only rebuild_eight.py changed in
production, with no broad module repair. No full harness or parent edits.

Exact existing positive replay verified read-only:
/tmp/health-crown-receipt-replay.iNn9fa/{first,second}.
Both MANIFEST.json SHA256:
f0b0b08790f52caed502efac23de5967718446fec30f007e7d30a67d4f805d97.
All 34 file hashes per run matched before/after verification. Counts unchanged:
budget215, BEFU10, HYEFU10, historical106, revenue69, BEFUdetail80,
HYEFUdetail80, Crown61. Verification used retained Bronze CAS, no fresh builds
or source capture. Parent will integrate G then H and run full gates separately.
