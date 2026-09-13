# Missing-originals audit integration — 2026-09-13

Relates to #234, #235 and #238.

The FOI safe-gaps worktree contained a completed recovery audit that had not
reached `main`. Its preceding implementation is already integrated. This change
retains the missing audit and records its relationship to later evidence.

## Preserved historical evidence

The [original report](missing-originals-recovery-audit-20260906.md) and
[original receipt](missing-originals-recovery-audit-20260906.json) are copied
byte-for-byte from commit `5f7b137e12a514f2cef7f99990f3d3483734c49e`.
Their observations are dated `2026-09-05T14:52:05Z` (September 6 locally).
References to fresh artifact access, the public Hub head, and pending approval
in those files describe that observation time, not the current state.

The original bounded search found no retained request 18631 originals. This
integration does not repeat that search or assert that all possible backups have
been exhausted. The request 18632 candidate cannot repair request 18631's gap.

The source worktree's historical ledger entry is not inserted into the middle of
the current hash chain. A new entry appends the source commit and artifact hashes,
preserving every existing ledger byte and all subsequent evidence.

## Later evidence and current local verification

The [September 10 decision](nz-publication-decision-20260910.json) explicitly
includes candidate `3514658895d5e26726f4d23a776a709a4c0fce165dcfb8e307ef10f4d15bb49e`
and supersedes the pending decisions cited by the historical audit. Its stated
publication conditions still apply.

The [September 12 public receipt](../../../evidence/publication/nz-fyi-raw-package-20260912.json)
records a different package: source run `34594859899`, manifest
`eacbd6b9d9e4c73bfab641de73f9083d2aceaf743127b07ea7ca50ca5cfb017b`.
It is not readback evidence for the older reconstructed candidate or restoration
of the missing batch. No remote readback was repeated for this integration.

A fresh local cold restore of the pinned `351465…bb49e` candidate passed using
the current package verifier, with one request, two responses, two events and
eight original files. The source package was preserved and restoration wrote to
a separate private archive directory. No raw payloads are included in this PR.

`uv run --locked pytest tests/test_foi_package.py -q --no-cov` passed all 105 tests.
The [integration receipt](missing-originals-recovery-integration-20260913.json)
records exact hashes and validation scope. Full repository validation and hosted
Actions outcomes are recorded in the PR. This completes integration of the
worktree's outstanding audit; broader FOI recovery, publication and phase
acceptance are not closed by this evidence change.
