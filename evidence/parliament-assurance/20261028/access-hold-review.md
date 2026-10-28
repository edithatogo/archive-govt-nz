# Review Report: Parliament exact report access holds

## Summary
The corrected source candidate passes local assurance; native approval and resumed archival remain pending.

## Verification Checks
- [x] **Plan Compliance**: Partial - implements exact unavailable-report isolation; native acceptance stays open.
- [x] **Style Compliance**: Pass - Ruff, strict types and Actionlint.
- [x] **New Tests**: Yes - exact native identity, stale metadata, manual authority, status classes, typed cold restore, no source re-probe, CLI and continued eligible publication.
- [x] **Test Coverage**: Yes - measured new hold modules88% combined statement/branch coverage; required hosted patch gate still applies.
- [x] **Test Results**: Passed -8660 tests,14 capability skips; full local harness stages passed.

## Findings and applied fixes
A hold could previously have been read by unawarev1 code after metadata refresh. Typedv2 is now required for hold/HTTP-diagnostic events; old readers reject before claiming a writer. Proof objects enter the exact referenced set only after candidate source evidence validation, preserving the unqualified-object boundary.

Review also identified a control-generation race between qualification and owner claim. The claim now requires the reviewed generation before any mutation; a regression verifies an intervening writer cannot be silently inherited. Native approval preserves pause, requires publication-clear state and cannot grant a licence or original publication.

The original legacy failure retains an unknown numeric HTTP code. No source restriction was re-probed or bypassed. New safe HTTP evidence contains only status and record/URL hashes. Known non-access errors remain unqualified. The original failed row remains failed, missing-original coverage explicit, and the actual driver test captures/publishes a separate eligible original without requesting the held attachment.

No unresolved source finding blocks required hosted CI. Native hold, fresh pinned proof/cold verification and bounded pilot remain mandatory before operational resumption. Parent archival and natural recurrence acceptance remain open.
