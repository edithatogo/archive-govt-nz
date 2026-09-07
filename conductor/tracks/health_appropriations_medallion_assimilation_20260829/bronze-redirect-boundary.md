# Phase 2.1 — local implementation review boundary

Follow-up to `ead9ca343d4d7ef819c1800afd7bdf5fd6f1308a`. The user requested
closure of the defensive capture fallback coverage gap, then a stop for parent
full assurance and independent review. No full harness, parent edits, census,
rights, global registry, Phase 2.4 or Phase 3 work occurred.

## Real contract, not artificial reachability

The finite `max_redirects + 1` request loop previously raised on its final
redirect response inside the loop. Its terminal fallback could not execute
with a valid configuration. Tests now characterize exact-boundary success,
one-hop-over-budget failure, and missing-Location immediate rejection with
ordinary HTTPX responses and valid budgets 0, 1 and 3. They assert exact request
URLs/counts, attempt outcomes/statuses, retained payload on success, closed
responses, and no promoted CAS/WARC/spool on budget rejection.

All eight tests passed before the refactor: this is explicit characterization,
not an invented red production defect. On budget exhaustion the runner now
records the same terminal receipt, closes the last response and naturally
exhausts its finite loop before raising the existing terminal error. A missing
Location still raises immediately, without consuming unused request budget.
No additional request is issued and no configuration/range mocking, coverage
exclusion or relaxed assertion is involved.

## Focused assurance and self-review

- 169 affected tests pass; capture.py has 161/161 lines and 48/48 branches
  covered (100%). The previous single uncovered fallback is now exercised by
  valid over-budget HTTP chains. The new test file contains eight cases.
- Three independent in-memory mutants are caught: one extra permitted request
  (3 failures), treating missing Location as nonterminal (1), and changing the
  terminal fallback outcome (3). No setup failures were counted as kills.
- Ruff check/format and basedpyright pass after standard formatting and explicit
  raw regex corrections. No threshold, warning suppression or exclusion added.
- The affected run again observed the existing unclosed-SQLite ResourceWarning;
  all tests passed and no suppression was introduced.

```sh
PYTHONPATH=src COVERAGE_FILE=build/health-redirect.coverage /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m pytest tests/domains/health_appropriations/test_capture_redirect_budget.py tests/domains/health_appropriations/test_capture_wire_length.py tests/domains/health_appropriations/test_capture_process_recovery.py tests/domains/health_appropriations/test_capture_checkpoint.py tests/domains/health_appropriations/test_bronze_ingestion_contracts.py tests/capture/test_capture.py tests/object_store/test_object_store.py tests/recovery/test_capture_recovery_integration.py tests/recovery/test_recovery.py tests/bronze/test_multihash.py tests/warc/test_warc.py tests/capture/test_capture_reconciliation.py tests/policy/test_resource_policy.py tests/capture/test_batch_eligibility.py tests/capture/test_run_capture_batch.py tests/policy/test_source_policy.py tests/domains/health_appropriations/test_inventory.py tests/domains/health_appropriations/test_donor.py --cov=archive_govt_nz.capture --cov-branch --cov-report=term-missing --cov-report=json:build/health-redirect-coverage.json -q
```

Review found no remaining actionable defect within the requested Phase 2.1
implementation/test slice. All named behaviors have mapped shared/Health
contracts in the preceding Bronze audits, including real process-death resume
and observable encoded-body length. Previously recorded power-loss, legacy-lock,
raw-wire and source-qualification boundaries remain distinct; none is promoted
by a coverage result. Phase 2.1 stays `[~]` solely pending the parent-owned
coherent full assurance and independent review checkpoint (M-18/AC-16).
Implementation stops here as explicitly requested.
