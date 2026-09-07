# Workflow integration review and validation

The first full gate at `d30a5d32` passed lock, Conductor, format, lint and types,
then exited 1: 6,271 tests passed but `test_foi_phase_validation.py` had one
collection error. Its new direct `tools` import was unavailable under the
repository pytest invocation. The correction reuses that test file's existing
explicit file-location `TOOL` loader rather than changing global import paths.
Coverage was 97.72%; no later gates ran in this failed attempt.

Independent eight-stage review reproduced both retained builds and all 34
files, but found three P2 gaps: a missing independently pinned Crown observation
receipt, inconsistent nested source-record identity being accepted, and
excluded formula areas accepting admitted record IDs. Those findings must be
fixed and re-reviewed before delivery; passing tests alone do not close them.

The catalogue-disposition validator, 108 chart literals and their distinct
semantics, and literal packaging have independent focused review evidence.
The original four-stage registry/resume/Gold paths remain unchanged. Neither
the historical PDF identity observation nor raw/context chart admission is
represented as canonical numerical extraction or whole-track completion.
