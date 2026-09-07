# Capture-written WARC P2 fixes — local focused evidence

Base: `78c17e2d55356097c02ec50b4c6c4511a1462073`.
Branch: `codex/health-warc-strict-framing-20260907`.
Observation date: 2026-09-07. Synthetic fixtures only; no live capture or remote
mutation. Parent gates and previous attempts were not modified or polled.

## Contract and scope

- Require zero HTTP Content-Type fields when the receipt has none, otherwise
  exactly one matching field. Names are case-insensitive. Both identical and
  conflicting duplicates fail closed; there is no first/last-value policy.
- Require exactly one outer Content-Length and the exact final `CRLF CRLF`
  at its declared block boundary, with no trailing bytes. Do not infer framing
  merely from a payload suffix: decoded bodies can themselves end in CRLF.
- Keep the generic historical WARC verifier unchanged. This stricter check is
  for capture-written resumable records, not arbitrary WARC conformance.
- Preserve request/final URL digests, status, decoded-body/CAS binding and
  legacy missing-binding rejection. HTTP wire Content-Length is deliberately
  not used to measure decoded payloads.
- Tests re-pin malformed WARC hashes and assert verifier leaves those bytes
  unchanged. The positive HTTPX MockTransport test emits a new 302-to-200 gzip
  capture through capture_url and verifies its decoded receipt/WARC. This is
  synthetic consistency evidence, not historical authenticity or live access.

## Tests first and retained attempts

Before production edits, the initial 27-case strict test suite produced
**18 failed, 9 passed in 0.82 seconds** (pytest exit 1). All six duplicate
Content-Type cases failed with `DID NOT RAISE ValueError`. Missing, CRLF-only,
LF-only and extra-CRLF terminators each failed for all three bodies (12 cases).
The partial lone-CR and CRLF-CR terminators already failed closed; the three
valid terminators passed. Five outer-length cases and one emitted encoded
redirect positive were subsequently added.

Initial static checks reported formatting and a missing async iterator return
annotation, followed by a mutation-runner docstring style finding. These were
corrected without suppressions or weakened assertions. First expanded green:
117 passed in 5.21 seconds; final green: 117 passed in 2.98 seconds.

## Reproduction

Use the existing locked environment's Python and companion ruff/basedpyright;
this run used the sibling health-foi integration `.venv` (Python 3.14.6).
Run from this checkout, with `PYTHONPATH=src`. No dependencies were changed.

```sh
python -m coverage run -m pytest -q \
  tests/warc/test_warc_binding_strict.py \
  tests/warc/test_warc_binding.py tests/warc/test_warc.py \
  tests/domains/health_appropriations/test_capture_checkpoint.py \
  tests/domains/health_appropriations/test_capture_process_recovery.py \
  tests/domains/health_appropriations/test_bronze_ingestion_contracts.py \
  tests/domains/health_appropriations/test_capture_wire_length.py
python -m coverage report --include='*/warc_binding.py'
ruff check src/archive_govt_nz/warc_binding.py \
  tests/warc/test_warc_binding_strict.py \
  evidence/assurance/health-warc-strict-framing-20260907/mutations.py
ruff format --check src/archive_govt_nz/warc_binding.py \
  tests/warc/test_warc_binding_strict.py \
  evidence/assurance/health-warc-strict-framing-20260907/mutations.py
basedpyright --pythonpath "$VIRTUAL_ENV/bin/python" \
  src/archive_govt_nz/warc_binding.py tests/warc/test_warc_binding_strict.py \
  evidence/assurance/health-warc-strict-framing-20260907/mutations.py
python evidence/assurance/health-warc-strict-framing-20260907/mutations.py
git diff --check
```

Repo pytest defaults retained (including strict/importlib mode and randomized
order). Coverage: 44 statements, 18 branches, zero missed/partial, 100%.
Ruff check/format and basedpyright: clean (0 errors, warnings, notes).
Mutation runner copies only source to temporary directories, uses original
tests against that source, requires a passing baseline and assertion failures
rather than collection errors. All 7 targeted mutants killed; no survivors.
This bounded mutation set is not the full repository mutation gate.

No full harness, publication, hosted CI, lifecycle closure or peer approval is
claimed. Banach's independent review and parent integration/gates remain external
to this receipt. Source/test/probe fixity and bounded results are in results.json.
