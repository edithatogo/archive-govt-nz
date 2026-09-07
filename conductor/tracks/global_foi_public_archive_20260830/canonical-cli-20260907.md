# Canonical local generator opt-in — P2.17

The existing local generator now accepts `--canonical-track PATH`. Omitting it
preserves the v1 seed catalogue and its exact file bytes. The explicit option
uses `build_source_index` and reproduces the committed canonical255 v2 files.
No publisher, scheduled job, activation or default catalogue source changes.

```sh
PYTHONPATH=src python tools/build_foi_catalogue.py \
  --canonical-track conductor/tracks/global_foi_public_archive_20260830 \
  --output build/foi-canonical-candidate
```

The command is local-only; source input validation precedes output creation.
All destination paths are preflighted before any file write. Conflicting bytes,
non-file targets and symlinks in the destination path fail with exit 2. Identical
files are not rewritten; missing files use exclusive creation, preventing an
existing file from being truncated. This is not a multi-file transaction or a
general defence against a hostile process swapping directory ancestors.

## Focused evidence

- Initial TDD: canonical invocation failed as an unrecognized argument;
  the unchanged-byte rerun test exposed the prior unnecessary identical rewrites.
- Final: 86 tests pass, including seven canonical guard mutants; 100% CLI line
  and branch coverage. Actual v1/v2 byte parity, repeat-run mtimes, bad input pins,
  file/directory/symlink conflicts, explicit seeds and script entrypoint covered.
- Socket connections are denied in CLI tests; local outputs are temporary.
- Ruff format/check and BasedPyright pass on the two changed Python files.
- Conductor implement/review guided compatibility, provenance and output safety.
  No full harness, remote writes, captures or shared lifecycle changes.

Exact focused command (using the repository's existing Python environment):

```sh
PYTHONPATH=src /Volumes/PortableSSD/GitHub/archive-govt-nz/.venv/bin/python -m pytest \
  tests/test_build_foi_catalogue.py tests/test_foi_canonical.py \
  tests/test_foi_canonical_mutants.py tests/test_foi_catalogue.py -q \
  --cov=tools.build_foi_catalogue --cov-branch --cov-report=term-missing \
  --cov-fail-under=100
```

## Read-only next-scope audit

P1.5 remains an evidence gap, not an identified new implementation defect.
The retained hosted-prerequisite readback verifies progress beyond 17225 and
unchanged-sync consistency, but explicitly lacks changed-sync hosted proof and
complete historical no-skipped-work evidence. Read-only recovery/validation of
existing run receipts is independent of an owner rights decision. New capture or
publication cannot be used to manufacture historical proof.

P4's publisher/restore and exact-decision guards already exist. The scheduled
metadata publisher intentionally remains v1. An eventual explicit canonical
publisher handoff can be developed with a mock Hub without raw-rights approval,
but is not activated or implemented here. The NZ reconstructed raw candidate
still has pending exact-manifest rights/privacy approval; that is a genuine owner
gate, not a missing generic human factual-review queue.

These findings use retained repository evidence, not fresh hosted readback.
Parent owns current contract review, full gate and lifecycle acceptance.
