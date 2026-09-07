# P4 canonical publisher handoff — 2026-09-07

Repository-owned handoff implemented locally from health-interfaces HEAD
`6c567c2c6de7324f324a2464a8a03f5e13057881` on isolated branch
`codex/foi-canonical-publisher-20260907`. No hosted publication was attempted.

`publish_catalogue(hub, seeds)` retains the existing v1 projection and receipt
shape. The keyword-only `canonical_track=Path(...)` explicitly selects the
existing `build_source_index` v2 builder. Its source pins and retained-receipt
checks run before any Hub access; invalid inputs never fall back to v1.
The resulting exact bytes use the existing immutable snapshot, anonymous
readback, restore comparison and compare-and-swap pointer contract. No alternate
transport, schema interpretation or rights-approval mechanism was introduced.

The API is a publisher: a real Hub would write remotely. This delivery exercised
only MemoryHub. The existing workflow and its two-argument caller are unchanged;
this opt-in does not request activation or authorize anyone to publish.

## Focused evidence

- TDD red: six new canonical cases failed because the keyword did not exist;
  the default v1 parity case passed. After implementation, two test assumptions
  were corrected: canonical rows are sorted rather than seed-first, and malformed
  pin fixtures must retain the pin envelope to test the intended set guard.
- Actual v1/v2 snapshot bytes equal their respective builders. The v2 registry
  passes its schema; all 255 identities and exact canonical input pin mappings
  are retained, including all original 30 source rows unchanged.
- Exact coverage and complete byte parity preserve null denominators, dated
  observation provenance, restricted/unknown dispositions, rights, schedules and
  raw counts. They do not certify historical transport or exhaustive discovery.
- Invalid pins fail before transport. Child access restrictions, file/byte caps
  and corrupted readback prevent pointer/card promotion. A failed v2 upgrade
  leaves an existing verified v1 pointer and card byte-identical; immutable
  candidate bytes may remain staged, as in the existing transport contract.
- Both modes are idempotent. Existing raw-package tests continue requiring the
  exact independently trusted manifest, source, destination, reviewer, rights,
  privacy and evidence decision. Metadata handoff grants none of these.

Reproduction (from the isolated worktree, using the repository environment):

```sh
PYTHONPATH=src /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m pytest tests/test_foi_delivery.py tests/test_foi_package.py tests/test_foi_canonical.py tests/test_foi_canonical_mutants.py tests/test_publish_foi_cli.py -q --cov=archive_govt_nz.foi_publication --cov-report=term-missing
```

## Focused review and remaining gates

Final result: **194 passed**, including seven killed canonical guard mutants;
publisher statement/branch coverage 100%. Scoped Ruff format/lint and BasedPyright
passed. See [machine receipt](canonical-publisher-20260907.json).

Conductor implement/review guided TDD and the authority-boundary audit. Review
checked opt-in/default behavior, failure ordering, exact restored bytes, immutable
retry, source identity preservation and unchanged raw approval code. The shared
transport retains its existing 10,000-file / 6-GiB snapshot limits; this is not a
new arbitrary-input importer or a claim of a new construction-memory bound.
The machine receipt records actual deterministic output size and digest pins.

This closes only the local canonical metadata handoff gap. It does not close
AC07/AC11 or P4 as a whole: hosted anonymous receipts, child raw manifests and
revision reconciliation, approved raw delivery, and second-instance restoration
remain distinct acceptance work. P1.5 historical proof gaps are also unchanged.
No raw approval, publication, live capture, schedule change, global registry
mutation or full harness occurred. Parent owns integration, full checks and
lifecycle acceptance. No additional external input is needed for this local slice.
