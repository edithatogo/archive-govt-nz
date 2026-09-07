# PR421 retained response binding correction

Base: `7b672a9c7448ec4ffb5f925553b70761db2f3993`.
Review finding: `PRRT_kwDOTo2MOM6fyBeB` (P1).
Scope: M-04, M-15, M-18; AC-04, AC-13, AC-16. This is a focused
resume-integrity correction, not phase or programme closeout.

Previously, mutable checkpoint fields could assign a different same-host
CAS/WARC pair to a source while both artifact digests remained valid.
Six regression cases failed before implementation: swapped receipts,
same-path/different-query receipts, changed final URL, status, CAS body,
and legacy WARC without request binding.

## Binding and limits

The capture writer now embeds `WARC-Request-URL-SHA256` and
`WARC-Final-URL-SHA256`. Capture passes the original input URL separately
from the final response URL. Hash input is the exact URL string, including
query and fragment; this identifies the supplied locator, not a claim that
fragments were sent over HTTP. WARC-Target-URI remains sanitized. No query
plaintext is added to WARC.

Resume checks a capped snapshot (65 MiB: the existing 64 MiB capture-body
limit plus envelope allowance), its artifact hash, existing WARC framing
parser, and the retained warcio response parser. Exactly one response must
match the request digest, final URL digest, sanitized final URL, HTTP status,
content type, payload digest, decoded body byte count and SHA-256 of the
verified CAS object. Binding headers must occur exactly once. Decoded body
verification uses the raw record stream, not another decompression pass.
HTTP Content-Length is not used as decoded-body length; WARC framing is.

Legacy records missing either URL digest fail closed and remain unchanged.
Do not synthesize capture-time evidence from mutable checkpoint fields.
Migration requires a fresh capture/new manifest path with the updated writer;
retain the old manifest and WARC as historical evidence. No automatic recapture
or migration occurs during failed resume.

This proves internal source/response/CAS consistency, not independently
retained redirect history or authenticity against coordinated artifact
rewriting. No rights or publication assurance is added.

## Validation and review

All commands ran in the isolated `codex/pr421-resume-binding-20260907` tree,
using the repository's existing Python environment and `PYTHONPATH=src`.

```sh
python -m pytest tests/domains/health_appropriations/test_capture_checkpoint.py -k requires_warc -q
# RED: six expected DID NOT RAISE failures before implementation.
python -m pytest tests/warc tests/domains/health_appropriations/test_capture_checkpoint.py tests/domains/health_appropriations/test_capture_process_recovery.py tests/domains/health_appropriations/test_bronze_ingestion_contracts.py tests/capture/test_capture.py -q --cov=archive_govt_nz.warc_binding --cov-branch --cov-report=term-missing
# GREEN: 90 passed; new verifier 36/36 statements and 14/14 branches.
python -m pytest tests/warc tests/domains/health_appropriations/test_capture_checkpoint.py -q --gremlins --gremlin-targets=src/archive_govt_nz/warc_binding.py --gremlin-clear-cache --gremlin-workers=4
# 48 tests at mutation checkpoint; 20/20 killed, zero survivors/cache hits.
# Final test-only additions distinguish path swaps and wire-length semantics.
```

Ruff check, Ruff format --check, basedpyright and git diff --check passed
for the eight changed source/test/tool paths. The mutation runner emitted
its previously-imported-module coverage warning; coverage above comes from
the separate focused coverage run. No exclusions or mutant pardons added.

Self-review checked missing/duplicate bindings, altered bodies and envelopes,
empty/multiple/truncated records, exact byte cap, and real capture redirects.
Existing recovery fixtures now include their claimed content type in WARC,
rather than bypassing the stronger check. Conductor implement/review procedures
were used; shared lifecycle edits and full harness were excluded by explicit
parent instructions. Independent review and integrated full harness remain
parent-owned gates. Revenue work and parent checkout were not modified.
